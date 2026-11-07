"""Streamlit Prompts Collection Platform
A platform for improving AI prompts based on best practices
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

import ai_feedback
import session
import ui
from analysis import (
    analyze_prompt,
    recommend_prompts,
)
from prompt_loader import get_all_prompts, get_category_folders

# Page configuration
BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo.svg"

st.set_page_config(
    page_title="Prompt Learning Platform",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "💡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for better styling
ui.sync_runtime_env()
st.markdown(ui.CSS, unsafe_allow_html=True)


# Load all example prompts
@st.cache_data
def load_example_prompts():
    """Load all example prompts for analysis"""
    return get_all_prompts()


@st.cache_data
def get_logo_data_uri():
    """Return logo as data URI so it can be centered with deterministic HTML/CSS."""
    if not LOGO_PATH.exists():
        return None
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def render_centered_logo(width_px=96):
    """Render the logo fully centered regardless of Streamlit widget layout behavior."""
    logo_uri = get_logo_data_uri()
    if not logo_uri:
        return
    st.markdown(
        f'<div style="text-align:center;margin:0.5rem auto 1rem auto;"><img src="{logo_uri}" alt="Prompt Learning Platform logo" width="{width_px}" /></div>',
        unsafe_allow_html=True,
    )


# Initialize session state
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "last_analyzed" not in st.session_state:
    st.session_state.last_analyzed = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "last_recommendation_query" not in st.session_state:
    st.session_state.last_recommendation_query = ""
if "last_recommendation_filters" not in st.session_state:
    st.session_state.last_recommendation_filters = {}

# Enforce onboarding / login gate for unauthenticated visitors
if session.current_user() is None and session.current_entitlement() is None:
    render_centered_logo(92)
    ui.render_onboarding_and_auth_gate(key_prefix="home_gate")
    st.stop()

ui.render_status_bar()

# Sidebar for navigation and settings
with st.sidebar:
    st.title("Settings & Info")

    # Dark mode toggle
    dark_mode = st.checkbox("Dark Mode", value=False)
    if dark_mode:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # Export/Import favorites
    st.header("Manage Favorites")
    if st.session_state.favorites:
        favorites_text = "\n\n".join(
            [f"Title: {f['title']}\nCategory: {f['category']}\nPrompt: {f['prompt']}" for f in st.session_state.favorites]
        )
        st.download_button("Export Favorites", favorites_text, file_name="favorite_prompts.txt", mime="text/plain")

    st.divider()

    # Intelligent Recommendations Section
    st.header("🎯 Prompt Matcher")
    st.caption("Tell us what you want to achieve and get matching prompts")

    rec_intent = st.text_input("Your goal / task", placeholder="e.g., summarize lecture notes, review code")

    all_prompts = load_example_prompts()
    all_difficulties = sorted(list(set(p.get("difficulty_level", "intermediate") for p in all_prompts)))
    all_formats = sorted(list(set(p.get("output_format", "text") for p in all_prompts)))

    col_d, col_f = st.columns(2)
    with col_d:
        rec_diff = st.selectbox("Difficulty", ["Any"] + all_difficulties)
    with col_f:
        rec_format = st.selectbox("Format", ["Any"] + all_formats)

    rec_time = st.select_slider("Available time", options=["Any", "quick", "moderate", "deep"], value="Any")

    if st.button("Find Matching Prompts", use_container_width=True):
        filters = {}
        if rec_diff != "Any":
            filters["difficulty_level"] = rec_diff
        if rec_format != "Any":
            filters["output_format"] = rec_format
        if rec_time != "Any":
            filters["time_estimate"] = rec_time

        recs = recommend_prompts(
            query=rec_intent,
            all_prompts=all_prompts,
            user_filters=filters if filters else None,
            user_history=[f["title"] for f in st.session_state.favorites],
            top_k=3,
        )
        st.session_state.recommendations = recs
        st.session_state.last_recommendation_query = rec_intent
        st.session_state.last_recommendation_filters = filters
        st.rerun()

    st.divider()

    # Search and Filter
    st.header("🔍 Search & Filter")

    # Search
    search_query = st.text_input("Search prompts", placeholder="Type keywords, tags, or titles...")

    # Category filter
    category_folders = get_category_folders()
    categories = ["All Categories"] + sorted(category_folders)
    selected_category = st.selectbox("Filter by Category", categories)

    # Tag filter
    all_tags = set()
    for prompt in all_prompts:
        all_tags.update(prompt.get("tags", []))
    all_tags = sorted(list(all_tags))

    selected_tags = st.multiselect("Filter by Tags", all_tags)

    st.divider()

    # Favorites section
    st.header("⭐ Favorites")
    if st.session_state.favorites:
        for i, fav in enumerate(st.session_state.favorites):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{fav['title']}**")
                st.caption(f"{fav['category']}")
            with col2:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.favorites.remove(fav)
                    st.rerun()
    else:
        st.info("No favorites yet. Click ⭐ on any prompt to add it!")

    st.divider()

    # About section
    st.header("ℹ️ About")
    st.info("""
    Enter your prompt in the main area and get improvement
    recommendations based on our curated prompt collection
    and logical Python analysis.
    """)

# Main content area
render_centered_logo(80)
ui.render_neural_hero(
    "KYRVYN PROMPT STUDIO",
    "Engineer publication-grade AI prompts with TRACE heuristics, multi-model neural cascades & dynamic optimization.",
    badge="🟢 KYRVYN NEURAL ENGINE v4.2 · ACTIVE · 3 MODELS ONLINE",
)


def _safe_page_link(col, path: str, label: str) -> None:
    try:
        col.page_link(path, label=label, use_container_width=True)
    except Exception:
        try:
            col.page_link(f"src/{path}", label=label, use_container_width=True)
        except Exception:
            col.button(label, use_container_width=True)


# Executive Studio Hub Grid
_c1, _c2, _c3 = st.columns(3)
with _c1:
    st.markdown(
        "<div class='pl-hub-card'>"
        "<div class='pl-hub-title'>🎯 Practice Arena</div>"
        "<div class='pl-hub-desc'>10 realistic student challenges with instant TRACE heuristic grading.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _safe_page_link(_c1, "pages/1_Practice.py", "Launch Arena ➔")

with _c2:
    st.markdown(
        "<div class='pl-hub-card'>"
        "<div class='pl-hub-title'>📚 Prompt Vault</div>"
        "<div class='pl-hub-desc'>100+ curated prompts, few-shot patterns & academic integrity guides.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _safe_page_link(_c2, "pages/2_Library.py", "Browse Vault ➔")

with _c3:
    st.markdown(
        "<div class='pl-hub-card'>"
        "<div class='pl-hub-title'>🤖 Neural AI Coach</div>"
        "<div class='pl-hub-desc'>Multi-model automated failover cascade (Groq ➔ OpenAI ➔ Gemini).</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _safe_page_link(_c3, "pages/6_AI_Feedback.py", "Open AI Coach ➔")

_c4, _c5, _c6 = st.columns(3)
with _c4:
    st.markdown(
        "<div class='pl-hub-card'>"
        "<div class='pl-hub-title'>🎓 Learn Curriculum</div>"
        "<div class='pl-hub-desc'>5 structured modules from foundational directives to advanced system prompts.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _safe_page_link(_c4, "pages/4_Learn.py", "Start Curriculum ➔")

with _c5:
    st.markdown(
        "<div class='pl-hub-card'>"
        "<div class='pl-hub-title'>🗂️ Pro Workspace</div>"
        "<div class='pl-hub-desc'>Personal prompt library, tag filtering, templates & instant export.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _safe_page_link(_c5, "pages/5_Workspace.py", "Open Workspace ➔")

with _c6:
    st.markdown(
        "<div class='pl-hub-card'>"
        "<div class='pl-hub-title'>🔑 Account & Plans</div>"
        "<div class='pl-hub-desc'>Manage Pro tier, redeem institutional vouchers & export GDPR data.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _safe_page_link(_c6, "pages/3_Account.py", "View Account ➔")

st.markdown("---")

if st.session_state.recommendations:
    st.markdown("### 🧠 Intelligent Recommendations")
    query_label = st.session_state.last_recommendation_query or "(filter-only recommendation)"
    st.caption(f"Query: {query_label}")

    for i, rec in enumerate(st.session_state.recommendations, 1):
        prompt = rec["prompt"]
        score_pct = int(rec["score"] * 100)
        title = prompt.get("title", "Untitled")
        category = prompt.get("category", "Unknown")
        difficulty = prompt.get("difficulty_level", "intermediate")
        time_est = prompt.get("time_estimate", "moderate")
        output_fmt = prompt.get("output_format", "text")

        with st.expander(f"{i}. {title} ({score_pct}% match)", expanded=(i == 1)):
            st.markdown(f"**Category:** {category}")
            st.markdown(f"**Profile:** {difficulty} | {time_est} | {output_fmt}")
            st.markdown(f"**Why this was selected:** {', '.join(rec['reasons'])}")
            st.markdown(f"**Description:** {prompt.get('description', '')}")
            st.code(prompt.get("prompt", ""), language=None)

    st.divider()

# Main input area - Studio Workbench
st.markdown("### 📝 Prompt Engineering Workbench")
st.caption("Apply 1-click architectural modifiers, detect dynamic `{variables}`, or analyze against publication-grade TRACE standards.")

# 🧪 One-Click Showcase Prompts
st.markdown("<div style='font-size:0.82rem;font-weight:750;letter-spacing:0.05em;color:var(--pl-muted);text-transform:uppercase;margin-bottom:0.35rem;'>⚡ Load Tested Industry Showcase Prompts:</div>", unsafe_allow_html=True)
d1, d2, d3, d4 = st.columns(4)
if d1.button("🔬 Literature Review", use_container_width=True, help="Load academic systematic review prompt"):
    st.session_state["prompt_input"] = (
        "You are an academic research mentor. Review my literature review on renewable energy microgrids in 200 words. "
        "Format as a structured markdown table with columns: Research Stage, Methodological Risk, Recommended Mitigation. "
        "Do not include conversational preamble. Verify citations and follow peer-reviewed rigor."
    )
    st.rerun()
if d2.button("💻 Python Architecture", use_container_width=True, help="Load software architecture prompt"):
    st.session_state["prompt_input"] = (
        "You are a Principal Software Architect. Design an asynchronous event-driven pipeline in Python using asyncio and PostgreSQL. "
        "Specify data contracts, error-handling retry strategies with exponential backoff, and idempotency guarantees. "
        "Output code strictly as tested snippets."
    )
    st.rerun()
if d3.button("📊 Executive Strategy", use_container_width=True, help="Load financial & SaaS metrics prompt"):
    st.session_state["prompt_input"] = (
        "You are a CFO and strategic advisor. Analyze this Q3 SaaS metrics report for Kyrvyn Ltd. "
        "Highlight CAC payback velocity, Net Revenue Retention (NRR), and runway sensitivity under a 15% churn stress test. "
        "Provide 3 prioritized executive action items."
    )
    st.rerun()
if d4.button("🛡️ AI Security Guardrails", use_container_width=True, help="Load prompt security audit"):
    st.session_state["prompt_input"] = (
        "You are an AI Security and Red-Teaming Specialist. Audit this user-facing customer service prompt for prompt injection vulnerabilities, "
        "data leakage vectors, and jailbreak susceptibility. Provide a hardened system prompt with explicit negative constraints."
    )
    st.rerun()

# Quick Action Modifier Pills
m1, m2, m3, m4 = st.columns(4)
curr_p = st.session_state.get("prompt_input", "")
if m1.button("⚡ Make Concise", use_container_width=True, help="Eliminate fluff & conversational preamble"):
    if curr_p:
        st.session_state["prompt_input"] = ui.apply_modifier(curr_p, "concise")
        st.rerun()
if m2.button("🧠 Chain-of-Thought", use_container_width=True, help="Inject step-by-step reasoning scaffold"):
    if curr_p:
        st.session_state["prompt_input"] = ui.apply_modifier(curr_p, "cot")
        st.rerun()
if m3.button("🎯 JSON Schema", use_container_width=True, help="Enforce strict structured output"):
    if curr_p:
        st.session_state["prompt_input"] = ui.apply_modifier(curr_p, "json")
        st.rerun()
if m4.button("🛡️ Guardrails", use_container_width=True, help="Prevent hallucinations & verify facts"):
    if curr_p:
        st.session_state["prompt_input"] = ui.apply_modifier(curr_p, "guardrails")
        st.rerun()

# Dynamic Variable Extraction
if curr_p:
    detected_vars = ui.extract_variables(curr_p)
    if detected_vars:
        with st.expander(f"🧩 Dynamic Variables Detected ({len(detected_vars)})", expanded=True):
            st.caption("Fill in variables to live-preview your interpolated prompt:")
            var_cols = st.columns(min(len(detected_vars), 3))
            var_map = {}
            for idx, v_name in enumerate(detected_vars):
                with var_cols[idx % len(var_cols)]:
                    var_map[v_name] = st.text_input(f"{{{v_name}}}", key=f"var_chip_{v_name}")
            if any(var_map.values()):
                rendered_preview = curr_p
                for vk, vv in var_map.items():
                    if vv:
                        rendered_preview = rendered_preview.replace(f"{{{vk}}}", vv)
                st.markdown("**Live Interpolated Prompt:**")
                st.code(rendered_preview, language=None)

with st.form("analyze_form", clear_on_submit=False):
    user_prompt = st.text_area(
        "Type or paste your prompt here",
        placeholder="Example: You are an academic writing mentor. Review this draft literature review outline on renewable energy policy...",
        height=150,
        key="prompt_input",
        label_visibility="collapsed",
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.form_submit_button("🔍 Analyze & Improve Prompt", type="primary", use_container_width=True)

# Process analysis
if analyze_button and user_prompt.strip():
    with st.spinner("Analyzing your prompt and comparing with our collection..."):
        example_prompts = load_example_prompts()
        recommendations, improved_suggestion, best_practices, similar_examples = analyze_prompt(
            user_prompt, example_prompts
        )
        st.session_state.last_analyzed = {
            "original": user_prompt,
            "recommendations": recommendations,
            "improved": improved_suggestion,
            "best_practices": best_practices,
            "similar_examples": similar_examples,
        }
        st.rerun()

# Display results if available
if st.session_state.last_analyzed:
    analysis = st.session_state.last_analyzed

    st.divider()
    st.markdown("### 📊 Analysis Results")

    # Interactive Circular Health Gauge & Telemetry
    practices_count = sum(analysis["best_practices"].values())
    total_practices = len(analysis["best_practices"])
    score = (practices_count / total_practices) * 100
    word_count = len(analysis["original"].split())

    if score >= 80:
        ui.render_confetti()
    ui.render_health_gauge(score, analysis["best_practices"])

    c_meta1, c_meta2, c_meta3 = st.columns(3)
    with c_meta1:
        st.metric("Token / Word Count", f"{word_count} words", "Optimal: 20-50 words" if word_count < 20 or word_count > 50 else "✓ Balanced")
    with c_meta2:
        st.metric("Identified Recommendations", len(analysis["recommendations"]))
    with c_meta3:
        st.metric("TRACE Dimension Score", f"{practices_count}/{total_practices} Passed")

    # Display recommendations using Streamlit native components
    if analysis["recommendations"]:
        st.markdown("### 💡 Recommendations for Improvement")
        for i, rec in enumerate(analysis["recommendations"], 1):
            priority_icon = "🔴" if rec.get("priority") == "high" else "🟡" if rec.get("priority") == "medium" else "🟢"
            with st.expander(f"{priority_icon} {i}. {rec['title']}", expanded=(rec.get("priority") == "high")):
                st.markdown(f"**{rec['description']}**")
                if "suggestion" in rec:
                    st.info(f"💡 {rec['suggestion']}")
                if rec.get("similar_example"):
                    st.markdown("**Similar example from our collection:**")
                    st.code(rec["similar_example"], language=None)
    else:
        st.success("🎉 Great job! Your prompt follows best practices. No major improvements needed.")

    # Display improved suggestion with Visual Diff and Code
    st.divider()
    st.markdown("### ✨ Engineered Prompt Comparison & Visual Diff")

    diff_tab, code_tab = st.tabs(["✨ Visual Delta (Color Diff)", "📋 Engineered Prompt (Code)"])
    with diff_tab:
        st.caption("Color-coded changes: <span class='pl-diff-add'>green additions</span> and <span class='pl-diff-del'>red removals</span>.", unsafe_allow_html=True)
        ui.render_diff_view(analysis["original"], analysis["improved"])
    with code_tab:
        st.code(analysis["improved"], language=None)

    # AI Coach Deep Review & Production Rewrite
    st.divider()
    st.markdown("### 🤖 AI Prompt Coach Deep Review & Rewrite")
    st.caption(
        "Generate a structured academic critique (Strengths, Critical Gaps, and Engineered TRACE Rewrite) for this prompt."
    )

    c_ai1, c_ai2 = st.columns([2, 3])
    with c_ai1:
        request_ai = st.button(
            "✨ Consult AI Prompt Coach", type="secondary", key="home_consult_ai_btn", use_container_width=True
        )

    cache_key = f"ai_coach_{hash(analysis['original'])}"
    if request_ai or st.session_state.get(cache_key):
        st.session_state[cache_key] = True
        with st.spinner("Consulting AI coach..."):
            if ai_feedback.enabled():
                try:
                    user_ref = session.current_user().id if session.current_user() else "guest"
                    ai_text = ai_feedback.get_feedback(session._db(), user_ref, analysis["original"])
                    st.success("✅ AI Coach Review (Live API):")
                    st.markdown(ai_text)
                except Exception as exc:
                    st.warning(f"Live provider note: {exc}. Showing pedagogical analysis:")
                    c_data = ai_feedback.get_pedagogical_coach_critique(analysis["original"])
                    st.markdown(
                        f"**🌟 Strengths:**\n{c_data['strengths']}\n\n**⚠️ Gaps:**\n{c_data['gaps']}\n\n**🚀 Production Rewrite:**\n```\n{c_data['rewrite']}\n```"
                    )
            else:
                c_data = ai_feedback.get_pedagogical_coach_critique(analysis["original"])
                st.info(
                    "💡 **AI Coach Analysis & Refinement** (Connect an API key in AI Feedback for dynamic LLM responses):"
                )
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown("#### 🌟 Strengths")
                    st.markdown(c_data["strengths"])
                with col_s2:
                    st.markdown("#### ⚠️ Critical Gaps")
                    st.markdown(c_data["gaps"])
                st.markdown("#### 🚀 Engineered Production Rewrite")
                st.code(c_data["rewrite"], language=None)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copy Improved Prompt", use_container_width=True):
            st.code(analysis["improved"], language=None)
            st.success("✅ Select and copy the prompt above (Ctrl+C)")
    with col2:
        if st.button("🔄 Analyze Again", use_container_width=True):
            st.session_state.last_analyzed = None
            st.rerun()

    # Show original for comparison
    with st.expander("📝 View Original Prompt"):
        st.code(analysis["original"], language=None)

    # Show similar examples if available
    if analysis.get("similar_examples"):
        st.divider()
        st.markdown("### 📚 Similar Prompts from Our Collection")
        for ex in analysis["similar_examples"][:3]:
            with st.expander(f"📄 {ex.get('title', 'Example Prompt')} ({ex.get('category', 'Unknown')})"):
                st.markdown(f"**Tags:** {', '.join(ex.get('tags', []))}")
                st.code(ex.get("prompt", ""), language=None)

# Footer
ui.footer()
