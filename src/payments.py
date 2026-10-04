"""Payment integration scaffold: webhook signature checks, idempotent event handling, entitlement store.

Nothing here talks to a payment provider or moves money. A provider adapter (Stripe, Paddle, Lemon Squeezy...)
should translate its webhook into the normalised event below, and a small separate web service (not Streamlit,
which cannot receive webhooks) should call `process_webhook`.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from typing import Protocol

TOLERANCE_SECONDS = 300


class PaymentProvider(Protocol):
    """What a provider adapter must implement."""

    def parse_webhook(self, body: bytes, headers: dict[str, str]) -> dict:
        """Return a normalised event: {id, type, subject, plan, period_end} or raise ValueError."""


def sign_webhook(secret: str, body: bytes, timestamp: int) -> str:
    return hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def verify_webhook(secret: str, body: bytes, signature: str, timestamp: int, now: float | None = None) -> bool:
    """Constant-time HMAC check plus replay window. Fails closed when the secret is empty."""
    if not secret or not signature:
        return False
    if abs((now if now is not None else time.time()) - int(timestamp)) > TOLERANCE_SECONDS:
        return False
    return hmac.compare_digest(sign_webhook(secret, body, int(timestamp)), signature)


class EntitlementStore:
    """SQLite store of who has paid until when, with processed event ids for idempotency."""

    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS grants (subject TEXT PRIMARY KEY, plan TEXT NOT NULL, expires_at INTEGER NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, received_at INTEGER NOT NULL)")
        self.db.commit()

    def seen(self, event_id: str) -> bool:
        return self.db.execute("SELECT 1 FROM events WHERE id=?", (event_id,)).fetchone() is not None

    def grant(self, subject: str, plan: str, expires_at: int) -> None:
        self.db.execute("INSERT INTO grants VALUES (?,?,?) ON CONFLICT(subject) DO UPDATE SET plan=excluded.plan, expires_at=excluded.expires_at",
                        (subject, plan, int(expires_at)))

    def revoke(self, subject: str) -> None:
        self.db.execute("DELETE FROM grants WHERE subject=?", (subject,))

    def get(self, subject: str, now: float | None = None):
        row = self.db.execute("SELECT plan, expires_at FROM grants WHERE subject=?", (subject,)).fetchone()
        if not row or row[1] <= (now if now is not None else time.time()):
            return None
        return {"subject": subject, "plan": row[0], "expires_at": row[1]}

    def record_event(self, event_id: str) -> None:
        self.db.execute("INSERT INTO events VALUES (?,?)", (event_id, int(time.time())))


def handle_event(store: EntitlementStore, event: dict) -> str:
    """Apply a normalised event exactly once. Returns 'applied', 'duplicate' or 'ignored'."""
    if store.seen(event["id"]):
        return "duplicate"
    kind = event["type"]
    if kind == "payment.succeeded":
        store.grant(event["subject"], event["plan"], int(event["period_end"]))
        result = "applied"
    elif kind in ("subscription.cancelled", "payment.refunded"):
        store.revoke(event["subject"])
        result = "applied"
    else:
        result = "ignored"
    store.record_event(event["id"])
    store.db.commit()
    return result


def process_webhook(store: EntitlementStore, secret: str, body: bytes, signature: str, timestamp: int,
                    provider: PaymentProvider, headers: dict[str, str] | None = None, now: float | None = None) -> str:
    """Verify, parse and apply a webhook. Raises PermissionError on a bad signature."""
    if not verify_webhook(secret, body, signature, timestamp, now):
        raise PermissionError("invalid webhook signature")
    try:
        event = provider.parse_webhook(body, headers or {})
        json.dumps(event)
    except (ValueError, TypeError) as exc:
        raise ValueError("unparseable webhook") from exc
    return handle_event(store, event)
