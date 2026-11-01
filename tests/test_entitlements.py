import time

import pytest

from entitlements import can_view, issue_code, preview, verify_code

SECRET = "x" * 32
NOW = 1_800_000_000


def code(**kw):
    args = dict(secret=SECRET, subject="a@b.co", plan="student", expires_at=NOW + 1000)
    args.update(kw)
    return issue_code(**args)


def test_roundtrip():
    ent = verify_code(SECRET, code(), now=NOW)
    assert ent and ent.subject == "a@b.co" and ent.plan == "student"


def test_expired_rejected():
    assert verify_code(SECRET, code(), now=NOW + 2000) is None


def test_wrong_secret_rejected():
    assert verify_code("y" * 32, code(), now=NOW) is None


def test_tampered_payload_rejected():
    prefix, payload, sig = code().split(".")
    other = code(plan="workshop").split(".")[1]
    assert verify_code(SECRET, f"{prefix}.{other}.{sig}", now=NOW) is None


@pytest.mark.parametrize("bad", ["", "garbage", "PL1.a.b", "PL1..", "PL2.a.b", None, "a.b.c.d"])
def test_garbage_never_raises(bad):
    assert verify_code(SECRET, bad, now=NOW) is None


def test_fails_closed_without_secret():
    c = code()
    assert verify_code("", c, now=NOW) is None
    assert verify_code("short", c, now=NOW) is None


def test_issue_validates_input():
    with pytest.raises(ValueError):
        issue_code("short", "a", "student", NOW)
    with pytest.raises(ValueError):
        issue_code(SECRET, "a", "admin", NOW)


def test_can_view_rules():
    free, prem = {"title": "f"}, {"title": "p", "access": "premium"}
    ent = verify_code(SECRET, code(expires_at=int(time.time()) + 100))
    assert can_view(free, None) and not can_view(prem, None)
    assert can_view(prem, ent)
    assert not can_view(prem, ent, now=time.time() + 1000)


def test_preview_truncates():
    assert preview("a b c d", 2) == "a b ..."
    assert preview("a b", 5) == "a b"


def test_static_pro_access_code():
    ent = verify_code("", "PMPPTL26!!", subject="user@test.co.uk")
    assert ent is not None
    assert ent.plan == "pro"
    assert ent.subject == "user@test.co.uk"
    assert ent.is_active()
