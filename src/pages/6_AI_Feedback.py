"""Pro: AI feedback on a prompt, capped per month. Connects to OpenAI, Groq, Gemini, or OpenRouter."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ai_feedback  # noqa: E402
import session  # noqa: E402
import ui  # noqa: E402
from tiers import allows, feature_tier  # noqa: E402
from workspace import Workspace  # noqa: E402

ui.setup("AI Feedback", "🤖")
ui.header("🤖 AI Prompt Coach", "An expert coach evaluates your prompt, identifies hidden gaps, and generates a refined, publication-grade rewrite.")

user = session.current_user()
if user is None:
    st.info("Sign in on the Account page first.")
    st.stop()

need = feature_tier("ai_feedback")
if not allows(session.current_tier(), need):
    st.warning(f"AI feedback is part of {need.capitalize()}. Upgrade on the Account page or unlock with an access code to open it.")
    st.stop()

db = session._db()
is_live = ai_feedback.enabled()

# Header status card
col_stat1, col_stat2 = st.columns([3, 2])
with col_stat1:
    if is_live:
        st.markdown(
            f"**Status:** <span class='pl-badge' style='background:#e0f2fe;color:#0369a1;'>🟢 LIVE AI ACTIVE ({ai_feedback.active_model()})</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "**Status:** <span class='pl-badge' style='background:#fef3c7;color:#92400e;'>🟡 KEY PENDING / DEMO COACH ACTIVE</span>",
            unsafe_allow_html=True,
        )
with col_stat2:
    st.markdown(f"**Monthly Allowance:** `{ai_feedback.remaining(db, user.id)} / {ai_feedback.monthly_cap()}` reviews left this month")

# Expandable connection manager for API keys
with st.expander("⚡ Connect an AI Provider (Groq, OpenAI, Gemini, OpenRouter)", expanded=not is_live):
    st.markdown(
        "You can connect any OpenAI-compatible API key. "
        "Keys can be added permanently to **Streamlit Cloud Secrets** / `.env` (`AI_API_KEY=...`), or entered below for this session:"
    )
    c_prov, c_model = st.columns(2)
    with c_prov:
        prov = st.selectbox(
            "Provider",
            ["Groq (Fast & Free Key)", "OpenAI (GPT-4o-mini)", "Google Gemini (Free tier via OpenAI URL)", "OpenRouter", "Custom Endpoint"],
            key="ai_provider_select",
        )
    with c_model:
        if "Groq" in prov:
            default_url = "https://api.groq.com/openai/v1/chat/completions"
            default_mod = "llama-3.3-70b-versatile"
        elif "OpenAI" in prov:
            default_url = "https://api.openai.com/v1/chat/completions"
            default_mod = "gpt-4o-mini"
        elif "Gemini" in prov:
            default_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            default_mod = "gemini-1.5-flash"
        elif "OpenRouter" in prov:
            default_url = "https://openrouter.ai/api/v1/chat/completions"
            default_mod = "anthropic/claude-3.5-haiku"
        else:
            default_url = ai_feedback.active_api_url()
            default_mod = ai_feedback.active_model()
        model_input = st.text_input("Model ID", value=default_mod, key="ai_model_input")

    key_input = st.text_input("API Key", type="password", placeholder="gsk_... or sk-...", key="session_key_input")
    b_col1, b_col2 = st.columns([2, 3])
    with b_col1:
        if st.button("Connect & Save Key for Session", type="primary", use_container_width=True):
            if key_input.strip():
                st.session_state["user_ai_api_key"] = key_input.strip()
                st.session_state["user_ai_api_url"] = default_url
                st.session_state["user_ai_model"] = model_input.strip()
                st.success("API key connected successfully!")
                st.rerun()
            else:
                st.warning("Please enter an API key first.")
    with b_col2:
        if st.session_state.get("user_ai_api_key"):
            if st.button("Disconnect Session Key", use_container_width=True):
                st.session_state.pop("user_ai_api_key", None)
                st.session_state.pop("user_ai_api_url", None)
                st.session_state.pop("user_ai_model", None)
                st.rerun()

st.markdown("---")
st.markdown("### 📝 Enter Your Prompt for AI Critique")
st.caption(
    "Submit a draft prompt. The AI coach will evaluate it against the TRACE framework, "
    "identify hallucinations or vagueness risks, and produce an optimized rewrite."
)

sample_prompt = (
    "You are a biology tutor for a first-year undergraduate student. "
    "Explain cellular respiration and ATP synthesis. Limit to 300 words. "
    "Use a clear step-by-step table comparing glycolysis, the Krebs cycle, and oxidative phosphorylation. "
    "Do not include conversational filler or generic introductions. "
    "Include one checkable question at the end to test my comprehension."
)

c_sample, _ = st.columns([2, 3])
with c_sample:
    if st.button("📋 Load Example Academic Prompt"):
        st.session_state["target_ai_prompt"] = sample_prompt

text = st.text_area(
    "Your draft prompt",
    value=st.session_state.get("target_ai_prompt", ""),
    height=160,
    placeholder="Example: You are an academic advisor. Help me outline my literature review on AI ethics...",
    key="ai_coach_textarea",
)

col_run1, col_run2 = st.columns([2, 3])
with col_run1:
    run_btn = st.button("🚀 Get AI Coach Feedback", type="primary", use_container_width=True)

if run_btn:
    if not text.strip() or len(text.strip()) < 10:
        st.warning("Please enter a prompt of at least 10 characters.")
    else:
        with st.spinner("Analyzing prompt structure and consulting AI coach..."):
            if is_live:
                try:
                    result = ai_feedback.get_feedback(db, user.id, text)
                    st.success("✅ Live AI Review Generated!")
                    st.markdown("### 🧠 AI Coach Evaluation")
                    st.markdown(result)
                except ai_feedback.AIFeedbackError as exc:
                    st.error(str(exc))
            else:
                # High-value structured pedagogical engine
                critique = ai_feedback.get_pedagogical_coach_critique(text)
                st.info("💡 **Pedagogical Coach Analysis** (Connect a live API key above for dynamic LLM feedback):")

                c_w1, c_w2 = st.columns(2)
                with c_w1:
                    st.markdown("#### 🌟 What Works Well")
                    st.markdown(critique["strengths"])
                with c_w2:
                    st.markdown("#### ⚠️ Critical Gaps to Address")
                    st.markdown(critique["gaps"])

                st.markdown("#### 🚀 Engineered Production Rewrite (TRACE Framework)")
                st.code(critique["rewrite"], language=None)

                # Option to save directly to Workspace
                if st.button("💾 Save Rewrite to My Workspace"):
                    ws = Workspace(db)
                    ws.save(user.id, "AI Coach Engineered Rewrite", critique["rewrite"], "ai-coach, improved")
                    st.success("Saved to your Workspace!")

ui.footer()
