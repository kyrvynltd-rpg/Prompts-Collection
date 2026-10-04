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
    for name in ("STRIPE_LINK_PLUS_MONTHLY", "LEMONSQUEEZY_LINK_PLUS_MONTHLY", "PAYPAL_LINK_PRO_ANNUAL"):
        monkeypatch.delenv(name, raising=False)
    assert billing.checkout_url("stripe", "u", "a@b.co") is None
    monkeypatch.setenv("STRIPE_LINK_PLUS_MONTHLY", "https://buy.example/abc")
    assert "client_reference_id=u" in billing.checkout_url("stripe", "u", "a@b.co")
    assert billing.checkout_url("stripe", "u", "a@b.co", "pro", "annual") is None
    monkeypatch.setenv("LEMONSQUEEZY_LINK_PLUS_MONTHLY", "https://s.example/checkout/buy/1?x=1")
    assert "%5Buser_id%5D=u" in billing.checkout_url("lemonsqueezy", "u", "a@b.co")
    monkeypatch.setenv("PAYPAL_LINK_PRO_ANNUAL", "https://paypal.example/s")
    assert "custom_id=u%3Apro" in billing.checkout_url("paypal", "u", "a@b.co", "pro", "annual")
    assert billing.configured_providers() == ["stripe", "lemonsqueezy"]


def test_renewal_keeps_the_tier_the_user_bought(db):
    store, now = DbEntitlements(db), int(time.time())
    billing.apply_event(store, {"id": "a", "type": "payment.succeeded", "subject": "u9", "customer": "c9", "plan": "pro", "period_end": now + 100})
    billing.apply_event(store, {"id": "b", "type": "payment.succeeded", "subject": None, "customer": "c9", "plan": None, "period_end": now + 999})
    assert store.get("u9")["plan"] == "pro" and store.get("u9")["expires_at"] == now + 999


def test_paypal_tier_from_custom_id(db):
    body = json.dumps({"id": "WH-2", "event_type": "BILLING.SUBSCRIPTION.ACTIVATED", "resource": {"id": "I-2", "custom_id": "u4:pro"}}).encode()
    store = DbEntitlements(db)
    billing.process_provider_webhook(store, PayPalProvider(lambda b, h: True), "", body, {})
    assert store.get("u4")["plan"] == "pro"


def test_webhook_server_handler(db, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "s")
    store = DbEntitlements(db)
    assert webhook_server.handle("/webhooks/nope", b"", {}, store)[0] == 404
    assert webhook_server.handle("/webhooks/stripe", b"{}", {}, store)[0] == 400
    body, now = b'{"id":"e1","type":"ignored.type"}', int(time.time())
    assert webhook_server.handle("/webhooks/stripe", body, _stripe_headers("s", body, now), store) == (200, "ignored")


# ---- pricing and tiers
def test_pricing_defaults_and_override(monkeypatch):
    for name in ("PRICE_PLUS_MONTHLY_GBP", "PRICE_PRO_MONTHLY_GBP"):
        monkeypatch.delenv(name, raising=False)
    p = get_pricing()
    assert p.get("plus", "monthly").label() == "\u00a34.99/month" and p.get("plus", "annual").amount == 39.99
    assert p.get("pro", "monthly").amount == 9.99 and p.get("pro", "annual").amount == 99.99
    assert p.annual_saving_percent("plus") == 33
    monkeypatch.setenv("PRICE_PLUS_MONTHLY_GBP", "5.99")
    assert get_pricing().get("plus", "monthly").amount == 5.99
    monkeypatch.setenv("PRICE_PLUS_MONTHLY_GBP", "junk")
    assert get_pricing().get("plus", "monthly").amount == 4.99


def test_tiers_and_gating():
    from entitlements import Entitlement, can_view, tier_for
    from tiers import allows, tier_of_plan
    assert tier_of_plan("student") == "plus" and tier_of_plan("workshop") == "pro" and tier_of_plan(None) == "free"
    assert allows("pro", "plus") and not allows("plus", "pro") and allows("free", "free")
    live, dead = Entitlement("u", "pro", 4_000_000_000), Entitlement("u", "plus", 1)
    assert tier_for(live) == "pro" and tier_for(dead) == "free" and tier_for(None) == "free"
    assert can_view({"access": "premium"}, Entitlement("u", "plus", 4_000_000_000))
    assert not can_view({"access": "premium"}, dead)


def test_module_tiers():
    mods = {m["id"]: m for m in learning.load_modules()}
    assert learning.required_tier(mods["m1-foundations"]) == "free"
    assert learning.required_tier(mods["m2-precision"]) == "plus"
    assert learning.required_tier(mods["m5-advanced"]) == "pro"


# ---- workspace
def test_workspace_crud_isolation_and_export(db):
    from workspace import Workspace, WorkspaceError
    ws = Workspace(db)
    pid = ws.save("u1", "Essay helper", "Plan my essay", "study, essay")
    ws.save("u2", "Other", "not yours")
    assert [i["title"] for i in ws.list("u1")] == ["Essay helper"] and ws.list("u1", "essay")[0]["tags"] == ["study", "essay"]
    assert ws.list("u1", "zzz") == []
    ws.save("u1", "Essay helper v2", "Plan my essay better", "", prompt_id=pid)
    assert ws.list("u1")[0]["title"] == "Essay helper v2"
    with pytest.raises(WorkspaceError):
        ws.save("u2", "x", "y", prompt_id=pid)  # cannot edit someone else's prompt
    with pytest.raises(WorkspaceError):
        ws.save("u1", "", "")
    with pytest.raises(WorkspaceError):
        ws.save("u1", "t", "x" * 9000)
    assert "Essay helper v2" in ws.export_markdown("u1") and json.loads(ws.export_json("u1"))[0]["id"] == pid
    ws.delete("u2", pid)  # no effect on another user's prompt
    assert len(ws.list("u1")) == 1
    ws.delete("u1", pid)
    assert ws.list("u1") == []


# ---- ai feedback
def test_ai_feedback_off_cap_and_failure(db, monkeypatch):
    import ai_feedback as ai
    monkeypatch.delenv("AI_API_KEY", raising=False)
    with pytest.raises(ai.AIFeedbackError, match="not switched on"):
        ai.get_feedback(db, "u", "a prompt that is long enough")
    monkeypatch.setenv("AI_API_KEY", "sk-secret-123")
    monkeypatch.setenv("AI_MONTHLY_CAP", "2")
    calls = []

    def ok(url, headers, payload):
        calls.append(payload)
        return {"choices": [{"message": {"content": "Looks good."}}]}

    assert ai.get_feedback(db, "u", "a prompt that is long enough", ok) == "Looks good."
    assert "sk-secret-123" not in json.dumps(calls[0])  # the key goes in a header only
    assert ai.remaining(db, "u") == 1

    def boom(url, headers, payload):
        raise OSError("network")

    with pytest.raises(ai.AIFeedbackError, match="did not use your allowance"):
        ai.get_feedback(db, "u", "a prompt that is long enough", boom)
    assert ai.remaining(db, "u") == 1  # failures are free
    ai.get_feedback(db, "u", "a prompt that is long enough", ok)
    with pytest.raises(ai.AIFeedbackError, match="allowance"):
        ai.get_feedback(db, "u", "a prompt that is long enough", ok)
    assert ai.remaining(db, "u", now=time.time() + 40 * 86400) == 2  # next month resets
    with pytest.raises(ai.AIFeedbackError):
        ai.get_feedback(db, "other", "short", ok)
    with pytest.raises(ai.AIFeedbackError):
        ai.get_feedback(db, "other", "x" * 5000, ok)
    monkeypatch.setenv("AI_MONTHLY_CAP", "junk")
    assert ai.monthly_cap() == 30


def test_templates_file():
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parent.parent / "data" / "templates.json").read_text())
    ids = [t["id"] for t in data["templates"]]
    assert len(ids) == len(set(ids)) >= 8 and all(t["body"] and t["title"] for t in data["templates"])


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
