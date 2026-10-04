import json

import pytest

from payments import EntitlementStore, handle_event, process_webhook, sign_webhook, verify_webhook

SECRET = "whsec_test_secret_value"
NOW = 1_800_000_000


class FakeProvider:
    def parse_webhook(self, body, headers):
        return json.loads(body)


def body(**kw):
    ev = {"id": "evt_1", "type": "payment.succeeded", "subject": "a@b.co", "plan": "student", "period_end": NOW + 86400}
    ev.update(kw)
    return json.dumps(ev).encode()


def test_signature_valid_and_invalid():
    b = body()
    sig = sign_webhook(SECRET, b, NOW)
    assert verify_webhook(SECRET, b, sig, NOW, now=NOW)
    assert not verify_webhook(SECRET, b + b" ", sig, NOW, now=NOW)
    assert not verify_webhook("other", b, sig, NOW, now=NOW)
    assert not verify_webhook(SECRET, b, "", NOW, now=NOW)


def test_replay_window():
    b = body()
    sig = sign_webhook(SECRET, b, NOW)
    assert not verify_webhook(SECRET, b, sig, NOW, now=NOW + 301)


def test_empty_secret_fails_closed():
    b = body()
    assert not verify_webhook("", b, sign_webhook("", b, NOW), NOW, now=NOW)


def test_grant_idempotent_and_revoke():
    s = EntitlementStore()
    ev = json.loads(body())
    assert handle_event(s, ev) == "applied"
    assert handle_event(s, ev) == "duplicate"
    assert s.get("a@b.co", now=NOW)["plan"] == "student"
    assert s.get("a@b.co", now=NOW + 86401) is None
    assert handle_event(s, {"id": "evt_2", "type": "subscription.cancelled", "subject": "a@b.co"}) == "applied"
    assert s.get("a@b.co", now=NOW) is None
    assert handle_event(s, {"id": "evt_3", "type": "something.else"}) == "ignored"


def test_process_webhook_rejects_bad_signature_without_side_effects():
    s = EntitlementStore()
    b = body()
    with pytest.raises(PermissionError):
        process_webhook(s, SECRET, b, "bad", NOW, FakeProvider(), now=NOW)
    assert s.get("a@b.co", now=NOW) is None


def test_process_webhook_happy_path():
    s = EntitlementStore()
    b = body()
    assert process_webhook(s, SECRET, b, sign_webhook(SECRET, b, NOW), NOW, FakeProvider(), now=NOW) == "applied"
    assert s.get("a@b.co", now=NOW)
