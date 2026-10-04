"""Security audit log. Records who did what and when, never secrets, passwords, tokens or message bodies.

Stored in the database (table audit_log) and mirrored to the standard `audit` logger so the host's log
collection (Render, Papertrail...) keeps a copy outside the database. Retention is set in retention.py.
"""
from __future__ import annotations

import hashlib
import logging
import time

from db import Database

logger = logging.getLogger("audit")

EVENTS = {
    "register", "login_ok", "login_fail", "login_locked", "logout", "password_reset_requested", "password_reset_done",
    "email_verified", "student_verified", "data_export", "account_deleted", "payment_event", "ai_feedback",
    "webhook_rejected",
}


def fingerprint(value: str) -> str:
    """Short one-way tag for an identifier (e.g. an email on a failed login) so logs hold no raw personal data."""
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()[:12]


def record(db: Database, event: str, user_id: str = "", detail: str = "", now: float | None = None) -> None:
    if event not in EVENTS:
        raise ValueError(f"unknown audit event {event!r}")
    ts = int(now if now is not None else time.time())
    detail = detail[:200]
    db.execute("INSERT INTO audit_log (ts, event, user_id, detail) VALUES (?,?,?,?)", (ts, event, user_id, detail))
    db.commit()
    logger.info("event=%s user=%s detail=%s", event, user_id or "-", detail)


def recent(db: Database, limit: int = 100) -> list[tuple]:
    return db.all("SELECT ts, event, user_id, detail FROM audit_log ORDER BY ts DESC LIMIT ?", (int(limit),))
