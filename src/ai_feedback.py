"""Pro: AI feedback on a prompt. Off until you set an API key, and capped per user per month.

Works with any OpenAI-compatible chat-completions endpoint (OpenAI, OpenRouter, Together, a local server...):
  AI_API_KEY (required to switch on), AI_API_URL (default https://api.openai.com/v1/chat/completions),
  AI_MODEL (default gpt-4o-mini), AI_MONTHLY_CAP (default 30 requests per user).
Only the prompt text the learner submits is sent. No account details. Nothing is called unless a key is set.
The HTTP call is injectable, so tests never touch the network and never spend money.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from collections.abc import Callable

import audit
from db import Database

MAX_INPUT = 4000
DEFAULT_URL = "https://api.openai.com/v1/chat/completions"
SYSTEM = (
    "You are a prompt-writing coach for university students. Review the prompt the student wrote. Give: 1) what works, "
    "2) the two most important gaps (role, task, context, constraints, format, checkability), 3) a short improved version. "
    "Under 220 words. Do not do the student's assignment for them. Remind them to verify facts."
)

Transport = Callable[[str, dict, dict], dict]


class AIFeedbackError(RuntimeError):
    """A problem the user can read: off, over cap, or provider failure."""


def enabled() -> bool:
    return bool(os.getenv("AI_API_KEY"))


def monthly_cap() -> int:
    try:
        return max(0, int(os.getenv("AI_MONTHLY_CAP", "30")))
    except ValueError:
        return 30


def month_key(now: float | None = None) -> str:
    return time.strftime("%Y-%m", time.gmtime(now if now is not None else time.time()))


def used(db: Database, user_id: str, now: float | None = None) -> int:
    row = db.one("SELECT count FROM ai_usage WHERE user_id=? AND month=?", (user_id, month_key(now)))
    return int(row[0]) if row else 0


def remaining(db: Database, user_id: str, now: float | None = None) -> int:
    return max(0, monthly_cap() - used(db, user_id, now))


def _http(url: str, headers: dict, payload: dict) -> dict:  # pragma: no cover - real network call
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - URL comes from operator config
        return json.loads(resp.read())


def get_feedback(db: Database, user_id: str, prompt: str, transport: Transport | None = None, now: float | None = None) -> str:
    if not enabled():
        raise AIFeedbackError("AI feedback is not switched on for this deployment yet.")
    prompt = (prompt or "").strip()
    if len(prompt) < 10:
        raise AIFeedbackError("Write a longer prompt first.")
    if len(prompt) > MAX_INPUT:
        raise AIFeedbackError(f"Keep the prompt under {MAX_INPUT} characters.")
    if remaining(db, user_id, now) <= 0:
        raise AIFeedbackError("You have used this month's AI feedback allowance. It resets next month.")
    payload = {"model": os.getenv("AI_MODEL", "gpt-4o-mini"), "max_tokens": 450,
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {os.getenv('AI_API_KEY', '')}", "Content-Type": "application/json"}
    try:
        data = (transport or _http)(os.getenv("AI_API_URL", DEFAULT_URL), headers, payload)
        text = str(data["choices"][0]["message"]["content"]).strip()
    except Exception as exc:  # network, HTTP, or unexpected shape: never leak internals or the key
        raise AIFeedbackError("The AI service did not answer. Try again later. This did not use your allowance.") from exc
    month = month_key(now)  # count only successful answers
    if db.one("SELECT 1 FROM ai_usage WHERE user_id=? AND month=?", (user_id, month)):
        db.execute("UPDATE ai_usage SET count=count+1 WHERE user_id=? AND month=?", (user_id, month))
    else:
        db.execute("INSERT INTO ai_usage (user_id, month, count) VALUES (?,?,1)", (user_id, month))
    db.commit()
    audit.record(db, "ai_feedback", user_id)
    return text
