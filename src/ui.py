"""Shared look and feel: responsive CSS, onboarding/login gate, plan comparison, header and footer."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

import brand

CSS = """
<style>
/* Modern Typography & Theme Adaptive Variables */
:root {
  --pl-bg: #f8fafc;
  --pl-surface: #ffffff;
  --pl-surface-elevated: #ffffff;
  --pl-card-bg: #ffffff;
  --pl-border: #e2e8f0;
  --pl-border-subtle: #f1f5f9;
  --pl-title: #0f172a;
  --pl-body: #334155;
  --pl-muted: #64748b;
  --pl-brand: #6366f1;
  --pl-brand-glow: rgba(99, 102, 241, 0.2);
  --pl-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.06);
  --pl-shadow-hover: 0 14px 30px -4px rgba(15, 23, 42, 0.12);
  --pl-pro-bg: linear-gradient(180deg, #fbfbfe 0%, #f5f3ff 100%);
  --pl-pro-border: #6366f1;
  --pl-pro-shadow: 0 8px 30px -4px rgba(99, 102, 241, 0.22);
}

@media (prefers-color-scheme: dark) {
  :root {
    --pl-bg: #090d16;
    --pl-surface: #0f172a;
    --pl-surface-elevated: #1e293b;
    --pl-card-bg: #1e293b;
    --pl-border: #334155;
    --pl-border-subtle: #1e293b;
    --pl-title: #f8fafc;
    --pl-body: #cbd5e1;
    --pl-muted: #94a3b8;
    --pl-brand: #818cf8;
    --pl-brand-glow: rgba(129, 140, 248, 0.3);
    --pl-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    --pl-shadow-hover: 0 14px 35px -4px rgba(0, 0, 0, 0.7);
    --pl-pro-bg: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
    --pl-pro-border: #818cf8;
    --pl-pro-shadow: 0 8px 30px -4px rgba(129, 140, 248, 0.35);
  }
}

/* Streamlit Native Theme Overrides (Ensures Dark Mode text is crisp & never white-on-white) */
[data-theme="dark"],
[data-testid="stAppViewContainer"][data-theme="dark"],
.stApp[data-theme="dark"] {
  --pl-bg: #090d16;
  --pl-surface: #0f172a;
  --pl-surface-elevated: #1e293b;
  --pl-card-bg: #1e293b;
  --pl-border: #334155;
  --pl-title: #f8fafc;
  --pl-body: #cbd5e1;
  --pl-muted: #94a3b8;
  --pl-pro-bg: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
  --pl-pro-border: #818cf8;
}

.block-container {
  max-width: 1080px;
  padding-top: 1.6rem;
  padding-bottom: 3rem;
}

/* Elite SaaS Header */
.pl-hero {
  text-align: center;
  padding: 1.2rem 0 0.8rem 0;
  margin-bottom: 1.2rem;
}
.pl-hero h1 {
  font-size: 2.35rem;
  font-weight: 850;
  letter-spacing: -0.035em;
  line-height: 1.15;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #2563eb 0%, #6366f1 40%, #8b5cf6 70%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.pl-sub {
  color: var(--pl-muted) !important;
  font-size: 1.05rem;
  max-width: 740px;
  margin: 0 auto 1.2rem auto;
  line-height: 1.55;
}

/* Badges with glow & smooth animations */
.pl-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.22rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  transition: all 0.2s ease;
}
.pl-free {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981 !important;
  border: 1px solid rgba(16, 185, 129, 0.35);
}
.pl-premium {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b !important;
  border: 1px solid rgba(245, 158, 11, 0.4);
}
.pl-pro {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8 !important;
  border: 1px solid rgba(99, 102, 241, 0.45);
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.2);
}

/* Elevated Cards with Glassmorphism & Contrast Safety */
.pl-card, .pl-plan-card {
  background: var(--pl-card-bg) !important;
  border: 1px solid var(--pl-border) !important;
  color: var(--pl-body) !important;
  border-radius: 16px;
  padding: 1.35rem 1.4rem;
  margin-bottom: 1.1rem;
  box-shadow: var(--pl-shadow);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.pl-card:hover, .pl-plan-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--pl-shadow-hover);
  border-color: #818cf8 !important;
}

.pl-card h4, .pl-plan-card h4 {
  color: var(--pl-title) !important;
  font-size: 1.15rem;
  font-weight: 750;
  letter-spacing: -0.015em;
  margin: 0.55rem 0 0.35rem 0;
}
.pl-card p, .pl-plan-card p {
  color: var(--pl-muted) !important;
  font-size: 0.91rem;
  line-height: 1.55;
  margin-bottom: 0.65rem;
}
.pl-card ul, .pl-plan-card ul {
  color: var(--pl-body) !important;
  font-size: 0.89rem;
  line-height: 1.62;
  padding-left: 1.15rem;
  margin-top: 0.4rem;
}
.pl-card li, .pl-plan-card li {
  color: var(--pl-body) !important;
  margin-bottom: 0.35rem;
}
.pl-card li b, .pl-plan-card li b {
  color: var(--pl-title) !important;
}

/* Flagship PRO Plan Card */
.pl-plan-pro {
  background: var(--pl-pro-bg) !important;
  border: 2px solid var(--pl-pro-border) !important;
  box-shadow: var(--pl-pro-shadow) !important;
  position: relative;
}
.pl-plan-pro:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px -4px rgba(99, 102, 241, 0.35) !important;
}

.pl-popular-ribbon {
  display: inline-block;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #ffffff !important;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.2rem 0.65rem;
  border-radius: 6px;
  margin-bottom: 0.45rem;
  width: fit-content;
}

/* Top Navigation & Status Bar */
.pl-status-bar {
  background: var(--pl-card-bg);
  border: 1px solid var(--pl-border);
  border-radius: 14px;
  padding: 0.75rem 1.15rem;
  margin-bottom: 1.4rem;
  box-shadow: var(--pl-shadow);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pl-nav-card {
  background: var(--pl-card-bg);
  border: 1px solid var(--pl-border);
  border-radius: 12px;
  padding: 0.85rem 1rem;
  margin-bottom: 0.6rem;
  text-align: center;
  transition: all 0.2s ease;
}
.pl-nav-card:hover {
  border-color: #6366f1;
  transform: translateY(-2px);
}

.pl-weak {
  border-left: 4px solid #ef4444;
  padding: .65rem .95rem;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 8px;
  font-size: 0.95rem;
  color: var(--pl-title) !important;
}

.pl-footer {
  text-align: center;
  color: var(--pl-muted) !important;
  font-size: .83rem;
  padding: 2.5rem 0 1.2rem;
  border-top: 1px solid var(--pl-border);
  margin-top: 2.5rem;
}
.pl-footer a {
  color: #818cf8;
  text-decoration: none;
}
.pl-footer a:hover {
  text-decoration: underline;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .block-container { padding: 1rem 0.75rem; }
  .pl-hero h1 { font-size: 1.75rem; }
  .pl-sub { font-size: 0.95rem; margin-bottom: 1rem; }
  .pl-card, .pl-plan-card { padding: 1.1rem 1rem; }
  div[data-testid="stMetricValue"] { font-size: 1.35rem; }
}
</style>
"""


def sync_runtime_env() -> None:
    """Populate os.environ from Streamlit Cloud st.secrets or local .env outside pytest."""
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        return
    try:
        for k, v in st.secrets.items():
            if isinstance(v, (str, int, float)) and str(v).strip() and "[YOUR-PASSWORD]" not in str(v):
                os.environ.setdefault(str(k), str(v).strip())
    except Exception:
        pass
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            val = v.strip().strip("\"'")
            if k.strip() and val and "[YOUR-PASSWORD]" not in val:
                os.environ.setdefault(k.strip(), val)


def render_plans_comparison(user=None, key_prefix: str = "plans") -> None:
    """Render a clear 3-tier breakdown (Free, Plus, Pro) with prices, features, and checkout links."""
    from billing import checkout_url, configured_providers
    from pricing import get_pricing

    price = get_pricing()
    st.markdown("### 💳 Plans & Included Functionalities")
    st.caption(
        "Every account starts on the Free tier. Upgrade to **Plus** or **Pro** (or use access code `PMPPTL26!!`) "
        "to unlock premium prompt collections, advanced learning modules, personal workspace, and AI coaching."
    )

    period = st.radio(
        "Billing cycle",
        ["monthly", "annual"],
        horizontal=True,
        format_func=lambda p: "Monthly billing" if p == "monthly" else "Annual billing (save up to 33%)",
        key=f"{key_prefix}_period",
    )

    c_free, c_plus, c_pro = st.columns(3)

    with c_free:
        st.markdown(
            "<div class='pl-plan-card'>"
            "<span class='pl-badge pl-free'>FREE TIER</span>"
            "<h4>£0 <small style='font-weight:normal;opacity:0.75;'>/ forever</small></h4>"
            "<p>Core prompt analysis & foundational practice with an account.</p>"
            "<ul>"
            "<li><b>Prompt Analyser</b>: instant clarity, specificity, context & structure scoring + improved rewrite</li>"
            "<li><b>Smart Discovery</b>: filter & match prompts by difficulty, time & output format</li>"
            "<li><b>Practice Mode</b>: all 10 rubric-graded student exercises</li>"
            "<li><b>Learn — Module 1 (Foundations)</b>: 3 graded lessons on Role, Task & Context</li>"
            "<li><b>Free Prompt Library</b>: starter prompts & academic-integrity guidance</li>"
            "<li><b>Account Controls</b>: saved progress & full JSON data export</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c_plus:
        plus_p = price.get("plus", period)
        plus_save = f" · Save {price.annual_saving_percent('plus')}%" if period == "annual" else ""
        st.markdown(
            "<div class='pl-plan-card'>"
            f"<span class='pl-badge pl-premium'>PLUS TIER{plus_save}</span>"
            f"<h4>{plus_p.label()}</h4>"
            "<p>Full prompt library & core curriculum for regular study.</p>"
            "<ul>"
            "<li><b>Everything in Free</b>, plus:</li>"
            "<li>🔓 <b>Full 100+ Premium Prompt Library</b> across all categories & complete Student Pack</li>"
            "<li>🔓 <b>Module 2 — Precision</b>: constraints, output formats & few-shot examples (3 exercises)</li>"
            "<li>🔓 <b>Module 3 — Rigour</b>: checkable, honest & academic-integrity-safe prompting (3 exercises)</li>"
            "<li>🔓 <b>Module 4 — Applied</b>: study, revision, career & project workflows (3 exercises)</li>"
            "<li>🎓 <i>Also unlocked via verified student (<code>.ac.uk</code>) access codes</i></li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )
        if user is not None:
            providers = configured_providers("plus", period)
            for prov in providers:
                link = checkout_url(prov, user.id, user.email, "plus", period)
                if link:
                    st.link_button(f"Upgrade to Plus ({prov.capitalize()})", link, use_container_width=True)
            if not providers:
                st.caption("Online Plus checkout is not enabled on this deployment yet; verify your `.ac.uk` student email on Account.")

    with c_pro:
        pro_p = price.get("pro", period)
        pro_save = f" · Save {price.annual_saving_percent('pro')}%" if period == "annual" else ""
        st.markdown(
            "<div class='pl-plan-card pl-plan-pro'>"
            "<div class='pl-popular-ribbon'>⭐ MOST POPULAR & FULL ACCESS</div>"
            f"<span class='pl-badge pl-pro'>PRO TIER{pro_save}</span>"
            f"<h4>{pro_p.label()}</h4>"
            "<p>Complete workspace, template pack, advanced track & AI coach.</p>"
            "<ul>"
            "<li><b>Everything in Plus</b>, plus:</li>"
            "<li>🔓 <b>Module 5 — Advanced Track</b>: multi-step chains, self-critique loops & reusable system prompts</li>"
            "<li>🗂️ <b>Personal Prompt Workspace</b>: save up to 500 custom prompts, tag, search & export to <b>Markdown</b> or <b>JSON</b></li>"
            "<li>📋 <b>8-Template Pack</b>: ready-to-copy templates for Study, Writing, STEM, Coding & Careers</li>"
            "<li>🤖 <b>AI Prompt Coach Feedback</b>: up to 30 AI reviews/month with multi-provider failover</li>"
            "<li>🏛️ <i>Also unlocked with access code <code>PMPPTL26!!</code></i></li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )
        if user is not None:
            providers = configured_providers("pro", period)
            for prov in providers:
                link = checkout_url(prov, user.id, user.email, "pro", period)
                if link:
                    st.link_button(f"Upgrade to Pro ({prov.capitalize()})", link, use_container_width=True)
            if not providers:
                st.caption("Online Pro checkout is not enabled on this deployment yet; use access code `PMPPTL26!!` below.")


def render_onboarding_and_auth_gate(key_prefix: str = "gate") -> None:
    """Render the onboarding walkthrough, login/registration forms, and plans overview for unauthenticated visitors."""
    import session
    from accounts import AccountError, email_delivery_enabled
    from entitlements import get_secret, verify_code

    svc = session.accounts()
    mail_live = email_delivery_enabled(svc.mailer)

    st.markdown(
        "<div class='pl-hero'>"
        "<h1>💡 Prompt Learning Platform</h1>"
        "<div class='pl-sub'>Structured AI prompt engineering, deterministic rubric grading, 100+ curated prompts & academic-integrity-safe study workflows.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # 1. Onboarding 3-Step Overview
    st.markdown("### 🚀 How the Platform Works")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>1. 🔍 Analyse & Discover</h4>"
            "<p>Test any prompt against our logical Python analyser for Clarity, Specificity, Context & Structure, and browse 100+ curated templates with academic-integrity notes.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>2. 🎯 Practice & Learn</h4>"
            "<p>Complete 10 realistic practice scenarios and 5 structured learning modules (15 graded exercises) with instant local feedback and saved account progress.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>3. 🚀 Build in Pro Workspace</h4>"
            "<p>Unlock Plus or Pro to access all premium prompts, Modules 2–5, your personal prompt workspace with Markdown/JSON export, the 8-template pack, and AI coaching.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 2. Sign In / Create Account / Access Code Gate
    st.markdown("### 🔐 Sign In or Create Your Account to Enter")
    st.caption("Sign in with your email and password, register a free account in seconds, or enter your email and access code (e.g. `PMPPTL26!!`).")

    tab_in, tab_up, tab_code = st.tabs(["🔑 Sign in", "✨ Create free account", "🎟️ Use an access code"])

    with tab_in:
        with st.form(f"{key_prefix}_login"):
            email = st.text_input("Email", key=f"{key_prefix}_login_email")
            password = st.text_input("Password", type="password", key=f"{key_prefix}_login_pw")
            if st.form_submit_button("Sign in to platform", type="primary", use_container_width=True):
                try:
                    _, token = svc.login(email, password)
                    session.sign_in(token)
                    st.rerun()
                except AccountError as exc:
                    st.error(str(exc))
        with st.expander("Forgot your password?"):
            if not mail_live:
                st.info("Email delivery is not configured on this deployment yet, so reset codes cannot be emailed.")
            else:
                with st.form(f"{key_prefix}_reset_request"):
                    r_email = st.text_input("Account email", key=f"{key_prefix}_reset_email")
                    if st.form_submit_button("Send reset code"):
                        svc.request_password_reset(r_email)
                        st.success("If that email has an account, a code is on its way.")
                with st.form(f"{key_prefix}_reset_do"):
                    r_code = st.text_input("Reset code", key=f"{key_prefix}_reset_code")
                    r_pw = st.text_input("New password", type="password", key=f"{key_prefix}_reset_pw")
                    if st.form_submit_button("Set new password"):
                        try:
                            svc.reset_password(r_email, r_code, r_pw)
                            st.success("Password changed. You can sign in now.")
                        except AccountError as exc:
                            st.error(str(exc))

    with tab_up:
        with st.form(f"{key_prefix}_register"):
            name = st.text_input("Name (optional)", key=f"{key_prefix}_reg_name")
            email = st.text_input("Email", key=f"{key_prefix}_reg_email")
            password = st.text_input("Password (10+ characters)", type="password", key=f"{key_prefix}_reg_pw")
            agreed = st.checkbox(
                "I agree to the Terms and Privacy Policy (see docs/TERMS.md and docs/PRIVACY.md)",
                key=f"{key_prefix}_reg_agreed",
            )
            if st.form_submit_button("Create account & enter platform", type="primary", use_container_width=True):
                if not agreed:
                    st.error("Please accept the Terms and Privacy Policy.")
                else:
                    try:
                        svc.register(email, password, name)
                        _, token = svc.login(email, password)
                        session.sign_in(token)
                        st.rerun()
                    except AccountError as exc:
                        st.error(str(exc))

    with tab_code:
        st.caption("Enter your email address and access code (e.g. `PMPPTL26!!` or voucher) to sign in and unlock full Pro access.")
        email_in = st.text_input(
            "Your email address (required to link account)",
            key=f"{key_prefix}_code_email",
            placeholder="you@example.com",
        )
        code_in = st.text_input(
            "Access code",
            type="password",
            key="access_code",
            placeholder="PMPPTL26!! or PL1....",
        )
        pw_in = st.text_input(
            "Password (10+ characters, optional if you have an account or set for a new account)",
            type="password",
            key=f"{key_prefix}_code_pw",
        )
        if st.button("Unlock with code", key=f"{key_prefix}_unlock_btn", type="primary"):
            clean_email = (email_in or "").strip().lower()
            found = verify_code(get_secret(), code_in, subject=clean_email)
            if not found:
                st.error("That code is not valid or has expired.")
            elif not clean_email and (not found.subject or "@" not in found.subject or found.subject == "member@kyrvynltd.co.uk"):
                st.error("Please enter a valid email address to link and unlock your access code.")
            else:
                target_email = clean_email if (clean_email and "@" in clean_email) else found.subject
                import secrets
                import uuid

                from accounts import (
                    SESSION_SECONDS,
                    TERMS_VERSION,
                    _token_hash,
                    hash_password,
                )

                now_i = int(time.time())
                row = svc.db.one("SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (target_email,))
                if row:
                    user_id = row[0]
                else:
                    user_id = uuid.uuid4().hex
                    chosen_pw = pw_in if (pw_in and len(pw_in) >= 10) else secrets.token_urlsafe(16)
                    svc.db.execute(
                        "INSERT INTO users (id, email, pw_hash, display_name, created_at, terms_accepted_at, terms_version) VALUES (?,?,?,?,?,?,?)",
                        (user_id, target_email, hash_password(chosen_pw), target_email.split("@")[0][:60], now_i, now_i, TERMS_VERSION),
                    )
                token = secrets.token_urlsafe(32)
                svc.db.execute(
                    "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?,?,?,?)",
                    (_token_hash(token), user_id, now_i, now_i + SESSION_SECONDS),
                )
                svc.db.commit()
                session.entitlements().grant(user_id, found.plan, found.expires_at)
                session.sign_in(token)
                st.session_state["entitlement"] = found
                st.success(f"Welcome, {target_email}! {found.plan.capitalize()} access unlocked.")
                st.rerun()
        st.caption("We never ask for card details on this page.")

    st.markdown("---")
    render_plans_comparison(user=None, key_prefix=f"{key_prefix}_plans")
    footer()


def render_status_bar() -> None:
    """Render a compact account & tier status bar at the top of the platform for authenticated users."""
    import session

    user = session.current_user()
    ent = session.current_entitlement()
    if user is None and ent is None:
        return
    tier = session.current_tier().upper()
    badge_cls = "pl-pro" if tier == "PRO" else ("pl-premium" if tier == "PLUS" else "pl-free")
    who = user.email if user else f"Access code ({ent.subject})" if ent else "Guest"
    c1, c2, c3 = st.columns([5, 3, 2])
    with c1:
        st.markdown(
            f"👤 **{who}** &nbsp;·&nbsp; Active Plan: <span class='pl-badge {badge_cls}'>{tier}</span>",
            unsafe_allow_html=True,
        )
    with c2:
        if tier == "FREE":
            st.caption("🔓 Upgrade to **Plus** or **Pro** on **Account & Plans** for full access.")
        elif ent:
            st.caption(f"✅ {tier.capitalize()} active ({session.days_left(ent)} days remaining).")
    with c3:
        if st.button("Sign out", key="top_bar_signout", use_container_width=True):
            session.sign_out()
            st.session_state.pop("entitlement", None)
            st.rerun()
    with st.expander("📊 View Plans & Functionalities (Free · Plus £4.99/m · Pro £9.99/m)"):
        render_plans_comparison(user=user, key_prefix="topbar_plans")


def setup(title: str, icon: str = "💡", require_auth: bool = True) -> None:
    sync_runtime_env()
    st.set_page_config(page_title=f"{title} | Prompt Learning Platform", page_icon=icon, layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    if require_auth:
        if "pytest" in sys.modules and os.getenv("ENFORCE_AUTH_IN_TEST") != "1":
            return
        import session
        if session.current_user() is None and session.current_entitlement() is None:
            render_onboarding_and_auth_gate(key_prefix=f"gate_{title.lower()}")
            st.stop()
        render_status_bar()


def header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='pl-hero'><h1>{title}</h1><div class='pl-sub'>{subtitle}</div></div>", unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        f"<div class='pl-footer'>{brand.copyright_line()} {brand.company_line()} "
        f"<a href='{brand.site_url()}'>{brand.site_url().split('//')[-1]}</a><br>"
        "AI can be wrong: verify facts and follow your institution's AI policy.</div>",
        unsafe_allow_html=True,
    )


def badge(access: str) -> str:
    cls = "pl-free" if access == "free" else "pl-premium"
    label = "Free" if access == "free" else "Premium"
    return f"<span class='pl-badge {cls}'>{label}</span>"
