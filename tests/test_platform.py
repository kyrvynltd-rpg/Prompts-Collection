import hashlib
import hmac
import json
import time

import pytest

import billing
import learning
import webhook_server
from accounts import AccountError, AccountService, ConsoleMailer, check_password, hash_password, is_student_email
from billing import DbEntitlements, LemonSqueezyProvider, PayPalProvider, StripeProvider, WebhookError
from db import MIGRATIONS, Database
from pricing import get_pricing


@pytest.fixture
def db():
    return Database(":memory:")


@pytest.fixture
def svc(db):
    return AccountService(db, ConsoleMailer())


# ---- database
def test_migrations_apply_once(db):
    assert db.migrate() == len(MIGRATIONS)
    assert db.one("SELECT COUNT(*) FROM schema_version")[0] == len(MIGRATIONS)


# ---- accounts
def test_password_hash_roundtrip():
    h = hash_password("correct horse battery")
    assert check_password("correct horse battery", h) and not check_password("nope", h)
    assert not check_password("x", "garbage")


def test_register_login_session_logout(svc):
    user = svc.register("Ada@Example.com", "a-long-password", "Ada")
    assert user.email == "ada@example.com"
    same, token = svc.login("ada@example.com", "a-long-password")
    assert same.id == user.id and svc.user_for_session(token).id == user.id
    svc.logout(token)
    assert svc.user_for_session(token) is None


def test_register_validation(svc):
    with pytest.raises(AccountError):
        svc.register("bad", "a-long-password")
    with pytest.raises(AccountError):
        svc.register("a@b.co", "short")
    svc.register("a@b.co", "a-long-password")
    with pytest.raises(AccountError):
        svc.register("A@B.co", "a-long-password")


def test_lockout_and_generic_error(svc):
    svc.register("a@b.co", "a-long-password")
    for _ in range(5):
        with pytest.raises(AccountError, match="not right"):
            svc.login("a@b.co", "wrong-password-x")
    with pytest.raises(AccountError, match="Too many"):
        svc.login("a@b.co", "a-long-password")
    svc.login("a@b.co", "a-long-password", now=time.time() + 3600)


def test_session_expiry(svc):
    svc.register("a@b.co", "a-long-password")
    _, token = svc.login("a@b.co", "a-long-password")
    assert svc.user_for_session(token, now=time.time() + 15 * 24 * 3600) is None


def test_student_domains():
    assert is_student_email("x@ox.ac.uk") and is_student_email("x@cs.ox.ac.uk")
    assert not is_student_email("x@ac.uk") and not is_student_email("x@gmail.com") and not is_student_email("x@evil.ac.uk.com")


def test_student_verification_flow(svc):
    user = svc.register("a@gmail.com", "a-long-password")
    with pytest.raises(AccountError):
        svc.start_student_verification(user.id, "a@gmail.com")
    svc.start_student_verification(user.id, "a@ox.ac.uk")
    code = svc.mailer.outbox[-1][2].split("code is: ")[1].split("\n")[0]
    with pytest.raises(AccountError):
        svc.confirm_student(user.id, "wrong")
    assert svc.confirm_student(user.id, code).student_verified
    with pytest.raises(AccountError):
        svc.confirm_student(user.id, code)  # single use


def test_student_code_not_usable_by_another_user(svc):
    a = svc.register("a@gmail.com", "a-long-password")
    b = svc.register("b@gmail.com", "a-long-password")
    svc.start_student_verification(a.id, "a@ox.ac.uk")
    code = svc.mailer.outbox[-1][2].split("code is: ")[1].split("\n")[0]
    with pytest.raises(AccountError):
        svc.confirm_student(b.id, code)


def test_export_and_delete(svc, db):
    user = svc.register("a@b.co", "a-long-password")
    learning.ProgressStore(db).record(user.id, "m1e1", 80, True)
    assert svc.export_data(user.id)["progress"][0]["exercise_id"] == "m1e1"
    svc.delete_account(user.id)
    assert svc.get_user(user.id) is None
    assert db.all("SELECT * FROM progress WHERE user_id=?", (user.id,)) == []
    svc.register("a@b.co", "a-long-password")  # email is free again


# ---- billing
def _stripe_headers(secret, body, ts):
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return {"Stripe-Signature": f"t={ts},v1={sig}"}


def test_stripe_checkout_then_renewal_and_cancel(db):
    store, now = DbEntitlements(db), int(time.time())
    done = json.dumps({"id": "evt_1", "type": "checkout.session.completed", "created": now,
                       "data": {"object": {"payment_status": "paid", "mode": "subscription", "client_reference_id": "u1",
                                           "customer": "cus_1", "metadata": {"plan": "student"}}}}).encode()
    p = StripeProvider()
    assert billing.process_provider_webhook(store, p, "s", done, _stripe_headers("s", done, now), now) == "applied"
    assert store.get("u1") is not None
    assert billing.process_provider_webhook(store, p, "s", done, _stripe_headers("s", done, now), now) == "duplicate"
    paid = json.dumps({"id": "evt_2", "type": "invoice.paid", "created": now,
                       "data": {"object": {"customer": "cus_1", "lines": {"data": [{"period": {"end": now + 90 * 86400}}]}}}}).encode()
    billing.process_provider_webhook(store, p, "s", paid, _stripe_headers("s", paid, now), now)
    assert store.get("u1")["expires_at"] > now + 90 * 86400
    gone = json.dumps({"id": "evt_3", "type": "customer.subscription.deleted", "created": now,
                       "data": {"object": {"customer": "cus_1"}}}).encode()
    billing.process_provider_webhook(store, p, "s", gone, _stripe_headers("s", gone, now), now)
    assert store.get("u1") is None


def test_stripe_rejects_bad_or_stale_signature():
    p, now = StripeProvider(), int(time.time())
    body = b'{"id":"e","type":"x"}'
    with pytest.raises(WebhookError):
        p.parse_webhook(body, {"Stripe-Signature": f"t={now},v1=deadbeef"}, "s", now)
    with pytest.raises(WebhookError):
        p.parse_webhook(body, _stripe_headers("s", body, now - 1000), "s", now)
    with pytest.raises(WebhookError):
        p.parse_webhook(body, {}, "s", now)
    with pytest.raises(WebhookError):
        p.parse_webhook(body, _stripe_headers("s", body, now), "", now)


def test_lemonsqueezy_flow(db):
    store, body = DbEntitlements(db), json.dumps({
        "meta": {"event_name": "subscription_created", "custom_data": {"user_id": "u2", "plan": "student"}},
        "data": {"id": "77", "attributes": {"renews_at": "2030-01-01T00:00:00Z", "customer_id": 5, "updated_at": "t"}}}).encode()
    sig = hmac.new(b"k", body, hashlib.sha256).hexdigest()
    assert billing.process_provider_webhook(store, LemonSqueezyProvider(), "k", body, {"X-Signature": sig}) == "applied"
    assert store.get("u2") is not None
    with pytest.raises(WebhookError):
        billing.process_provider_webhook(store, LemonSqueezyProvider(), "k", body, {"X-Signature": "bad"})


def test_paypal_needs_verifier_and_works_with_one(db):
    body = json.dumps({"id": "WH-1", "event_type": "BILLING.SUBSCRIPTION.ACTIVATED", "resource": {"id": "I-1", "custom_id": "u3"}}).encode()
    store = DbEntitlements(db)
    with pytest.raises(WebhookError):
        billing.process_provider_webhook(store, PayPalProvider(), "", body, {})
    assert billing.process_provider_webhook(store, PayPalProvider(lambda b, h: True), "", body, {}) == "applied"
    assert store.get("u3") is not None


def test_unknown_event_ignored_and_unmapped_customer(db):
    store = DbEntitlements(db)
    assert billing.apply_event(store, {"id": "x", "type": "payment.succeeded", "subject": None, "customer": "nobody",
                                       "plan": "student", "period_end": 9_999_999_999}) == "ignored"


def test_checkout_urls(monkeypatch):
    monkeypatch.delenv("STRIPE_PAYMENT_LINK", raising=False)
    assert billing.checkout_url("stripe", "u", "a@b.co") is None
    monkeypatch.setenv("STRIPE_PAYMENT_LINK", "https://buy.example/abc")
    assert "client_reference_id=u" in billing.checkout_url("stripe", "u", "a@b.co")
    monkeypatch.setenv("LEMONSQUEEZY_CHECKOUT_URL", "https://s.example/checkout/buy/1?x=1")
    assert "%5Buser_id%5D=u" in billing.checkout_url("lemonsqueezy", "u", "a@b.co")
    assert billing.configured_providers() == ["stripe", "lemonsqueezy"]


def test_webhook_server_handler(db, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "s")
    store = DbEntitlements(db)
    assert webhook_server.handle("/webhooks/nope", b"", {}, store)[0] == 404
    assert webhook_server.handle("/webhooks/stripe", b"{}", {}, store)[0] == 400
    body, now = b'{"id":"e1","type":"ignored.type"}', int(time.time())
    assert webhook_server.handle("/webhooks/stripe", body, _stripe_headers("s", body, now), store) == (200, "ignored")


# ---- pricing
def test_pricing_defaults_and_override(monkeypatch):
    p = get_pricing()
    assert (p.monthly, p.annual) == (4.99, 39.99) and p.annual_saving_percent == 33
    monkeypatch.setenv("PRICE_MONTHLY_GBP", "9.99")
    assert get_pricing().monthly_label() == "£9.99/month"
    monkeypatch.setenv("PRICE_MONTHLY_GBP", "junk")
    assert get_pricing().monthly == 4.99


# ---- learning
def test_modules_are_valid_and_model_answers_pass():
    modules = learning.load_modules()
    assert len(modules) >= 4
    ids = learning.exercise_ids(modules)
    assert len(ids) == len(set(ids))
    assert any(m["access"] == "free" for m in modules)
    for m in modules:
        for e in m["exercises"]:
            assert e["checks"] and sum(c["weight"] for c in e["checks"]) > 0
            assert learning.grade(e, "") .score < e["pass_mark"], e["id"]


def test_model_tips_score_well():
    for m in learning.load_modules():
        for e in m["exercises"]:
            tip = e["model_answer_tip"]
            quoted = tip[tip.find("'") + 1: tip.rfind("'")]
            assert learning.grade(e, quoted).passed, (e["id"], learning.grade(e, quoted).missing_hints)


def test_grade_feedback_and_unknown_check():
    ex = learning.load_modules()[0]["exercises"][0]
    g = learning.grade(ex, "Summarise this paper.")
    assert not g.passed and g.missing_hints
    with pytest.raises(ValueError):
        learning.grade({"checks": [{"type": "nope", "label": "x"}]}, "t")


def test_progress_tracking(db):
    store, modules = learning.ProgressStore(db), learning.load_modules()
    m = modules[0]
    for e in m["exercises"]:
        store.record("u", e["id"], 40, False)
    store.record("u", m["exercises"][0]["id"], 90, True)
    store.record("u", m["exercises"][0]["id"], 50, False)  # a worse later attempt keeps the best
    prog = store.for_user("u")
    first = prog[m["exercises"][0]["id"]]
    assert first["best_score"] == 90 and first["attempts"] == 3 and first["passed"] == 1
    s = learning.module_summary(m, prog)
    assert s["done"] == 1 and not learning.certificate_ready(m, prog)
    assert 0 < learning.overall_percent(modules, prog) < 100
