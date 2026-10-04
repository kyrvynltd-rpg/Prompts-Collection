import hashlib
import hmac
import json
import sys
import time

import pytest

import billing
import learning
from accounts import AccountService, check_password, is_student_email
from billing import DbEntitlements, LemonSqueezyProvider, PayPalProvider, StripeProvider, WebhookError
from db import Database
from workspace import MAX_PROMPTS, Workspace, WorkspaceError


@pytest.fixture
def db():
    return Database(":memory:")


def stripe_headers(secret, body, ts):
    return {"Stripe-Signature": f"t={ts},v1=" + hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()}


def test_stripe_payload_validation():
    p, now = StripeProvider(), int(time.time())
    for body in (b"not json", b"[1]"):
        with pytest.raises(WebhookError):
            p.parse_webhook(body, stripe_headers("s", body, now), "s", now)
    body = b'{"type":"x"}'  # signed but no event id
    with pytest.raises(WebhookError, match="event id"):
        p.parse_webhook(body, stripe_headers("s", body, now), "s", now)
    with pytest.raises(WebhookError, match="bad signature header"):
        p.parse_webhook(b"{}", {"Stripe-Signature": "v1=abc"}, "s", now)
    with pytest.raises(WebhookError, match="bad signature header"):
        p.parse_webhook(b"{}", {"Stripe-Signature": "t=abc,v1=abc"}, "s", now)


def test_stripe_refund_and_other_events():
    p, now = StripeProvider(), int(time.time())
    for kind, expected in (("charge.refunded", "payment.refunded"), ("customer.subscription.deleted", "subscription.cancelled")):
        body = json.dumps({"id": "e", "type": kind, "data": {"object": {"customer": "c"}}}).encode()
        assert p.parse_webhook(body, stripe_headers("s", body, now), "s", now)["type"] == expected
    body = json.dumps({"id": "e", "type": "invoice.paid", "data": {"object": {"customer": "c", "lines": {"data": []}}}}).encode()
    assert p.parse_webhook(body, stripe_headers("s", body, now), "s", now) is None
    body = json.dumps({"id": "e", "type": "checkout.session.completed", "data": {"object": {"payment_status": "unpaid"}}}).encode()
    assert p.parse_webhook(body, stripe_headers("s", body, now), "s", now) is None
    body = json.dumps({"id": "e", "type": "checkout.session.completed", "created": now,
                       "data": {"object": {"payment_status": "paid", "mode": "payment", "client_reference_id": "u"}}}).encode()
    assert p.parse_webhook(body, stripe_headers("s", body, now), "s", now)["period_end"] > now + 300 * 86400


def _ls(name, extra=None):
    attrs = {"customer_id": 1, "updated_at": "t", **(extra or {})}
    return json.dumps({"meta": {"event_name": name, "custom_data": {"user_id": "u", "plan": "pro"}}, "data": {"id": "9", "attributes": attrs}}).encode()


def test_lemonsqueezy_events():
    p = LemonSqueezyProvider()

    def sign(body):
        return {"X-Signature": hmac.new(b"k", body, hashlib.sha256).hexdigest()}

    with pytest.raises(WebhookError, match="missing"):
        p.parse_webhook(b"{}", {}, "k")
    with pytest.raises(WebhookError, match="missing"):
        p.parse_webhook(b"{}", {"X-Signature": "x"}, "")
    assert p.parse_webhook(_ls("subscription_expired"), sign(_ls("subscription_expired")), "k")["type"] == "subscription.cancelled"
    assert p.parse_webhook(_ls("order_refunded"), sign(_ls("order_refunded")), "k")["type"] == "payment.refunded"
    assert p.parse_webhook(_ls("subscription_created"), sign(_ls("subscription_created")), "k") is None  # no renew date
    assert p.parse_webhook(_ls("something_else"), sign(_ls("something_else")), "k") is None


def test_paypal_events():
    p = PayPalProvider(lambda b, h: True)

    def body(kind, ident="WH"):
        return json.dumps({"id": ident, "event_type": kind, "resource": {"id": "I", "custom_id": "u:pro"}}).encode()

    assert p.parse_webhook(body("BILLING.SUBSCRIPTION.CANCELLED"), {}, "")["type"] == "subscription.cancelled"
    assert p.parse_webhook(body("PAYMENT.SALE.REFUNDED"), {}, "")["type"] == "payment.refunded"
    assert p.parse_webhook(body("OTHER"), {}, "") is None
    with pytest.raises(WebhookError, match="event id"):
        p.parse_webhook(body("PAYMENT.SALE.COMPLETED", ""), {}, "")
    with pytest.raises(WebhookError):
        PayPalProvider(lambda b, h: False).parse_webhook(body("X"), {}, "")


def test_unknown_provider_checkout_and_ignored_webhook(db, monkeypatch):
    assert billing.checkout_url("nope", "u", "e@x.co") is None
    body = b'{"id":"e1","type":"unrelated"}'
    now = int(time.time())
    out = billing.process_provider_webhook(DbEntitlements(db), StripeProvider(), "s", body, stripe_headers("s", body, now), now)
    assert out == "ignored"
    store = DbEntitlements(db)
    store.grant("u", "plus", 5)
    assert store.get("u") is None  # expired grant is not active


def test_account_edge_cases(db):
    assert not is_student_email("not-an-email")
    assert not check_password("x", "bcrypt$a$b") and not check_password("x", "scrypt$!!$!!")
    svc = AccountService(db)
    assert svc.user_for_session("") is None and svc.user_for_session("nope") is None
    with pytest.raises(Exception, match="not right"):
        svc.login("ghost@x.co", "whatever-long-pass")


def test_db_without_postgres_driver(monkeypatch):
    monkeypatch.setitem(sys.modules, "psycopg", None)
    with pytest.raises(RuntimeError, match="requirements-postgres"):
        Database("postgresql://u:p@localhost/db")


def test_db_close_and_shared(monkeypatch):
    import db as dbmod
    monkeypatch.setattr(dbmod, "_shared", None)
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("APP_DB_PATH", ":memory:")
    shared = dbmod.get_db()
    assert dbmod.get_db() is shared
    shared.close()


def test_learning_max_words_and_workspace_full(db, monkeypatch):
    ex = {"checks": [{"type": "max_words", "label": "short", "n": 3}], "pass_mark": 100}
    assert learning.grade(ex, "one two").passed and not learning.grade(ex, "one two three four").passed
    import workspace
    monkeypatch.setattr(workspace, "MAX_PROMPTS", 2)
    ws = Workspace(db)
    ws.save("u", "a", "body body")
    ws.save("u", "b", "body body")
    with pytest.raises(WorkspaceError, match="full"):
        ws.save("u", "c", "body body")
    assert MAX_PROMPTS == 500
