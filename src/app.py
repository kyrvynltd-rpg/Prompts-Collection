"""
Streamlit Prompts Collection Platform
A platform for improving AI prompts based on best practices
"""

import streamlit as st
from prompt_loader import get_all_prompts, get_category_folders
import re
from collections import Counter
from pathlib import Path
import time
import base64


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

# Show a short branded landing screen before the app content.
app_param = st.query_params.get("app")
if isinstance(app_param, list):
    app_param = app_param[0] if app_param else None

if app_param != "1":
    lcol1, lcol2, lcol3 = st.columns([1, 2, 1])
    with lcol2:
        render_centered_logo(104)

        st.markdown(
            """
            <div class="welcome-wrap">
                <div class="main-header">Welcome to Prompt Learning Platform</div>
                <div class="welcome-lead">In this platform, you will learn how to write clearer, stronger prompts and improve AI output quality.</div>
                <ul class="welcome-list">
                    <li>Understand prompt structure: role, goal, constraints, and output format.</li>
                    <li>Compare your prompt against best practices from a curated prompt library.</li>
                    <li>Get actionable improvements and a refined version you can reuse immediately.</li>
                </ul>
                <div class="welcome-note"><span class="pulse">Preparing your workspace...</span> Redirecting in 7 seconds.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Preload cached data while users read the intro for smoother app transition.
        _ = load_example_prompts()

        progress_bar = st.progress(0)
        for i in range(7):
            progress_bar.progress(int(((i + 1) / 7) * 100))
            time.sleep(1)

        st.caption("If redirect does not start automatically, use this link below.")
        if st.button("Open the app now", type="primary", use_container_width=True):
            st.query_params["app"] = "1"
            st.rerun()

    st.query_params["app"] = "1"
    st.rerun()

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

def normalize_text(text):
    """Normalize text for better comparison"""
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def calculate_jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity between two sets"""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0

def extract_keywords(text, min_length=3):
    """Extract meaningful keywords from text"""
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 
                  'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 
                  'that', 'these', 'those', 'you', 'your', 'it', 'its', 'they', 'them'}
    
    words = normalize_text(text).split()
    keywords = [w for w in words if len(w) >= min_length and w not in stop_words]
    return set(keywords)

def extract_patterns_from_examples(example_prompts):
    """Extract common patterns and best practices from example prompts"""
    patterns = {
        'role_definitions': [],
        'action_verbs': Counter(),
        'quality_markers': Counter(),
        'format_indicators': Counter(),
        'constraint_phrases': Counter(),
        'common_structures': [],
        'category_patterns': {}
    }
    
    for ex in example_prompts:
        prompt_text = ex.get('prompt', '').lower()
        category = ex.get('category', '')
        
        # Track patterns by category
        if category not in patterns['category_patterns']:
            patterns['category_patterns'][category] = {
                'roles': [],
                'verbs': Counter(),
                'quality': Counter()
            }
        
        # Extract role definitions with better regex
        role_patterns = [
            r'you are ([^.]+?)(?:\.|,|$)',
            r'you\'re ([^.]+?)(?:\.|,|$)',
            r'act as ([^.]+?)(?:\.|,|$)',
            r'as a ([^.]+?)(?:\.|,|$)'
        ]
        for pattern in role_patterns:
            role_match = re.search(pattern, prompt_text)
            if role_match:
                role = role_match.group(1).strip()
                patterns['role_definitions'].append(role)
                patterns['category_patterns'][category]['roles'].append(role)
                break
        
        # Extract action verbs with context
        action_verbs = ['generate', 'create', 'write', 'analyze', 'help', 'provide', 
                       'explain', 'design', 'develop', 'assist', 'review', 'optimize',
                       'draft', 'build', 'make', 'produce', 'formulate', 'construct',
                       'compose', 'craft', 'prepare', 'organize', 'structure']
        for verb in action_verbs:
            if verb in prompt_text:
                patterns['action_verbs'][verb] += 1
                patterns['category_patterns'][category]['verbs'][verb] += 1
        
        # Extract quality markers
        quality_words = ['clear', 'well-structured', 'comprehensive', 'detailed', 
                        'accurate', 'professional', 'engaging', 'effective', 'concise',
                        'well-organized', 'thorough', 'precise', 'polished', 'refined']
        for word in quality_words:
            if word in prompt_text:
                patterns['quality_markers'][word] += 1
                patterns['category_patterns'][category]['quality'][word] += 1
        
        # Extract format indicators
        format_phrases = ['include', 'with', 'should', 'must', 'following', 
                         'according to', 'based on', 'structure', 'format',
                         'containing', 'featuring', 'consisting of']
        for phrase in format_phrases:
            if phrase in prompt_text:
                patterns['format_indicators'][phrase] += 1
        
        # Extract constraint phrases
        constraint_phrases = ['following', 'according to', 'based on', 
                            'following standards', 'best practices', 'standards',
                            'guidelines', 'principles', 'conventions']
        for phrase in constraint_phrases:
            if phrase in prompt_text:
                patterns['constraint_phrases'][phrase] += 1
    
    return patterns

ROLE_REGEX = re.compile(r"\b(you are|you\'re|act as|as an?|role:)\b", re.IGNORECASE)
ROLE_EXTRACT_REGEXES = [
    re.compile(r"you are\s+([^.]+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"you\'re\s+([^.]+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"act as\s+([^.]+?)(?:\.|,|$)", re.IGNORECASE),
]

ACTION_REGEXES = [
    re.compile(r"\b(generate|create|write|analy[sz]e|provide|explain|design|develop|review|optimi[sz]e|draft|summari[sz]e|classify|compare|plan|produce|format)\b", re.IGNORECASE),
    re.compile(r"\b(help|assist)\b", re.IGNORECASE),
]

OUTPUT_FORMAT_REGEXES = [
    re.compile(r"\b(output|response|deliverable|result)\b\s*[:\-]", re.IGNORECASE),
    re.compile(r"\b(json|yaml|markdown|table|bullet points?|steps?|sections?|checklist|schema|template)\b", re.IGNORECASE),
    re.compile(r"\b(return|respond)\b.*\b(in|as)\b", re.IGNORECASE),
]

QUALITY_REGEXES = [
    re.compile(r"\b(clear|concise|comprehensive|detailed|accurate|professional|engaging|well-structured|thorough|precise|evidence-based)\b", re.IGNORECASE),
    re.compile(r"\b(high quality|best quality|production-ready|robust)\b", re.IGNORECASE),
]

CONSTRAINT_REGEXES = [
    re.compile(r"\b(must|should|do not|don't|avoid|only|exactly|at least|at most|no more than|under|within|without)\b", re.IGNORECASE),
    re.compile(r"\b(audience|tone|length|word count|limit|constraints?|requirements?|guidelines?|standards?|best practices?)\b", re.IGNORECASE),
    re.compile(r"\b(following|according to|based on)\b", re.IGNORECASE),
]

EXAMPLE_REGEX = re.compile(r"\b(example|for instance|such as|e\.g\.|input:|output:)\b", re.IGNORECASE)
FORMAT_HINT_REGEX = re.compile(r"\b(format|structure|layout|organize|sections?)\b", re.IGNORECASE)

CATEGORY_PROFILES = {
    'Coding & Development': {
        'role': 'an expert software engineer',
        'constraints': 'Add constraints like "include edge cases", "handle errors", and "follow coding best practices".',
        'quality': ['correct', 'robust', 'well-documented'],
    },
    'Writing & Content': {
        'role': 'a professional writer',
        'constraints': 'Specify audience, tone, and length limits to improve consistency.',
        'quality': ['clear', 'engaging', 'well-structured'],
    },
    'Data Analysis': {
        'role': 'a data analyst',
        'constraints': 'Add assumptions, method, and validation constraints (for example confidence limits or checks).',
        'quality': ['accurate', 'evidence-based', 'clear'],
    },
    'Business & Strategy': {
        'role': 'a business strategist',
        'constraints': 'Define assumptions, decision criteria, and trade-offs to make recommendations actionable.',
        'quality': ['practical', 'structured', 'evidence-based'],
    },
    'Education & Learning': {
        'role': 'an experienced educator',
        'constraints': 'Specify learner level, outcomes, and assessment format.',
        'quality': ['clear', 'step-by-step', 'pedagogically sound'],
    },
}


def regex_hit_count(text, regexes):
    return sum(1 for rgx in regexes if rgx.search(text))


def infer_category(user_keywords, similar_examples):
    if similar_examples:
        return similar_examples[0].get('category', '')

    joined = ' '.join(sorted(user_keywords))
    if re.search(r"\b(code|python|javascript|api|debug|algorithm|database|sql|test)\b", joined):
        return 'Coding & Development'
    if re.search(r"\b(write|article|content|blog|email|copy|story|resume)\b", joined):
        return 'Writing & Content'
    if re.search(r"\b(data|statistics|dataset|visualization|report|analysis)\b", joined):
        return 'Data Analysis'
    if re.search(r"\b(business|strategy|market|sales|finance)\b", joined):
        return 'Business & Strategy'
    if re.search(r"\b(teach|lesson|quiz|study|learn|curriculum)\b", joined):
        return 'Education & Learning'
    return ''


def detect_prompt_features(prompt):
    text = prompt.strip()
    lower = text.lower()
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    word_count = len(text.split())

    role_hits = 1 if ROLE_REGEX.search(lower) else 0
    action_hits = regex_hit_count(lower, ACTION_REGEXES)
    format_hits = regex_hit_count(lower, OUTPUT_FORMAT_REGEXES)
    quality_hits = regex_hit_count(lower, QUALITY_REGEXES)
    constraint_hits = regex_hit_count(lower, CONSTRAINT_REGEXES)
    has_examples = bool(EXAMPLE_REGEX.search(lower))
    has_formatting = bool(FORMAT_HINT_REGEX.search(lower))

    # Weighted confidence to reduce over-triggering on generic words.
    action_score = min(1.0, action_hits / 1.0)
    format_score = min(1.0, format_hits / 2.0)
    quality_score = min(1.0, quality_hits / 1.0)
    constraints_score = min(1.0, constraint_hits / 2.0)

    avg_sentence_length = (sum(len(s.split()) for s in sentences) / len(sentences)) if sentences else 0

    return {
        'has_role': role_hits > 0,
        'has_action': action_score >= 1.0,
        'has_specifications': format_score >= 0.5,
        'has_quality_markers': quality_score >= 1.0,
        'has_constraints': constraints_score >= 0.5,
        'has_examples': has_examples,
        'has_formatting': has_formatting,
        'sentence_count': len(sentences),
        'word_count': word_count,
        'avg_sentence_length': avg_sentence_length,
        'scores': {
            'action': action_score,
            'format': format_score,
            'quality': quality_score,
            'constraints': constraints_score,
        },
    }


def find_similar_examples(user_prompt, example_prompts, max_examples=5):
    """Find similar examples with richer text representation to improve recommendation relevance."""
    user_keywords = extract_keywords(user_prompt)
    user_words = set(normalize_text(user_prompt).split())
    similarities = []

    for ex in example_prompts:
        ex_prompt = ex.get('prompt', '')
        ex_title = ex.get('title', '')
        ex_description = ex.get('description', '')
        ex_tags = ' '.join(ex.get('tags', []))
        ex_text = f"{ex_title} {ex_description} {ex_tags} {ex_prompt}".strip()

        ex_keywords = extract_keywords(ex_text)
        ex_words = set(normalize_text(ex_text).split())

        keyword_similarity = calculate_jaccard_similarity(user_keywords, ex_keywords)
        word_similarity = calculate_jaccard_similarity(user_words, ex_words)

        category = ex.get('category', '').lower()
        category_bonus = 0.08 if any(word in category for word in user_keywords) else 0

        tags = [tag.lower() for tag in ex.get('tags', [])]
        tag_overlap = len([tag for tag in tags if tag in user_keywords])
        tag_bonus = min(0.12, 0.04 * tag_overlap)

        combined_score = (keyword_similarity * 0.55) + (word_similarity * 0.25) + category_bonus + tag_bonus
        if combined_score > 0.07:
            similarities.append({'prompt': ex, 'score': combined_score})

    similarities.sort(key=lambda x: x['score'], reverse=True)
    return [s['prompt'] for s in similarities[:max_examples]]


def _metadata_completeness(prompt):
    fields = [
        'difficulty_level', 'time_estimate', 'output_format', 'expected_outcomes',
        'prerequisites', 'use_case_examples', 'success_criteria', 'tone',
        'best_for', 'avoid_if', 'constraints', 'related_prompts'
    ]
    present = 0
    for f in fields:
        value = prompt.get(f)
        if value is None:
            continue
        if isinstance(value, (list, dict, str)) and len(value) == 0:
            continue
        present += 1
    return present / len(fields)


def _build_prompt_search_text(prompt):
    parts = [
        prompt.get('title', ''),
        prompt.get('description', ''),
        prompt.get('prompt', ''),
        ' '.join(prompt.get('tags', [])),
        ' '.join(prompt.get('expected_outcomes', [])),
        ' '.join(prompt.get('use_case_examples', [])),
        ' '.join(prompt.get('success_criteria', [])),
        prompt.get('best_for', ''),
    ]
    return ' '.join(p for p in parts if p)


def _recommendation_score(prompt, query, filters):
    text_blob = _build_prompt_search_text(prompt)
    query_keywords = extract_keywords(query) if query else set()
    prompt_keywords = extract_keywords(text_blob)

    query_score = calculate_jaccard_similarity(query_keywords, prompt_keywords) if query_keywords else 0.0

    # Metadata filter scoring
    filter_score = 0.0
    filter_count = 0
    if filters.get('difficulty') and filters['difficulty'] != 'Any':
        filter_count += 1
        filter_score += 1.0 if prompt.get('difficulty_level', '').lower() == filters['difficulty'].lower() else 0.0
    if filters.get('time') and filters['time'] != 'Any':
        filter_count += 1
        filter_score += 1.0 if prompt.get('time_estimate', '').lower() == filters['time'].lower() else 0.0
    if filters.get('output_format') and filters['output_format'] != 'Any':
        filter_count += 1
        filter_score += 1.0 if prompt.get('output_format', '').lower() == filters['output_format'].lower() else 0.0

    normalized_filter_score = (filter_score / filter_count) if filter_count > 0 else 0.0
    metadata_score = _metadata_completeness(prompt)

    # Weighted composite favors intent match first, then filter fit and metadata quality.
    if query_keywords:
        final_score = (query_score * 0.65) + (normalized_filter_score * 0.25) + (metadata_score * 0.10)
    else:
        final_score = (normalized_filter_score * 0.70) + (metadata_score * 0.30)
    return final_score


def recommend_prompts(query, prompts, filters, max_results=8):
    scored = []
    for prompt in prompts:
        score = _recommendation_score(prompt, query, filters)
        if score > 0.08 or (not query and any(v != 'Any' for v in filters.values())):
            scored.append((score, prompt))

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:max_results]

    recommendations = []
    for score, prompt in top:
        reasons = []
        if query:
            reasons.append("Strong intent match")
        if filters.get('difficulty') != 'Any' and prompt.get('difficulty_level') == filters.get('difficulty'):
            reasons.append("Difficulty aligned")
        if filters.get('time') != 'Any' and prompt.get('time_estimate') == filters.get('time'):
            reasons.append("Time estimate aligned")
        if filters.get('output_format') != 'Any' and prompt.get('output_format') == filters.get('output_format'):
            reasons.append("Output format aligned")
        if not reasons:
            reasons.append("High metadata quality")

        recommendations.append({
            'score': score,
            'prompt': prompt,
            'reasons': reasons,
        })
    return recommendations


def build_learning_paths(prompts):
    difficulty_order = {'beginner': 0, 'intermediate': 1, 'expert': 2}
    by_category = {}
    for p in prompts:
        cat = p.get('category', 'General')
        by_category.setdefault(cat, []).append(p)

    paths = {}
    for cat, items in by_category.items():
        ordered = sorted(
            items,
            key=lambda p: (
                difficulty_order.get(p.get('difficulty_level', 'intermediate'), 1),
                p.get('title', '')
            )
        )
        if ordered:
            paths[cat] = ordered[:6]
    return paths


def analyze_prompt_structure(user_prompt):
    """Analyze structural features using boundary-aware detection."""
    return detect_prompt_features(user_prompt)


def infer_role_from_context(user_prompt, similar_examples, category_hint):
    for ex in similar_examples:
        ex_prompt = ex.get('prompt', '')
        for rgx in ROLE_EXTRACT_REGEXES:
            match = rgx.search(ex_prompt)
            if match:
                return match.group(1).strip()

    user_keywords = extract_keywords(user_prompt)
    if category_hint in CATEGORY_PROFILES:
        return CATEGORY_PROFILES[category_hint]['role']

    if any(kw in user_keywords for kw in ['code', 'program', 'python', 'javascript', 'function', 'api', 'database']):
        return 'an expert programmer'
    if any(kw in user_keywords for kw in ['write', 'article', 'blog', 'content', 'email', 'copy']):
        return 'a professional writer'
    if any(kw in user_keywords for kw in ['analyze', 'data', 'report', 'statistics']):
        return 'a data analyst'
    if any(kw in user_keywords for kw in ['design', 'create', 'build', 'develop']):
        return 'a creative professional'
    return 'a helpful AI assistant'


def analyze_prompt(user_prompt, example_prompts):
    """Analyze user prompt and provide calibrated, category-aware recommendations."""
    recommendations = []
    word_count = len(user_prompt.split())

    patterns = extract_patterns_from_examples(example_prompts)
    similar_examples = find_similar_examples(user_prompt, example_prompts)
    structure = analyze_prompt_structure(user_prompt)

    user_keywords = extract_keywords(user_prompt)
    category_hint = infer_category(user_keywords, similar_examples)
    profile = CATEGORY_PROFILES.get(category_hint, {})

    best_practices = {
        'role_definition': structure['has_role'],
        'specific_instructions': structure['has_action'],
        'output_format': structure['has_specifications'],
        'quality_markers': structure['has_quality_markers'],
        'constraints': structure['has_constraints']
    }

    # Role guidance is contextual: strong prompts are not forced to have explicit role.
    if not best_practices['role_definition']:
        role_priority = 'low'
        if word_count < 18 and not structure['has_specifications']:
            role_priority = 'high'
        elif word_count < 28:
            role_priority = 'medium'

        suggested_role = infer_role_from_context(user_prompt, similar_examples, category_hint)
        recommendations.append({
            'type': 'role_definition',
            'title': 'Consider Adding Role Definition',
            'description': 'Role context can improve consistency, especially for short or ambiguous prompts.',
            'suggestion': f'You can start with: "You are {suggested_role}."',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': role_priority
        })

    if not best_practices['specific_instructions']:
        suggested_verbs = [verb for verb, _ in patterns['action_verbs'].most_common(5)] or ['analyze', 'create', 'explain']
        recommendations.append({
            'type': 'specific_instructions',
            'title': 'Add Specific Action Instructions',
            'description': 'Use explicit action verbs so the expected task is unambiguous.',
            'suggestion': f'Use directive verbs such as: {", ".join(suggested_verbs[:5])}.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'high'
        })

    if structure['scores']['format'] < 0.5 and word_count > 12:
        recommendations.append({
            'type': 'output_format',
            'title': 'Specify Output Format or Structure',
            'description': 'Define the response format (for example sections, bullets, JSON, table) to improve reliability.',
            'suggestion': 'Add a clear output contract, such as "Output: 3 sections with bullet points" or "Return JSON with keys...".',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })

    if word_count < 12:
        recommendations.append({
            'type': 'detail',
            'title': 'Add More Detail',
            'description': f'Your prompt is short ({word_count} words). Add objective, context, and constraints to reduce ambiguity.',
            'suggestion': 'Include: objective, audience/context, output format, and any limits.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'high'
        })
    elif 12 <= word_count < 20:
        recommendations.append({
            'type': 'detail',
            'title': 'Consider Adding More Context',
            'description': f'Your prompt is concise ({word_count} words). A bit more context can increase precision.',
            'suggestion': 'Add one sentence clarifying constraints, audience, or acceptance criteria.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })

    if structure['scores']['quality'] < 1.0 and word_count > 18:
        quality_suggestions = profile.get('quality') or [word for word, _ in patterns['quality_markers'].most_common(5)]
        if not quality_suggestions:
            quality_suggestions = ['clear', 'comprehensive', 'accurate']
        recommendations.append({
            'type': 'quality_markers',
            'title': 'Add Quality Indicators',
            'description': 'Quality criteria improve consistency and make outputs easier to evaluate.',
            'suggestion': f'Add quality expectations such as: {", ".join(quality_suggestions[:3])}.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })

    if structure['scores']['constraints'] < 0.5 and word_count > 24:
        constraint_suggestion = profile.get('constraints', 'Add constraints on scope, length, tone, and must/avoid rules to tighten outputs.')
        recommendations.append({
            'type': 'constraints',
            'title': 'Add Explicit Constraints',
            'description': 'Constraints reduce variability and improve control over final output.',
            'suggestion': constraint_suggestion,
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })

    if structure['sentence_count'] == 1 and structure['avg_sentence_length'] > 28:
        recommendations.append({
            'type': 'structure',
            'title': 'Consider Breaking Into Multiple Sentences',
            'description': 'Long single-sentence prompts are harder to parse reliably.',
            'suggestion': 'Split request into 2-4 sentences or short bullet points.',
            'similar_example': None,
            'priority': 'low'
        })

    if not structure['has_examples'] and word_count > 35:
        recommendations.append({
            'type': 'examples',
            'title': 'Consider Adding an Example',
            'description': 'One concrete example can greatly improve alignment with your intent.',
            'suggestion': 'Add a compact sample input/output snippet.',
            'similar_example': None,
            'priority': 'low'
        })

    # Priority sorting and calibration: suppress very low-signal recommendations for already-strong prompts.
    strength_score = (
        (1.0 if best_practices['role_definition'] else 0.0) * 0.8 +
        structure['scores']['action'] * 1.0 +
        structure['scores']['format'] * 1.1 +
        structure['scores']['quality'] * 0.9 +
        structure['scores']['constraints'] * 0.8
    )
    if strength_score >= 3.7:
        recommendations = [r for r in recommendations if r['priority'] in ('high', 'medium')]

    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))

    improved_suggestion = generate_improved_prompt(
        user_prompt,
        example_prompts,
        best_practices,
        similar_examples,
        patterns,
        structure,
        category_hint,
    )

    return recommendations, improved_suggestion, best_practices, similar_examples


def generate_improved_prompt(user_prompt, example_prompts, best_practices, similar_examples, patterns, structure=None, category_hint=''):
    """Generate a suggested improved version of the prompt using shared feature detection logic."""
    improved = user_prompt.strip()
    word_count = len(improved.split())
    structure = structure or detect_prompt_features(improved)

    # Add role only when the missing-role signal is meaningful.
    if not best_practices['role_definition'] and (word_count < 28 or not structure['has_specifications']):
        role = infer_role_from_context(improved, similar_examples, category_hint)
        improved = f"You are {role}. {improved}"

    # Add quality expectations when missing.
    if structure['scores']['quality'] < 1.0 and word_count > 18:
        if category_hint in CATEGORY_PROFILES:
            quality_suggestions = CATEGORY_PROFILES[category_hint]['quality']
        else:
            quality_suggestions = ['clear', 'comprehensive']

        q = quality_suggestions[0]
        if q not in improved.lower():
            improved = re.sub(r'([.!?])$', f', keep the output {q}\\1', improved)

    # Add constraints when prompt is long enough but unconstrained.
    if structure['scores']['constraints'] < 0.5 and word_count > 24:
        if category_hint == 'Coding & Development':
            addition = ' include edge cases and basic error handling'
        elif category_hint == 'Writing & Content':
            addition = ' define audience, tone, and length'
        elif category_hint == 'Data Analysis':
            addition = ' state assumptions and validation checks'
        else:
            addition = ' include clear constraints and limits'
        improved = re.sub(r'([.!?])$', f',{addition}\\1', improved)

    if improved and improved[0].islower():
        improved = improved[0].upper() + improved[1:]

    if improved and improved[-1] not in ['.', '!', '?']:
        improved += "."

    improved = re.sub(r'\s+', ' ', improved)
    improved = re.sub(r'([,.!?])\1+', r'\1', improved)
    improved = re.sub(r'\s+([,.!?])', r'\1', improved)

    return improved.strip()

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
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>💡 Prompt Improvement Tool | Built with Streamlit</p>
    <p>Make your prompts better using our curated collection and logical Python analysis</p>
    <p style='margin-top: 0.8rem; font-size: 0.9rem;'>Copyright © 2026 Gabriele Iacopo Langellotto. All rights reserved. Intellectual Property of Gabriele Iacopo Langellotto.</p>
</div>
""", unsafe_allow_html=True)
