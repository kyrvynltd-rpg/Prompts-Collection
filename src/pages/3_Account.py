"""Enter a premium access code. Verification is local and fails closed."""
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ui  # noqa: E402
from entitlements import get_secret, verify_code  # noqa: E402

ui.setup("Account", "🔑")
ui.header("🔑 Premium access", "Free prompts and Practice mode are open to everyone. Premium Student Success prompts need an access code.")

ent = st.session_state.get("entitlement")
if ent and ent.is_active():
    days = max(0, int((ent.expires_at - time.time()) // 86400))
    st.success(f"Premium active ({ent.plan} plan). About {days} days left.")
    if st.button("Remove code from this session"):
        st.session_state.pop("entitlement", None)
        st.rerun()
else:
    code = st.text_input("Access code", type="password", key="access_code", placeholder="PL1....")
    if st.button("Unlock premium", type="primary", use_container_width=True):
        if not get_secret():
            st.error("Premium is not configured on this deployment yet.")
        else:
            found = verify_code(get_secret(), code)
            if found:
                st.session_state["entitlement"] = found
                st.rerun()
            else:
                st.error("That code is not valid or has expired.")
    st.caption("Codes come from your workshop leader or purchase confirmation. We never ask for card details on this page.")

ui.footer()
