"""
Streamlit Prompts Collection Platform
A platform for improving AI prompts based on best practices
"""

import base64
from pathlib import Path

import streamlit as st

import ai_feedback
import brand
import session
import ui
from prompt_loader import get_all_prompts, get_category_folders

# Page configuration
BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo.svg"

st.set_page_config(
    page_title="Prompt Learning Platform",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
ui.sync_runtime_env()
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .center-shell {
        max-width: 980px;
        margin: 0 auto;
    }
    .brand-block {
        text-align: center;
    }
    .prompt-title {
        text-align: center;
        margin-bottom: 0.75rem;
    }
    .welcome-wrap {
        max-width: 820px;
        margin: 0 auto;
        text-align: center;
    }
    .logo-center {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto 0.9rem auto;
    }
    .logo-center img {
        display: block;
        margin: 0 auto;
    }
    .welcome-lead {
        font-size: 1.05rem;
        color: #7b8794;
        margin-bottom: 1rem;
    }
    .welcome-list {
        display: inline-block;
        margin: 0.75rem auto 1rem auto;
        text-align: left;
        max-width: 700px;
        color: #b8c2cc;
        line-height: 1.6;
        padding-left: 1.1rem;
    }
    .welcome-note {
        color: #93a1b0;
        margin-top: 0.8rem;
    }
    .pulse {
        display: inline-block;
        animation: pulse 1.4s ease-in-out infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.45; }
        50% { opacity: 1; }
        100% { opacity: 0.45; }
    }
    @media (max-width: 640px) {
        .block-container { padding: 1rem 0.8rem; }
        .main-header { font-size: 1.75rem; }
        .sub-header { font-size: 0.95rem; margin-bottom: 1.25rem; }
    }
    </style>
""", unsafe_allow_html=True)

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
        f'<div class="logo-center"><img src="{logo_uri}" alt="Prompt Learning Platform logo" width="{width_px}" /></div>',
        unsafe_allow_html=True,
    )

# (The timed splash screen was removed: it delayed every visit by 7 seconds.)

# Initialize session state
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'last_analyzed' not in st.session_state:
    st.session_state.last_analyzed = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'last_recommendation_query' not in st.session_state:
    st.session_state.last_recommendation_query = ""
if 'last_recommendation_filters' not in st.session_state:
    st.session_state.last_recommendation_filters = {}

from analysis import (  # noqa: E402
    analyze_prompt,
    build_learning_paths,
    recommend_prompts,
)

if session.current_user() is None and session.current_entitlement() is None:
    render_centered_logo(92)
    ui.render_onboarding_and_auth_gate(key_prefix="home_gate")
    st.stop()

ui.render_status_bar()

# Sidebar (keeping as requested)
with st.sidebar:
    st.header("🎯 Smart Discovery")

    all_prompts = load_example_prompts()
    recommendation_query = st.text_area(
        "What do you need right now?",
        placeholder="Example: I need a quick prompt to analyze customer churn trends and produce actionable recommendations.",
        height=90,
        key="recommendation_query"
    )

    rec_col1, rec_col2 = st.columns(2)
    with rec_col1:
        rec_difficulty = st.selectbox("Difficulty", ["Any", "beginner", "intermediate", "expert"], key="rec_difficulty")
    with rec_col2:
        rec_time = st.selectbox("Time", ["Any", "quick", "moderate", "thorough"], key="rec_time")
    rec_output = st.selectbox("Output format", ["Any", "text", "markdown", "code", "json", "structured"], key="rec_output")

    if st.button("🎯 Recommend Best Prompts", type="primary", use_container_width=True):
        filters = {
            'difficulty': rec_difficulty,
            'time': rec_time,
            'output_format': rec_output,
        }
        st.session_state.recommendations = recommend_prompts(recommendation_query.strip(), all_prompts, filters)
        st.session_state.last_recommendation_query = recommendation_query.strip()
        st.session_state.last_recommendation_filters = filters

    paths = build_learning_paths(all_prompts)
    selected_path_category = st.selectbox("Learning path", ["None"] + sorted(paths.keys()), key="learning_path_category")
    if selected_path_category != "None" and selected_path_category in paths:
        st.caption(f"Suggested progression in {selected_path_category}")
        for i, prompt in enumerate(paths[selected_path_category][:4], 1):
            level = prompt.get('difficulty_level', 'intermediate')
            st.write(f"{i}. {prompt.get('title', 'Untitled')} ({level})")

    st.divider()

    st.header("🔍 Search & Filter")

    # Search
    search_query = st.text_input("Search prompts", placeholder="Type keywords, tags, or titles...")

    # Category filter
    category_folders = get_category_folders()
    categories = ["All Categories"] + sorted(category_folders)
    selected_category = st.selectbox("Filter by Category", categories)

    # Load prompts for sidebar

    # Tag filter
    all_tags = set()
    for prompt in all_prompts:
        all_tags.update(prompt.get('tags', []))
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
st.markdown('<div class="center-shell">', unsafe_allow_html=True)
st.markdown('<div class="brand-block">', unsafe_allow_html=True)
render_centered_logo(92)
st.markdown('<div class="main-header">Prompt Learning Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Make your prompts better using our collection and logical Python analysis</div>', unsafe_allow_html=True)

def _page_ref(rel: str) -> str:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    main_script = getattr(ctx, "main_script_path", "") if ctx else ""
    return f"src/{rel}" if Path(main_script).name == "main.py" else rel

_nav1, _nav2, _nav3 = st.columns(3)
_nav1.page_link(_page_ref("pages/1_Practice.py"), label="🎯 Practice mode", use_container_width=True)
_nav2.page_link(_page_ref("pages/2_Library.py"), label="📚 Prompt library", use_container_width=True)
_nav3.page_link(_page_ref("pages/3_Account.py"), label="🔑 Account & Plans", use_container_width=True)
_nav4, _nav5, _nav6 = st.columns(3)
_nav4.page_link(_page_ref("pages/4_Learn.py"), label="🎓 Learn modules", use_container_width=True)
_nav5.page_link(_page_ref("pages/5_Workspace.py"), label="🗂️ Pro Workspace", use_container_width=True)
_nav6.page_link(_page_ref("pages/6_AI_Feedback.py"), label="🤖 AI Feedback", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.recommendations:
    st.markdown("### 🧠 Intelligent Recommendations")
    query_label = st.session_state.last_recommendation_query or "(filter-only recommendation)"
    st.caption(f"Query: {query_label}")

    for i, rec in enumerate(st.session_state.recommendations, 1):
        prompt = rec['prompt']
        score_pct = int(rec['score'] * 100)
        title = prompt.get('title', 'Untitled')
        category = prompt.get('category', 'Unknown')
        difficulty = prompt.get('difficulty_level', 'intermediate')
        time_est = prompt.get('time_estimate', 'moderate')
        output_fmt = prompt.get('output_format', 'text')

        with st.expander(f"{i}. {title} ({score_pct}% match)", expanded=(i == 1)):
            st.markdown(f"**Category:** {category}")
            st.markdown(f"**Profile:** {difficulty} | {time_est} | {output_fmt}")
            st.markdown(f"**Why this was selected:** {', '.join(rec['reasons'])}")
            st.markdown(f"**Description:** {prompt.get('description', '')}")
            st.code(prompt.get('prompt', ''), language=None)

    st.divider()

# Main input area
st.markdown('<h3 class="prompt-title">Enter Your Prompt</h3>', unsafe_allow_html=True)
with st.form("analyze_form", clear_on_submit=False):
    user_prompt = st.text_area(
        "Type or paste your prompt here",
        placeholder="Example: Write a blog post about AI...",
        height=150,
        key="prompt_input",
        label_visibility="collapsed"
    )
    # Inside Streamlit forms, Ctrl+Enter submits text areas.
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.form_submit_button("🔍 Analyze & Improve Prompt", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Process analysis
if analyze_button and user_prompt.strip():
    with st.spinner("Analyzing your prompt and comparing with our collection..."):
        example_prompts = load_example_prompts()
        recommendations, improved_suggestion, best_practices, similar_examples = analyze_prompt(user_prompt, example_prompts)
        st.session_state.last_analyzed = {
            'original': user_prompt,
            'recommendations': recommendations,
            'improved': improved_suggestion,
            'best_practices': best_practices,
            'similar_examples': similar_examples
        }
        st.rerun()

# Display results if available
if st.session_state.last_analyzed:
    analysis = st.session_state.last_analyzed

    st.divider()
    st.markdown("### 📊 Analysis Results")

    # Show best practices score with detailed breakdown
    practices_count = sum(analysis['best_practices'].values())
    total_practices = len(analysis['best_practices'])
    score = (practices_count / total_practices) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Practices Score", f"{score:.0f}%", f"{practices_count}/{total_practices} practices found")
    with col2:
        st.metric("Recommendations", len(analysis['recommendations']))
    with col3:
        word_count = len(analysis['original'].split())
        st.metric("Word Count", word_count, "Optimal: 20-50 words" if word_count < 20 or word_count > 50 else "✓")

    # Detailed breakdown of best practices
    with st.expander("📋 Detailed Best Practices Breakdown"):
        practice_names = {
            'role_definition': 'Role Definition',
            'specific_instructions': 'Specific Instructions',
            'output_format': 'Output Format',
            'quality_markers': 'Quality Markers',
            'constraints': 'Constraints/Standards'
        }
        for practice, name in practice_names.items():
            status = "✅" if analysis['best_practices'].get(practice, False) else "❌"
            st.write(f"{status} **{name}**: {'Found' if analysis['best_practices'].get(practice, False) else 'Missing'}")

    # Display recommendations using Streamlit native components
    if analysis['recommendations']:
        st.markdown("### 💡 Recommendations for Improvement")
        for i, rec in enumerate(analysis['recommendations'], 1):
            priority_icon = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get('priority') == 'medium' else "🟢"
            with st.expander(f"{priority_icon} {i}. {rec['title']}", expanded=(rec.get('priority') == 'high')):
                st.markdown(f"**{rec['description']}**")
                if 'suggestion' in rec:
                    st.info(f"💡 {rec['suggestion']}")
                if rec.get('similar_example'):
                    st.markdown("**Similar example from our collection:**")
                    st.code(rec['similar_example'], language=None)
    else:
        st.success("🎉 Great job! Your prompt follows best practices. No major improvements needed.")

    # Display improved suggestion
    st.divider()
    st.markdown("### ✨ Suggested Improved Prompt")
    st.code(analysis['improved'], language=None)

    # AI Coach Deep Review & Production Rewrite
    st.divider()
    st.markdown("### 🤖 AI Prompt Coach Deep Review & Rewrite")
    st.caption("Generate a structured academic critique (Strengths, Critical Gaps, and Engineered TRACE Rewrite) for this prompt.")

    c_ai1, c_ai2 = st.columns([2, 3])
    with c_ai1:
        request_ai = st.button("✨ Consult AI Prompt Coach", type="secondary", key="home_consult_ai_btn", use_container_width=True)

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
                    st.markdown(f"**🌟 Strengths:**\n{c_data['strengths']}\n\n**⚠️ Gaps:**\n{c_data['gaps']}\n\n**🚀 Production Rewrite:**\n```\n{c_data['rewrite']}\n```")
            else:
                c_data = ai_feedback.get_pedagogical_coach_critique(analysis["original"])
                st.info("💡 **AI Coach Analysis & Refinement** (Connect an API key in AI Feedback for dynamic LLM responses):")
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
            st.code(analysis['improved'], language=None)
            st.success("✅ Select and copy the prompt above (Ctrl+C)")
    with col2:
        if st.button("🔄 Analyze Again", use_container_width=True):
            st.session_state.last_analyzed = None
            st.rerun()

    # Show original for comparison
    with st.expander("📝 View Original Prompt"):
        st.code(analysis['original'], language=None)

    # Show similar examples if available
    if analysis.get('similar_examples'):
        st.divider()
        st.markdown("### 📚 Similar Prompts from Our Collection")
        for ex in analysis['similar_examples'][:3]:
            with st.expander(f"📄 {ex.get('title', 'Example Prompt')} ({ex.get('category', 'Unknown')})"):
                st.markdown(f"**Tags:** {', '.join(ex.get('tags', []))}")
                st.code(ex.get('prompt', ''), language=None)

# Footer
st.divider()
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>💡 Prompt Improvement Tool | Built with Streamlit</p>
    <p>Make your prompts better using our curated collection and logical Python analysis</p>
    <p style='margin-top: 0.8rem; font-size: 0.9rem;'>{brand.copyright_line()} Intellectual property of {brand.owner_name()}. <a href='{brand.site_url()}'>{brand.site_url().split('//')[-1]}</a></p>
</div>
""", unsafe_allow_html=True)
