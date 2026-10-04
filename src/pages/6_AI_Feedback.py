"""Pro: AI feedback on a prompt, capped per month. Off until the operator sets an API key."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ai_feedback  # noqa: E402
import session  # noqa: E402
import ui  # noqa: E402
from tiers import allows  # noqa: E402

ui.setup("AI feedback", "🤖")
ui.header("🤖 AI feedback", "A coach reviews your prompt. Pro feature with a monthly allowance.")

user = session.current_user()
if user is None:
    st.info("Sign in on the Account page first.")
    st.stop()
if not allows(session.current_tier(), "pro"):
    st.warning("AI feedback is part of Pro. See plans on the Account page.")
    st.stop()
if not ai_feedback.enabled():
    st.info("AI feedback is not switched on for this deployment yet.")
    st.stop()

db = session._db()
st.caption(f"{ai_feedback.remaining(db, user.id)} of {ai_feedback.monthly_cap()} reviews left this month. "
           "Your prompt text is sent to an AI provider to produce the feedback. Do not paste personal data.")
text = st.text_area("Your prompt", height=160)
if st.button("Get feedback", type="primary"):
    try:
        with st.spinner("Reviewing..."):
            st.markdown(ai_feedback.get_feedback(db, user.id, text))
    except ai_feedback.AIFeedbackError as exc:
        st.error(str(exc))
ui.footer()
