"""Streamlit glue: shared services, the signed-in user, and the premium entitlement for this visitor.

A visitor is premium if they hold a valid access code (workshops) or their account has an active paid grant.
Streamlit keeps the sign-in in the browser session only, so a page refresh signs the learner out. That is a known
limit of Streamlit; the database holds everything else.
"""
from __future__ import annotations

import time

import streamlit as st

from accounts import AccountService, User
from billing import DbEntitlements
from db import Database, get_db
from entitlements import Entitlement
from learning import ProgressStore


@st.cache_resource
def _db() -> Database:
    return get_db()


def accounts() -> AccountService:
    return AccountService(_db())


def entitlements() -> DbEntitlements:
    return DbEntitlements(_db())


def progress_store() -> ProgressStore:
    return ProgressStore(_db())


def current_user() -> User | None:
    token = st.session_state.get("session_token", "")
    user = accounts().user_for_session(token) if token else None
    if token and user is None:
        st.session_state.pop("session_token", None)
    return user


def current_entitlement() -> Entitlement | None:
    """Access code first, then an active paid grant on the signed-in account."""
    code_ent = st.session_state.get("entitlement")
    if code_ent and code_ent.is_active():
        return code_ent  # type: ignore[no-any-return]
    user = current_user()
    if user:
        grant = entitlements().get(user.id)
        if grant:
            return Entitlement(subject=user.id, plan=grant["plan"], expires_at=grant["expires_at"])
    return None


def sign_in(token: str) -> None:
    st.session_state["session_token"] = token


def sign_out() -> None:
    token = st.session_state.pop("session_token", "")
    if token:
        accounts().logout(token)


def days_left(ent: Entitlement) -> int:
    return max(0, int((ent.expires_at - time.time()) // 86400))
