"""Data retention: delete what we no longer need. Run daily (scripts/purge.py) from a scheduler or cron.

Defaults (see docs/DATA_RETENTION.md), override with env vars of the same name in days:
  RETAIN_AUDIT_DAYS=365, RETAIN_LOGIN_ATTEMPT_DAYS=30, RETAIN_EVENT_DAYS=730, RETAIN_AI_USAGE_DAYS=400
Expired sessions and spent or expired email tokens are deleted straight away.
"""
from __future__ import annotations

import os
import time

from db import Database

DAY = 86400


def _days(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def purge(db: Database, now: float | None = None) -> dict[str, int]:
    now_i = int(now if now is not None else time.time())
    counts: dict[str, int] = {}
    jobs = {
        "sessions": ("DELETE FROM sessions WHERE expires_at<=?", now_i),
        "email_tokens": ("DELETE FROM email_tokens WHERE expires_at<=? OR used_at IS NOT NULL", now_i),
        "login_attempts": ("DELETE FROM login_attempts WHERE attempted_at<?", now_i - _days("RETAIN_LOGIN_ATTEMPT_DAYS", 30) * DAY),
        "audit_log": ("DELETE FROM audit_log WHERE ts<?", now_i - _days("RETAIN_AUDIT_DAYS", 365) * DAY),
        "events": ("DELETE FROM events WHERE received_at<?", now_i - _days("RETAIN_EVENT_DAYS", 730) * DAY),
        "ai_usage": ("DELETE FROM ai_usage WHERE month<?", time.strftime("%Y-%m", time.gmtime(now_i - _days("RETAIN_AI_USAGE_DAYS", 400) * DAY))),
    }
    for name, (sql, bound) in jobs.items():
        counts[name] = max(0, db.execute(sql, (bound,)).rowcount)
    db.commit()
    return counts
