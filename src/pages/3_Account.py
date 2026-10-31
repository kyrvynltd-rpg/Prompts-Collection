"""Account: sign up, sign in, student verification, upgrade, access code, and data controls."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import session  # noqa: E402
import ui  # noqa: E402
from accounts import AccountError, email_delivery_enabled  # noqa: E402
from billing import checkout_url, configured_providers  # noqa: E402
from entitlements import get_secret, verify_code  # noqa: E402
from pricing import get_pricing  # noqa: E402
from tiers import PRO_FEATURES  # noqa: E402

ui.setup("Account", "🔑")
ui.header("🔑 Account", "Free prompts and Practice are open to everyone. An account saves your progress and unlocks Premium.")

svc = session.accounts()
user = session.current_user()
price = get_pricing()
mail_live = email_delivery_enabled(svc.mailer)

if user is None:
    tab_in, tab_up = st.tabs(["Sign in", "Create account"])
    with tab_in:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
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
                with st.form("reset_request"):
                    r_email = st.text_input("Account email", key="reset_email")
                    if st.form_submit_button("Send reset code"):
                        svc.request_password_reset(r_email)
                        st.success("If that email has an account, a code is on its way.")
                with st.form("reset_do"):
                    r_code = st.text_input("Reset code")
                    r_pw = st.text_input("New password", type="password")
                    if st.form_submit_button("Set new password"):
                        try:
                            svc.reset_password(r_email, r_code, r_pw)
                            st.success("Password changed. You can sign in now.")
                        except AccountError as exc:
                            st.error(str(exc))
    with tab_up:
        with st.form("register"):
            name = st.text_input("Name (optional)")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password (10+ characters)", type="password", key="reg_pw")
            agreed = st.checkbox("I agree to the Terms and Privacy Policy (see docs/TERMS.md and docs/PRIVACY.md)")
            if st.form_submit_button("Create account", type="primary"):
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
else:
    st.success(f"Signed in as {user.email}")
    ent = session.current_entitlement()
    if ent:
        st.success(f"{session.current_tier().capitalize()} active. About {session.days_left(ent)} days left.")
    else:
        st.subheader("Choose a plan")
        period = st.radio("Billing", ["monthly", "annual"], horizontal=True, format_func=str.capitalize)
        cols = st.columns(2)
        for col, tier_name, blurb in ((cols[0], "plus", "All Premium prompts and modules, saved progress."),
                                      (cols[1], "pro", "Plus, and: " + "; ".join(PRO_FEATURES).lower() + ".")):
            with col:
                st.markdown(f"**{tier_name.capitalize()}**  \n{price.get(tier_name, period).label()}"
                            + (f" (save {price.annual_saving_percent(tier_name)}%)" if period == "annual" else ""))
                st.caption(blurb)
                providers = configured_providers(tier_name, period)
                for p in providers:
                    link = checkout_url(p, user.id, user.email, tier_name, period)
                    if link:
                        st.link_button(f"{tier_name.capitalize()} with {p.capitalize()}", link, use_container_width=True)
                if not providers:
                    st.caption("Online payment is not switched on yet.")
        st.caption("Free tier: free prompts, Practice and the first module. Cancel any time.")
        if not user.student_verified:
            st.info("Student? Verify your university email below to confirm you are eligible for student pricing.")

    if not svc.is_email_verified(user.id):
        if not mail_live:
            st.caption("Email confirmation is unavailable until an email provider is configured for this deployment.")
        else:
            with st.form("verify_email"):
                st.caption("Confirm your email: we sent a code when you signed up.")
                v_code = st.text_input("Email confirmation code")
                if st.form_submit_button("Confirm email"):
                    try:
                        svc.confirm_email(user.id, v_code)
                        st.rerun()
                    except AccountError as exc:
                        st.error(str(exc))

    st.subheader("Student verification")
    if user.student_verified:
        st.success(f"Verified student ({user.student_domain}).")
    elif not mail_live:
        st.info("Student email verification is unavailable until an email provider is configured for this deployment.")
    else:
        with st.form("student"):
            addr = st.text_input("University email (.ac.uk)")
            if st.form_submit_button("Send confirmation code"):
                try:
                    svc.start_student_verification(user.id, addr)
                    st.success("Code sent. Check your inbox.")
                except AccountError as exc:
                    st.error(str(exc))
        with st.form("student_code"):
            code = st.text_input("Confirmation code")
            if st.form_submit_button("Confirm"):
                try:
                    svc.confirm_student(user.id, code)
                    st.rerun()
                except AccountError as exc:
                    st.error(str(exc))

    with st.expander("Your data"):
        st.download_button("Download my data (JSON)", __import__("json").dumps(svc.export_data(user.id), indent=2),
                           file_name="my-data.json", mime="application/json")
        if st.checkbox("I understand deleting my account cannot be undone"):
            if st.button("Delete my account"):
                svc.delete_account(user.id)
                session.sign_out()
                st.rerun()
    if st.button("Sign out"):
        session.sign_out()
        st.rerun()

with st.expander("Have an access code (workshop or voucher)?"):
    code_in = st.text_input("Access code", type="password", key="access_code", placeholder="PL1....")
    if st.button("Unlock with code"):
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

ui.footer()
