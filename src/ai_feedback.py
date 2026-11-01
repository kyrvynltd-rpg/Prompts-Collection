"""Pro: AI feedback on a prompt. Off until you set an API key, and capped per user per month.

Works with any OpenAI-compatible chat-completions endpoint (OpenAI, Groq, OpenRouter, Together, Google Gemini):
  AI_API_KEY (required to switch on), AI_API_URL (default https://api.openai.com/v1/chat/completions),
  AI_MODEL (default gpt-4o-mini), AI_MONTHLY_CAP (default 30 requests per user).
Only the prompt text the learner submits is sent. No account details. Nothing is called unless a key is set.
The HTTP call is injectable, so tests never touch the network and never spend money.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from collections.abc import Callable

import audit
from db import Database

MAX_INPUT = 4000
DEFAULT_URL = "https://api.openai.com/v1/chat/completions"
SYSTEM = (
    "You are an elite prompt-writing coach for university students and researchers. "
    "Review the student's prompt with academic rigor and constructive insight. "
    "Provide exactly three structured sections:\n"
    "1) **What Works Well**: Specific strengths in role, task framing, or clarity.\n"
    "2) **Critical Gaps & Failure Modes**: The 2 most important missing elements (e.g. absent role, lack of constraints, missing output schema, risk of hallucination/confabulation, vague context).\n"
    "3) **Engineered Production Rewrite**: A polished, ready-to-use version of their prompt applying the TRACE framework and academic-integrity safeguards.\n"
    "Keep total output under 260 words. Never do the student's assignment for them. Always remind them to independently verify citations."
)

Transport = Callable[[str, dict, dict], dict]


class AIFeedbackError(RuntimeError):
    """A problem the user can read: off, over cap, or provider failure."""


def active_api_key() -> str:
    """Return active API key from environment or user session state."""
    key = (os.getenv("AI_API_KEY") or "").strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.session_state.get("user_ai_api_key", "")).strip()
    except Exception:
        return ""


def active_api_url() -> str:
    """Return active API URL endpoint."""
    url = (os.getenv("AI_API_URL") or "").strip()
    if url:
        return url
    try:
        import streamlit as st
        return str(st.session_state.get("user_ai_api_url", "")).strip() or DEFAULT_URL
    except Exception:
        return DEFAULT_URL


def active_model() -> str:
    """Return active model identifier."""
    m = (os.getenv("AI_MODEL") or "").strip()
    if m:
        return m
    try:
        import streamlit as st
        return str(st.session_state.get("user_ai_model", "")).strip() or "gpt-4o-mini"
    except Exception:
        return "gpt-4o-mini"


def enabled() -> bool:
    return bool(active_api_key())


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
    payload = {"model": active_model(), "max_tokens": 500,
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {active_api_key()}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        data = (transport or _http)(active_api_url(), headers, payload)
        msg = data["choices"][0]["message"]
        text = str(msg.get("content") or msg.get("reasoning") or "").strip()
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


def get_pedagogical_coach_critique(prompt: str) -> dict[str, str]:
    """Generate high-rigour pedagogical feedback and rewrite using structured heuristics.

    Used for interactive demonstration when external API keys are pending setup.
    """
    p = (prompt or "").strip()
    has_role = bool(re.search(r"\b(you are|act as|role|as an?)\b", p, re.I))
    has_format = bool(re.search(r"\b(table|bullet|json|list|step|markdown|words?)\b", p, re.I))
    has_neg = bool(re.search(r"\b(do not|don't|avoid|without|never|exclude)\b", p, re.I))
    has_cite_check = bool(re.search(r"\b(cite|source|verify|uncertain|check|reference)\b", p, re.I))

    strengths = []
    if len(p.split()) > 15:
        strengths.append("Provides a substantive initial task description rather than a single-word query.")
    if has_role:
        strengths.append("Establishes an explicit persona/role, priming the model's domain vocabulary.")
    if has_format:
        strengths.append("Requests a specific structural format, reducing post-generation editing time.")
    if not strengths:
        strengths.append("Identifies a clear core objective or subject matter to explore.")

    gaps = []
    if not has_role:
        gaps.append("Absence of an explicit expert Role (leaves tone, depth, and scholarly perspective to chance).")
    if not has_neg:
        gaps.append("Missing Negative Constraints (fails to prohibit conversational fluff, clichés, or unauthorized writing).")
    if not has_cite_check:
        gaps.append("No Epistemic/Integrity Check (models confabulate citations unless explicitly told to flag uncertainty).")
    if not has_format:
        gaps.append("Unspecified Output Structure (lacks clear length ceiling, schema, or tabular formatting).")
    if not gaps:
        gaps.append("Could further specify multi-step verification checkpoints for complex claims.")

    # Generate engineered rewrite applying TRACE framework
    base_clean = p.replace("\n", " ").strip()
    improved = (
        f"You are a subject-matter academic tutor and writing mentor. "
        f"Your task is to assist with the following objective:\n\n"
        f"\"{base_clean}\"\n\n"
        f"Adhere strictly to these execution guidelines:\n"
        f"1. Audience & Register: Postgraduate/Undergraduate university level; objective, rigorous, and clear.\n"
        f"2. Negative Constraints: Do not produce unrequested filler, generic introductions, or conversational conclusions.\n"
        f"3. Verification & Epistemic Humility: If citing facts or academic arguments, note the source. Explicitly state 'Unverified' if uncertain.\n"
        f"4. Format: Structure the output using concise bullet points and bold thematic headers. Limit to under 300 words."
    )

    return {
        "strengths": "\n".join(f"- {s}" for s in strengths),
        "gaps": "\n".join(f"- {g}" for g in gaps[:2]),
        "rewrite": improved,
    }
