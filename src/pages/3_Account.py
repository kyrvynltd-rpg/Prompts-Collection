"""Account & Plans: onboarding/sign-in gate, full Free/Plus/Pro comparison, student verification, access codes, and data controls."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import session  # noqa: E402
import ui  # noqa: E402
from accounts import AccountError, email_delivery_enabled  # noqa: E402
from entitlements import get_secret, verify_code  # noqa: E402

ui.setup("Account & Plans", "🔑", require_auth=False)

svc = session.accounts()
user = session.current_user()
ent = session.current_entitlement()
mail_live = email_delivery_enabled(svc.mailer)

if user is None and ent is None:
    ui.render_onboarding_and_auth_gate(key_prefix="account_gate")
    st.stop()

ui.header(
    "🔑 Account & Plans",
    "Manage your account, compare Free, Plus & Pro functionalities, verify student eligibility, or export your data.",
)

if user is not None:
    st.success(f"Signed in as **{user.email}**  ·  Active tier: **{session.current_tier().upper()}**")
elif ent is not None:
    st.success(f"Access code active (**{session.current_tier().upper()}**, about {session.days_left(ent)} days remaining).")

if ent is not None:
    st.info(f"✅ Your **{session.current_tier().capitalize()}** entitlement is active ({session.days_left(ent)} days left).")

# Always show the full 3-tier comparison & upgrade options so users can see every feature and tier
ui.render_plans_comparison(user=user, key_prefix="account_plans")

if user is not None and not user.student_verified:
    st.info("🎓 **Student?** Verify your university `.ac.uk` email below to confirm student status.")

if user is not None and not svc.is_email_verified(user.id):
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

if user is not None:
    st.subheader("🎓 Student verification")
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

with st.expander("🎟️ Have an access code (workshop or student voucher)?", expanded=(ent is None)):
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

if user is not None:
    with st.expander("🗂️ Your data & account controls (GDPR Export / Delete)"):
        st.download_button(
            "Download my data (JSON)",
            json.dumps(svc.export_data(user.id), indent=2),
            file_name="my-data.json",
            mime="application/json",
        )
        if st.checkbox("I understand deleting my account cannot be undone"):
            if st.button("Delete my account"):
                svc.delete_account(user.id)
                session.sign_out()
                st.rerun()
    if st.button("Sign out"):
        session.sign_out()
        st.session_state.pop("entitlement", None)
        st.rerun()

ui.footer()
