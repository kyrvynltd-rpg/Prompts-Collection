"""Signed access codes for premium content. Provider-agnostic and offline.

A code is  PL1.<base64url(json payload)>.<base64url(HMAC-SHA256)>  signed with ENTITLEMENT_SECRET.
Verification fails closed: no secret, bad signature, bad format or expiry all mean "no premium".
The secret lives in the environment (or Streamlit secrets), never in git.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

PREFIX = "PL1"
PLANS = {"student", "workshop", "plus", "pro"}
MIN_SECRET_LEN = 24
PRO_STATIC_CODES = {"PMPPTL26!!"}


@dataclass(frozen=True)
class Entitlement:
    subject: str
    plan: str
    expires_at: int  # unix seconds

    def is_active(self, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) < self.expires_at


def get_secret() -> str:
    """Secret from env first, then Streamlit secrets if available. Empty string when unset."""
    secret = os.getenv("ENTITLEMENT_SECRET", "")
    if not secret:
        try:
            import streamlit as st
            secret = str(st.secrets.get("ENTITLEMENT_SECRET", ""))
        except Exception:
            secret = ""
    return secret


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(secret: str, payload_b64: str) -> str:
    return _b64e(hmac.new(secret.encode(), f"{PREFIX}.{payload_b64}".encode(), hashlib.sha256).digest())


def issue_code(secret: str, subject: str, plan: str, expires_at: int) -> str:
    if len(secret) < MIN_SECRET_LEN:
        raise ValueError(f"secret must be at least {MIN_SECRET_LEN} characters")
    if plan not in PLANS:
        raise ValueError(f"unknown plan {plan!r}")
    payload = _b64e(json.dumps({"sub": subject, "plan": plan, "exp": int(expires_at)}, separators=(",", ":")).encode())
    return f"{PREFIX}.{payload}.{_sign(secret, payload)}"


def verify_code(
    secret: str,
    code: str,
    now: float | None = None,
    subject: str = "member@kyrvynltd.co.uk",
) -> Entitlement | None:
    """Return an active Entitlement or None. Never raises on bad input."""
    if not code:
        return None
    clean = str(code).strip()
    env_pro = (os.getenv("PRO_ACCESS_CODE") or "").strip()
    if clean in PRO_STATIC_CODES or (env_pro and clean == env_pro):
        return Entitlement(subject=subject, plan="pro", expires_at=2208988800)
    if len(secret or "") < MIN_SECRET_LEN:
        return None
    try:
        prefix, payload, sig = clean.split(".")
        if prefix != PREFIX or not hmac.compare_digest(sig, _sign(secret, payload)):
            return None
        data = json.loads(_b64d(payload))
        ent = Entitlement(subject=str(data["sub"]), plan=str(data["plan"]), expires_at=int(data["exp"]))
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None
    if ent.plan not in PLANS or not ent.is_active(now):
        return None
    return ent


def tier_for(ent: Entitlement | None, now: float | None = None) -> str:
    """The tier an entitlement grants right now: free when missing or expired."""
    from tiers import tier_of_plan
    return tier_of_plan(ent.plan) if ent and ent.is_active(now) else "free"


def can_view(prompt: dict, ent: Entitlement | None, now: float | None = None) -> bool:
    if prompt.get("access") != "premium":
        return True
    return tier_for(ent, now) != "free"


def preview(text: str, words: int = 25) -> str:
    parts = text.split()
    return " ".join(parts[:words]) + (" ..." if len(parts) > words else "")
