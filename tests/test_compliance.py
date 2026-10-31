import json
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.server import HTTPServer

import pytest

import audit
import brand
import retention
import webhook_server
from accounts import AccountError, AccountService, ConsoleMailer
from billing import DbEntitlements
from db import Database


@pytest.fixture
def db():
    return Database(":memory:")


@pytest.fixture
def svc(db):
    return AccountService(db, ConsoleMailer())


def _code(mailer, subject_word):
    msg = [m for m in mailer.outbox if subject_word in m[1]][-1]
    return msg[2].split("code is: ")[1].split("\n")[0]


# ---- audit
def test_audit_records_and_rejects_unknown(db):
    audit.record(db, "register", "u1", "x", now=5)
    assert audit.recent(db)[0][:3] == (5, "register", "u1")
    with pytest.raises(ValueError):
        audit.record(db, "made_up")
    assert audit.fingerprint(" A@B.co ") == audit.fingerprint("a@b.co") and "a@b.co" not in audit.fingerprint("a@b.co")


def test_account_actions_are_audited_without_secrets(svc, db):
    user = svc.register("a@b.co", "a-long-password")
    _, token = svc.login("a@b.co", "a-long-password")
    with pytest.raises(AccountError):
        svc.login("a@b.co", "wrong-password-1")
    svc.logout(token)
    svc.logout(token)  # second logout is harmless
    svc.export_data(user.id)
    svc.delete_account(user.id)
    events = [r[1] for r in audit.recent(db, 50)]
    for expected in ("register", "login_ok", "login_fail", "logout", "data_export", "account_deleted"):
        assert expected in events
    blob = json.dumps(audit.recent(db, 50))
    assert "a-long-password" not in blob and token not in blob and "a@b.co" not in blob


def test_lockout_is_audited(svc, db):
    svc.register("a@b.co", "a-long-password")
    for _ in range(5):
        with pytest.raises(AccountError):
            svc.login("a@b.co", "wrong-password-1")
    with pytest.raises(AccountError):
        svc.login("a@b.co", "a-long-password")
    assert "login_locked" in [r[1] for r in audit.recent(db, 50)]


# ---- password rules, terms, email verification, reset
@pytest.mark.parametrize("pw", ["password123", "short", "aaaaaaaaaaaa", "a@b.co" * 2])
def test_weak_passwords_rejected(svc, pw):
    with pytest.raises(AccountError):
        svc.register("a@b.co", pw) if pw != "a@b.co" * 2 else svc.register("a@b.co", "A@B.CO".lower())


def test_terms_must_be_accepted_and_are_recorded(svc, db):
    with pytest.raises(AccountError, match="Terms"):
        svc.register("a@b.co", "a-long-password", accept_terms=False)
    user = svc.register("a@b.co", "a-long-password")
    row = db.one("SELECT terms_accepted_at, terms_version FROM users WHERE id=?", (user.id,))
    assert row[0] and row[1]


def test_email_verification(svc, monkeypatch):
    from accounts import email_delivery_enabled
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("EMAIL_API_KEY", raising=False)
    assert not email_delivery_enabled(svc.mailer)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")
    assert email_delivery_enabled(svc.mailer)

    class LiveMailer:
        def send(self, to: str, subject: str, body: str) -> None:
            pass

    assert email_delivery_enabled(LiveMailer())
    user = svc.register("a@b.co", "a-long-password")
    assert not svc.is_email_verified(user.id)
    with pytest.raises(AccountError):
        svc.confirm_email(user.id, "wrong")
    svc.confirm_email(user.id, _code(svc.mailer, "Confirm your email"))
    assert svc.is_email_verified(user.id)
    with pytest.raises(AccountError):
        svc.confirm_email(user.id, _code(svc.mailer, "Confirm your email"))  # single use


def test_password_reset_flow(svc):
    user = svc.register("a@b.co", "a-long-password")
    _, old_token = svc.login("a@b.co", "a-long-password")
    n = len(svc.mailer.outbox)
    svc.request_password_reset("nobody@b.co")
    assert len(svc.mailer.outbox) == n  # no email, and no error either: no account enumeration
    svc.request_password_reset("A@B.co")
    code = _code(svc.mailer, "Reset your password")
    with pytest.raises(AccountError):
        svc.reset_password("a@b.co", "wrong", "another-long-password")
    with pytest.raises(AccountError):
        svc.reset_password("a@b.co", code, "short")  # rules apply, code not burned
    svc.reset_password("a@b.co", code, "another-long-password")
    assert svc.user_for_session(old_token) is None  # signed out everywhere
    svc.login("a@b.co", "another-long-password")
    with pytest.raises(AccountError):
        svc.login("a@b.co", "a-long-password")
    with pytest.raises(AccountError):
        svc.reset_password("a@b.co", code, "yet-another-password")  # single use
    with pytest.raises(AccountError):
        svc.reset_password("ghost@b.co", code, "yet-another-password")
    assert svc.get_user(user.id)


def test_reset_code_expires(svc):
    svc.register("a@b.co", "a-long-password")
    svc.request_password_reset("a@b.co")
    with pytest.raises(AccountError):
        svc.reset_password("a@b.co", _code(svc.mailer, "Reset"), "another-long-password", now=time.time() + 7200)


def test_export_includes_workspace_and_delete_erases_everything(svc, db):
    from workspace import Workspace
    user = svc.register("a@b.co", "a-long-password")
    Workspace(db).save(user.id, "t", "body body body")
    db.execute("INSERT INTO ai_usage VALUES (?,?,?)", (user.id, "2026-10", 3))
    DbEntitlements(db).grant(user.id, "pro", 9_999_999_999)
    DbEntitlements(db).link_customer("cus_x", user.id)
    db.commit()
    assert svc.export_data(user.id)["workspace_prompts"][0]["title"] == "t"
    with pytest.raises(AccountError):
        svc.export_data("missing")
    svc.delete_account(user.id)
    for table, col in (("workspace_prompts", "user_id"), ("ai_usage", "user_id"), ("grants", "subject"), ("customers", "user_id")):
        assert db.one(f"SELECT COUNT(*) FROM {table} WHERE {col}=?", (user.id,))[0] == 0


# ---- retention
def test_purge_removes_old_data_and_keeps_new(db, monkeypatch):
    now = 1_800_000_000
    db.execute("INSERT INTO sessions VALUES ('old','u',1,?)", (now - 10,))
    db.execute("INSERT INTO sessions VALUES ('live','u',1,?)", (now + 10,))
    db.execute("INSERT INTO email_tokens VALUES ('t1','u','reset',?,NULL)", (now - 1,))
    db.execute("INSERT INTO email_tokens VALUES ('t2','u','reset',?,?)", (now + 99, now - 5))
    db.execute("INSERT INTO email_tokens VALUES ('t3','u','reset',?,NULL)", (now + 99,))
    db.execute("INSERT INTO login_attempts VALUES ('a',?,0)", (now - 40 * 86400,))
    db.execute("INSERT INTO login_attempts VALUES ('a',?,0)", (now - 86400,))
    db.execute("INSERT INTO audit_log VALUES (?,'login_ok','u','')", (now - 400 * 86400,))
    db.execute("INSERT INTO audit_log VALUES (?,'login_ok','u','')", (now - 86400,))
    db.execute("INSERT INTO events VALUES ('e1',?)", (now - 800 * 86400,))
    db.execute("INSERT INTO ai_usage VALUES ('u','2020-01',1)")
    db.execute("INSERT INTO ai_usage VALUES ('u','2027-01',1)")
    db.commit()
    counts = retention.purge(db, now)
    assert counts == {"sessions": 1, "email_tokens": 2, "login_attempts": 1, "audit_log": 1, "events": 1, "ai_usage": 1}
    assert db.one("SELECT COUNT(*) FROM sessions")[0] == 1
    monkeypatch.setenv("RETAIN_AUDIT_DAYS", "junk")
    assert retention._days("RETAIN_AUDIT_DAYS", 365) == 365
    monkeypatch.setenv("RETAIN_AUDIT_DAYS", "0")
    assert retention._days("RETAIN_AUDIT_DAYS", 365) == 1


# ---- backup script
def test_backup_creates_a_readable_copy(tmp_path, monkeypatch):
    import importlib.util
    import os
    import sys
    from pathlib import Path

    import db as dbmod
    dbfile = tmp_path / "live.db"
    live = Database(str(dbfile))
    live.execute("INSERT INTO audit_log VALUES (1,'register','u','')")
    live.commit()
    monkeypatch.setattr(dbmod, "_shared", live)
    spec = importlib.util.spec_from_file_location("backup_script", Path(__file__).resolve().parent.parent / "scripts" / "backup.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["backup_script"] = mod
    spec.loader.exec_module(mod)
    out = mod.backup(str(tmp_path / "b"))
    assert sqlite3.connect(out).execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 1
    if os.name != "nt":
        assert oct(out.stat().st_mode)[-3:] == "600"
    else:
        assert out.exists() and out.stat().st_size > 0
    live.is_postgres = True
    with pytest.raises(SystemExit):
        mod.backup(str(tmp_path / "b2"))
    live.is_postgres = False


# ---- brand
def test_owner_shown_and_overridable(monkeypatch):
    assert "Kyrvyn Ltd" in brand.copyright_line() and "kyrvynltd.co.uk" in brand.site_url()
    assert "17246800" in brand.company_line() and "Exning Road" in brand.company_line()
    monkeypatch.setenv("COMPANY_NUMBER", "12345678")
    monkeypatch.setenv("CONTACT_EMAIL", "hi@kyrvynltd.co.uk")
    assert "12345678" in brand.company_line() and brand.contact_email() == "hi@kyrvynltd.co.uk"


def test_owner_appears_in_all_public_files():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    for name in ("LICENSE", "README.md", "docs/TERMS.md", "docs/PRIVACY.md", "SECURITY.md", "landing/index.html", "docs/OWNERSHIP.md"):
        assert "Kyrvyn Ltd" in (root / name).read_text(encoding="utf-8"), name
    for name in ("LICENSE", "README.md", "landing/index.html", "src/app.py", "src/ui.py"):
        assert "Gabriele Iacopo Langellotto. All rights reserved" not in (root / name).read_text(encoding="utf-8"), name


# ---- real HTTP webhook server
@pytest.fixture
def server(monkeypatch):
    import db as dbmod
    shared = Database(":memory:")
    monkeypatch.setattr(dbmod, "_shared", shared)
    monkeypatch.setattr(webhook_server, "get_db", lambda: shared)
    httpd = HTTPServer(("127.0.0.1", 0), webhook_server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", shared
    httpd.shutdown()


def _req(url, data=None, headers=None):
    request = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_http_health_unknown_and_rejected(server):
    base, shared = server
    assert _req(base + "/health") == (200, "ok")
    assert _req(base + "/nope")[0] == 404
    assert _req(base + "/webhooks/stripe", b"{}")[0] == 400
    assert _req(base + "/webhooks/unknown", b"{}")[0] == 404
    assert "webhook_rejected" in [r[1] for r in audit.recent(shared)]


def test_http_rejects_oversized_body(server):
    base, _ = server
    request = urllib.request.Request(base + "/webhooks/stripe", data=b"x", method="POST", headers={"Content-Length": "2000000"})
    with pytest.raises((urllib.error.HTTPError, urllib.error.URLError, ConnectionError)):
        urllib.request.urlopen(request, timeout=5)
