"""Shared look and feel: responsive CSS, onboarding/login gate, plan comparison, header and footer."""
import os
import sys
from pathlib import Path

import streamlit as st

import brand

CSS = """
<style>
.block-container { max-width: 1000px; padding-top: 1.5rem; }
.pl-hero h1 { margin-bottom: .2rem; }
.pl-sub { color: #6b7280; margin-bottom: 1.2rem; }
.pl-badge { display:inline-block; padding: .15rem .6rem; border-radius: 999px; font-size: .75rem; font-weight: 600; }
.pl-free { background:#e8f5ec; color:#146c2e; }
.pl-premium { background:#fff3d6; color:#8a5a00; }
.pl-pro { background:#ede9fe; color:#5b21b6; }
.pl-card { border:1px solid rgba(128,128,128,.25); border-radius:12px; padding:1rem 1.1rem; margin-bottom:.8rem; height: 100%; }
.pl-plan-card { border:1px solid rgba(128,128,128,.3); border-radius:14px; padding:1.1rem 1.2rem; margin-bottom:.8rem; background: rgba(128,128,128,.04); }
.pl-plan-pro { border:2px solid #4f46e5; background: rgba(79,70,229,.05); }
.pl-weak { border-left: 4px solid #d9534f; padding:.5rem .8rem; background: rgba(217,83,79,.08); border-radius:6px; }
.pl-footer { text-align:center; color:#6b7280; font-size:.8rem; padding:1.5rem 0 .5rem; }
@media (max-width: 640px) {
  .block-container { padding: 1rem .8rem; }
  .pl-hero h1 { font-size: 1.5rem; }
  div[data-testid="stMetricValue"] { font-size: 1.4rem; }
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
        "Every account starts on the Free tier. Upgrade to **Plus** or **Pro** (or use a verified Student / Workshop access code) "
        "to unlock premium prompt collections, advanced learning modules, the personal workspace, and AI coaching."
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
            "<h4 style='margin:0.4rem 0 0.2rem 0;'>£0 <small style='font-weight:normal;color:#6b7280;'>/ forever</small></h4>"
            "<p style='font-size:0.88rem;color:#6b7280;margin-bottom:0.6rem;'>Core prompt analysis & foundational practice with an account.</p>"
            "<ul style='font-size:0.88rem;padding-left:1.1rem;line-height:1.55;'>"
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
            f"<h4 style='margin:0.4rem 0 0.2rem 0;'>{plus_p.label()}</h4>"
            "<p style='font-size:0.88rem;color:#6b7280;margin-bottom:0.6rem;'>Full prompt library & core curriculum for regular study.</p>"
            "<ul style='font-size:0.88rem;padding-left:1.1rem;line-height:1.55;'>"
            "<li><b>Everything in Free</b>, plus:</li>"
            "<li>🔓 <b>Full 100+ Premium Prompt Library</b> across all categories & the complete Student Success pack</li>"
            "<li>🔓 <b>Module 2 — Precision</b>: constraints, output formats & few-shot examples (3 graded exercises)</li>"
            "<li>🔓 <b>Module 3 — Rigour</b>: checkable, honest & academic-integrity-safe prompting (3 graded exercises)</li>"
            "<li>🔓 <b>Module 4 — Applied</b>: study, revision, career & project workflows (3 graded exercises)</li>"
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
                st.caption("Online Plus checkout is not enabled on this deployment yet; use an access code below.")

    with c_pro:
        pro_p = price.get("pro", period)
        pro_save = f" · Save {price.annual_saving_percent('pro')}%" if period == "annual" else ""
        st.markdown(
            "<div class='pl-plan-card pl-plan-pro'>"
            f"<span class='pl-badge pl-pro'>PRO TIER{pro_save}</span>"
            f"<h4 style='margin:0.4rem 0 0.2rem 0;'>{pro_p.label()}</h4>"
            "<p style='font-size:0.88rem;color:#6b7280;margin-bottom:0.6rem;'>Complete workspace, template pack, advanced track & AI coach.</p>"
            "<ul style='font-size:0.88rem;padding-left:1.1rem;line-height:1.55;'>"
            "<li><b>Everything in Plus</b>, plus:</li>"
            "<li>🔓 <b>Module 5 — Advanced Track</b>: multi-step prompt chains, self-critique loops & reusable system prompts</li>"
            "<li>🗂️ <b>Personal Prompt Workspace</b>: save up to 500 custom prompts, tag, search & export to <b>Markdown</b> or <b>JSON</b></li>"
            "<li>📋 <b>8-Template Pack</b>: ready-to-copy templates for Study, Writing, STEM, Coding & Careers</li>"
            "<li>🤖 <b>AI Prompt Coach Feedback</b>: up to 30 AI prompt reviews/month (when enabled by operator)</li>"
            "<li>🏛️ <i>Also unlocked via Workshop / Institutional access codes</i></li>"
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
                st.caption("Online Pro checkout is not enabled on this deployment yet; use a workshop access code below.")


def render_onboarding_and_auth_gate(key_prefix: str = "gate") -> None:
    """Render the onboarding walkthrough, login/registration forms, and plans overview for unauthenticated visitors."""
    import session
    from accounts import AccountError, email_delivery_enabled
    from entitlements import get_secret, verify_code

    svc = session.accounts()
    mail_live = email_delivery_enabled(svc.mailer)

    st.markdown(
        "<div class='pl-hero' style='text-align:center;'>"
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
            "<h4>1. Analyse & Discover</h4>"
            "<p style='font-size:0.9rem;color:#6b7280;'>Test any prompt against our logical Python analyser for Clarity, Specificity, Context & Structure, and browse 100+ curated templates with academic-integrity notes.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>2. Practice & Learn</h4>"
            "<p style='font-size:0.9rem;color:#6b7280;'>Complete 10 realistic practice scenarios and 5 structured learning modules (15 graded exercises) with instant local feedback and saved account progress.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>3. Build in Pro Workspace</h4>"
            "<p style='font-size:0.9rem;color:#6b7280;'>Unlock Plus or Pro to access all premium prompts, Modules 2–5, your personal prompt workspace with Markdown/JSON export, the 8-template pack, and AI coaching.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 2. Sign In / Create Account / Access Code Gate
    st.markdown("### 🔐 Sign In or Create Your Account to Enter")
    st.caption("Sign in with your account, register a free account in seconds, or unlock directly with a workshop/student access code.")

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
        st.caption("Have a signed workshop (`Pro`) or student (`Plus`) voucher code? Enter it below to unlock access.")
        code_in = st.text_input(
            "Access code",
            type="password",
            key="access_code",
            placeholder="PL1....",
        )
        if st.button("Unlock with code", key=f"{key_prefix}_unlock_btn", type="primary"):
            if not get_secret():
                st.error("Access codes are not configured on this deployment yet.")
            else:
                found = verify_code(get_secret(), code_in)
                if found:
                    st.session_state["entitlement"] = found
                    st.rerun()
                else:
                    st.error("That code is not valid or has expired.")
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
