"""Pure prompt-analysis logic (no Streamlit). Split out of app.py so it can be tested and type-checked."""
from __future__ import annotations

import re
from collections import Counter


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
