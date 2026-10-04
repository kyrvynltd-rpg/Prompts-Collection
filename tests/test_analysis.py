import analysis
from prompt_loader import get_all_prompts


def test_analysis_end_to_end_on_real_library():
    examples = get_all_prompts()
    prompt = "write an email to my lecturer asking for an extension"
    result = analysis.analyze_prompt(prompt, examples)
    suggestions, improved_text, practices, similar = result[:4]
    assert suggestions and "extension" in improved_text and isinstance(practices, dict) and similar
    features = analysis.detect_prompt_features(prompt)
    assert features
    improved = analysis.generate_improved_prompt(prompt, examples, practices, similar, {}, None, "")
    assert isinstance(improved, str) and len(improved) >= len(prompt)


def test_recommendations_and_paths():
    examples = get_all_prompts()
    recs = analysis.recommend_prompts("essay planning", examples, {}, max_results=3)
    assert 0 < len(recs) <= 3
    assert analysis.build_learning_paths(examples)


def test_text_helpers():
    assert analysis.normalize_text("  Hello,  WORLD! ") == analysis.normalize_text("hello world")
    assert analysis.calculate_jaccard_similarity({"a", "b"}, {"b", "c"}) == 1 / 3
    assert analysis.calculate_jaccard_similarity(set(), set()) == 0
    assert "essay" in analysis.extract_keywords("planning an essay for history")
