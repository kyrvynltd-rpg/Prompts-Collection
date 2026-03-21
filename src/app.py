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

def find_similar_examples(user_prompt, example_prompts, max_examples=5):
    """Find similar example prompts using improved similarity scoring"""
    user_normalized = normalize_text(user_prompt)
    user_keywords = extract_keywords(user_prompt)
    user_words = set(user_normalized.split())
    
    similarities = []
    
    for ex in example_prompts:
        ex_prompt = ex.get('prompt', '')
        ex_normalized = normalize_text(ex_prompt)
        ex_keywords = extract_keywords(ex_prompt)
        ex_words = set(ex_normalized.split())
        
        # Calculate multiple similarity metrics
        # 1. Jaccard similarity on keywords
        keyword_similarity = calculate_jaccard_similarity(user_keywords, ex_keywords)
        
        # 2. Word overlap similarity
        word_similarity = calculate_jaccard_similarity(user_words, ex_words)
        
        # 3. Category relevance (if user prompt matches category keywords)
        category = ex.get('category', '').lower()
        category_bonus = 0.1 if any(word in category for word in user_keywords) else 0
        
        # 4. Tag relevance
        tags = [tag.lower() for tag in ex.get('tags', [])]
        tag_bonus = 0.05 * len([tag for tag in tags if tag in user_keywords])
        
        # Combined score (weighted)
        combined_score = (keyword_similarity * 0.5) + (word_similarity * 0.3) + category_bonus + min(tag_bonus, 0.15)
        
        if combined_score > 0.05:  # Lower threshold for better matches
            similarities.append({
                'prompt': ex,
                'score': combined_score,
                'keyword_sim': keyword_similarity,
                'word_sim': word_similarity,
                'common_keywords': user_keywords.intersection(ex_keywords)
            })
    
    # Sort by combined score
    similarities.sort(key=lambda x: x['score'], reverse=True)
    return [s['prompt'] for s in similarities[:max_examples]]

def analyze_prompt_structure(user_prompt):
    """Analyze the structural elements of the prompt"""
    structure = {
        'has_role': False,
        'has_action': False,
        'has_specifications': False,
        'has_quality_markers': False,
        'has_constraints': False,
        'sentence_count': len(re.split(r'[.!?]+', user_prompt)),
        'word_count': len(user_prompt.split()),
        'avg_sentence_length': 0,
        'has_examples': False,
        'has_formatting': False
    }
    
    user_lower = user_prompt.lower()
    
    # Check for role
    structure['has_role'] = any(phrase in user_lower for phrase in 
                                ['you are', 'you\'re', 'act as', 'role:', 'as a'])
    
    # Check for action verbs
    action_verbs = ['generate', 'create', 'write', 'analyze', 'help', 'provide', 
                   'explain', 'design', 'develop', 'assist', 'review', 'optimize']
    structure['has_action'] = any(verb in user_lower for verb in action_verbs)
    
    # Check for specifications
    spec_indicators = ['include', 'with', 'should', 'must', 'following', 
                      'according to', 'based on', 'structure', 'format']
    structure['has_specifications'] = any(indicator in user_lower for indicator in spec_indicators)
    
    # Check for quality markers
    quality_words = ['clear', 'well-structured', 'comprehensive', 'detailed', 
                    'accurate', 'professional', 'engaging', 'effective']
    structure['has_quality_markers'] = any(word in user_lower for word in quality_words)
    
    # Check for constraints
    constraint_phrases = ['following', 'according to', 'based on', 
                        'following standards', 'best practices', 'standards']
    structure['has_constraints'] = any(phrase in user_lower for phrase in constraint_phrases)
    
    # Check for examples
    structure['has_examples'] = any(phrase in user_lower for phrase in 
                                   ['example', 'for instance', 'such as', 'like'])
    
    # Check for formatting instructions
    structure['has_formatting'] = any(phrase in user_lower for phrase in 
                                     ['format', 'structure', 'layout', 'organize'])
    
    # Calculate average sentence length
    sentences = [s.strip() for s in re.split(r'[.!?]+', user_prompt) if s.strip()]
    if sentences:
        structure['avg_sentence_length'] = sum(len(s.split()) for s in sentences) / len(sentences)
    
    return structure

def analyze_prompt(user_prompt, example_prompts):
    """Analyze user prompt and provide improvement recommendations based on examples"""
    recommendations = []
    user_lower = user_prompt.lower()
    user_words = user_prompt.split()
    word_count = len(user_words)
    
    # Extract patterns from examples
    patterns = extract_patterns_from_examples(example_prompts)
    
    # Find similar examples
    similar_examples = find_similar_examples(user_prompt, example_prompts)
    
    # Analyze prompt structure
    structure = analyze_prompt_structure(user_prompt)
    
    # Extract best practices from example prompts
    best_practices = {
        'role_definition': structure['has_role'],
        'specific_instructions': structure['has_action'],
        'output_format': structure['has_specifications'],
        'quality_markers': structure['has_quality_markers'],
        'constraints': structure['has_constraints']
    }
    
    # Check for role definition
    if not best_practices['role_definition']:
        # Suggest role based on similar examples or content analysis
        suggested_role = "a helpful AI assistant"
        role_context = ""
        
        if similar_examples:
            for ex in similar_examples:
                ex_prompt = ex.get('prompt', '').lower()
                role_patterns = [
                    r'you are ([^.]+?)(?:\.|,|$)',
                    r'you\'re ([^.]+?)(?:\.|,|$)',
                    r'act as ([^.]+?)(?:\.|,|$)'
                ]
                for pattern in role_patterns:
                    role_match = re.search(pattern, ex_prompt)
                    if role_match:
                        suggested_role = role_match.group(1).strip()
                        role_context = f" (based on similar prompt: {ex.get('title', '')})"
                        break
                if suggested_role != "a helpful AI assistant":
                    break
        
        # If no similar examples, infer from content
        if suggested_role == "a helpful AI assistant":
            user_keywords = extract_keywords(user_prompt)
            if any(kw in user_keywords for kw in ['code', 'program', 'python', 'javascript', 'function']):
                suggested_role = "an expert programmer"
            elif any(kw in user_keywords for kw in ['write', 'article', 'blog', 'content', 'email']):
                suggested_role = "a professional writer"
            elif any(kw in user_keywords for kw in ['analyze', 'data', 'report', 'statistics']):
                suggested_role = "a data analyst"
            elif any(kw in user_keywords for kw in ['design', 'create', 'build', 'develop']):
                suggested_role = "a creative professional"
        
        recommendations.append({
            'type': 'role_definition',
            'title': 'Add Role Definition',
            'description': 'Effective prompts start by defining the AI\'s role. This establishes context and sets expectations for the response.',
            'suggestion': f'Consider starting with: "You are {suggested_role}."{role_context}',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'high'
        })
    
    # Check for specific instructions
    if not best_practices['specific_instructions']:
        # Get most common action verbs from similar examples or patterns
        suggested_verbs = []
        if similar_examples:
            for ex in similar_examples:
                ex_prompt = ex.get('prompt', '').lower()
                for verb, count in patterns['action_verbs'].most_common(5):
                    if verb in ex_prompt:
                        suggested_verbs.append(verb)
                        if len(suggested_verbs) >= 3:
                            break
                if len(suggested_verbs) >= 3:
                    break
        
        if not suggested_verbs:
            suggested_verbs = [verb for verb, _ in patterns['action_verbs'].most_common(5)]
        
        recommendations.append({
            'type': 'specific_instructions',
            'title': 'Add Specific Action Instructions',
            'description': 'Include clear action verbs that specify what the AI should do. This makes your prompt more directive and effective.',
            'suggestion': f'Consider using action verbs like: {", ".join(suggested_verbs[:5])}',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'high'
        })
    
    # Check for output format specifications
    if not best_practices['output_format'] and word_count > 10:
        recommendations.append({
            'type': 'output_format',
            'title': 'Specify Output Format or Structure',
            'description': 'Describe the desired output format, structure, or key elements to include. This helps the AI understand exactly what you need.',
            'suggestion': 'Add phrases like "include...", "with...", "following...", or "should have..." to specify what you want in the output.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })
    
    # Check prompt length and detail
    if word_count < 10:
        recommendations.append({
            'type': 'detail',
            'title': 'Add More Detail',
            'description': f'Your prompt is quite short ({word_count} words). Effective prompts typically provide clear context and specific instructions (20-50 words is ideal).',
            'suggestion': 'Add more context about what you want, any constraints, examples of desired output, or specific requirements.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'high'
        })
    elif word_count > 200:
        recommendations.append({
            'type': 'conciseness',
            'title': 'Consider Conciseness',
            'description': f'Your prompt is quite long ({word_count} words). While detail is good, ensure every part is necessary and clear.',
            'suggestion': 'Review if any sections can be condensed while maintaining clarity and essential information. Consider breaking into bullet points if needed.',
            'similar_example': None,
            'priority': 'low'
        })
    elif word_count < 20 and word_count >= 10:
        recommendations.append({
            'type': 'detail',
            'title': 'Consider Adding More Context',
            'description': f'Your prompt could benefit from more detail ({word_count} words). Adding context, constraints, or examples can improve results.',
            'suggestion': 'Consider adding: specific requirements, examples, constraints, or quality indicators.',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })
    
    # Check for quality markers
    if not best_practices['quality_markers'] and word_count > 15:
        quality_suggestions = [word for word, _ in patterns['quality_markers'].most_common(5)]
        if not quality_suggestions:
            quality_suggestions = ['clear', 'well-structured', 'comprehensive', 'detailed', 'professional']
        
        recommendations.append({
            'type': 'quality_markers',
            'title': 'Add Quality Indicators',
            'description': 'Specify the desired quality level or characteristics of the output. This helps guide the AI toward better results.',
            'suggestion': f'Consider adding quality descriptors like: {", ".join(quality_suggestions[:5])}',
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })
    
    # Check for constraints or guidelines
    if not best_practices['constraints'] and word_count > 20:
        # Get category-specific constraint suggestions
        constraint_suggestion = 'Add phrases like "following [standard]", "according to [guideline]", "with [best practice]", or "using [methodology]"'
        
        if similar_examples:
            # Find category from similar examples
            category = similar_examples[0].get('category', '')
            if 'Coding' in category or 'Development' in category:
                constraint_suggestion = 'Add phrases like "following PEP 8 standards", "with proper error handling", or "using best practices"'
            elif 'Writing' in category or 'Content' in category:
                constraint_suggestion = 'Add phrases like "following style guidelines", "with proper formatting", or "using clear language"'
            elif 'Business' in category or 'Strategy' in category:
                constraint_suggestion = 'Add phrases like "based on industry standards", "following best practices", or "using proven methodologies"'
            elif 'Data' in category:
                constraint_suggestion = 'Add phrases like "following data science best practices", "with proper validation", or "using statistical methods"'
        
        recommendations.append({
            'type': 'constraints',
            'title': 'Add Guidelines or Standards',
            'description': 'Include standards, best practices, or constraints to guide the output quality and ensure it meets your requirements.',
            'suggestion': constraint_suggestion,
            'similar_example': similar_examples[0].get('prompt', '') if similar_examples else None,
            'priority': 'medium'
        })
    
    # Check sentence structure
    if structure['sentence_count'] == 1 and word_count > 30:
        recommendations.append({
            'type': 'structure',
            'title': 'Consider Breaking Into Multiple Sentences',
            'description': 'Your prompt is one long sentence. Breaking it into multiple sentences can improve clarity and readability.',
            'suggestion': 'Split complex instructions into separate sentences for better clarity.',
            'similar_example': None,
            'priority': 'low'
        })
    
    # Check for examples
    if not structure['has_examples'] and word_count > 25:
        recommendations.append({
            'type': 'examples',
            'title': 'Consider Adding Examples',
            'description': 'Including examples can help clarify your expectations and improve the quality of the output.',
            'suggestion': 'Add phrases like "for example", "such as", or provide a concrete example of what you want.',
            'similar_example': None,
            'priority': 'low'
        })
    
    # Sort recommendations by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
    
    # Generate improved version suggestion
    improved_suggestion = generate_improved_prompt(user_prompt, example_prompts, best_practices, similar_examples, patterns)
    
    return recommendations, improved_suggestion, best_practices, similar_examples

def generate_improved_prompt(user_prompt, example_prompts, best_practices, similar_examples, patterns):
    """Generate a suggested improved version of the prompt using logical analysis"""
    improved = user_prompt.strip()
    user_lower = improved.lower()
    user_keywords = extract_keywords(improved)
    word_count = len(improved.split())
    
    # If no role definition, add one based on content analysis
    if not best_practices['role_definition']:
        # Try to find role from similar examples first
        role = None
        if similar_examples:
            for ex in similar_examples:
                ex_prompt = ex.get('prompt', '').lower()
                role_patterns = [
                    r'you are ([^.]+?)(?:\.|,|$)',
                    r'you\'re ([^.]+?)(?:\.|,|$)',
                    r'act as ([^.]+?)(?:\.|,|$)'
                ]
                for pattern in role_patterns:
                    role_match = re.search(pattern, ex_prompt)
                    if role_match:
                        role = role_match.group(1).strip()
                        break
                if role:
                    break
        
        # If no role from examples, infer from content with more sophisticated matching
        if not role:
            # Check for coding-related keywords
            coding_keywords = ['code', 'program', 'function', 'script', 'python', 'javascript', 
                             'api', 'algorithm', 'debug', 'test', 'database', 'sql', 'html', 'css']
            if any(kw in user_keywords for kw in coding_keywords):
                role = "an expert programmer"
            # Check for writing-related keywords
            elif any(kw in user_keywords for kw in ['write', 'article', 'blog', 'content', 'post', 
                                                    'email', 'document', 'copy', 'story', 'essay']):
                role = "a professional writer"
            # Check for data/analysis keywords
            elif any(kw in user_keywords for kw in ['analyze', 'data', 'report', 'statistics', 
                                                   'visualization', 'dataset', 'chart', 'graph']):
                role = "a data analyst"
            # Check for business/strategy keywords
            elif any(kw in user_keywords for kw in ['business', 'strategy', 'plan', 'market', 
                                                    'sales', 'marketing', 'financial']):
                role = "a business consultant"
            # Check for design/creative keywords
            elif any(kw in user_keywords for kw in ['design', 'create', 'build', 'develop', 
                                                    'creative', 'art', 'visual']):
                role = "a creative professional"
            # Check for education keywords
            elif any(kw in user_keywords for kw in ['teach', 'learn', 'explain', 'tutor', 
                                                   'education', 'lesson', 'course']):
                role = "an experienced educator"
            # Check for support/help keywords
            elif any(kw in user_keywords for kw in ['help', 'assist', 'support', 'guide', 'advice']):
                role = "a helpful assistant"
            else:
                role = "a helpful AI assistant"
        
        improved = f"You are {role}. {improved}"
    
    # Add quality markers if missing and prompt is substantial
    if not best_practices['quality_markers'] and word_count > 15:
        # Get most appropriate quality marker from similar examples
        quality_suggestions = []
        if similar_examples:
            for ex in similar_examples:
                ex_prompt = ex.get('prompt', '').lower()
                for quality in ['clear', 'comprehensive', 'well-structured', 'detailed', 'professional']:
                    if quality in ex_prompt and quality not in improved.lower():
                        quality_suggestions.append(quality)
                        if len(quality_suggestions) >= 2:
                            break
                if len(quality_suggestions) >= 2:
                    break
        
        # If no suggestions from examples, add based on context
        if not quality_suggestions:
            if any(kw in user_keywords for kw in ['code', 'program', 'technical']):
                quality_suggestions = ['clean', 'well-documented']
            elif any(kw in user_keywords for kw in ['write', 'content', 'article']):
                quality_suggestions = ['engaging', 'well-structured']
            else:
                quality_suggestions = ['clear', 'comprehensive']
        
        # Insert quality marker appropriately
        if quality_suggestions and quality_suggestions[0] not in improved.lower():
            # Try to insert after first action verb or at appropriate position
            action_verbs = ['generate', 'create', 'write', 'analyze', 'help', 'provide', 'design', 'develop']
            for verb in action_verbs:
                if verb in improved.lower():
                    # Insert quality marker after the verb
                    improved = re.sub(
                        rf'({verb}[^.]*?)([,.])',
                        rf'\1, {quality_suggestions[0]}\2',
                        improved,
                        count=1,
                        flags=re.IGNORECASE
                    )
                    break
    
    # Add constraints/standards if missing and prompt is substantial
    if not best_practices['constraints'] and word_count > 25:
        # Check if we should add best practices reference
        if any(kw in user_keywords for kw in ['code', 'program', 'python', 'javascript']):
            if 'following' not in improved.lower() and 'standards' not in improved.lower():
                # Try to add at the end before punctuation
                improved = re.sub(r'([.!?])$', r', following best practices\1', improved)
        elif any(kw in user_keywords for kw in ['write', 'content', 'document']):
            if 'best practices' not in improved.lower():
                improved = re.sub(r'([.!?])$', r', following writing best practices\1', improved)
    
    # Ensure proper capitalization
    if improved and improved[0].islower():
        improved = improved[0].upper() + improved[1:]
    
    # Ensure it ends with punctuation
    if improved and improved[-1] not in ['.', '!', '?']:
        improved += "."
    
    # Clean up any double punctuation or spacing issues
    improved = re.sub(r'\s+', ' ', improved)  # Multiple spaces
    improved = re.sub(r'([,.!?])\1+', r'\1', improved)  # Multiple punctuation
    improved = re.sub(r'\s+([,.!?])', r'\1', improved)  # Space before punctuation
    
    return improved.strip()

# Sidebar (keeping as requested)
with st.sidebar:
    st.header("🔍 Search & Filter")
    
    # Search
    search_query = st.text_input("Search prompts", placeholder="Type keywords, tags, or titles...")
    
    # Category filter
    category_folders = get_category_folders()
    categories = ["All Categories"] + sorted(category_folders)
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Load prompts for sidebar
    all_prompts = load_example_prompts()
    
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
