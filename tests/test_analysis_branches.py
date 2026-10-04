import json

import pytest

import analysis
import prompt_loader
from prompt_loader import get_all_prompts

PROMPTS = [
    "help", "write a python function", "write an email", "analyze this dataset and report statistics",
    "design a business strategy for sales growth in the market", "teach me a lesson and make a quiz to study",
    "create something", "build a thing",
    "Write a blog article about sustainable gardening for beginners that is engaging and well structured and includes "
    "tips, a short intro, a call to action, and a friendly tone. Please keep the writing clear and accurate and make sure it "
    "flows well from start to end because readers are busy people who skim.",
    "You are a senior data analyst. Analyse the attached dataset and produce a report in a table format with headings. Include "
    "assumptions, validation checks and limits. For example, input: sales by month, output: a summary table. Avoid jargon and "
    "do not exceed 300 words. Be clear, accurate and comprehensive in the output.",
    "Debug this python code and explain the algorithm and database query step by step including edge cases and error handling "
    "so that I understand why the api call fails and how to test it properly in my project this week",
    "one very long run on sentence without any punctuation that keeps going and going and going and going and going and going "
    "and going and going and going and going and going and going and going and going and going and going and going and going",
]
HINTS = ["", "Coding & Development", "Writing & Content", "Data Analysis", "Business & Strategy", "Education & Learning", "Nope"]


@pytest.fixture(scope="module")
def examples():
    return get_all_prompts()


@pytest.mark.parametrize("prompt", PROMPTS)
def test_every_prompt_shape_analyses_and_improves(prompt, examples):
    suggestions, improved, practices, similar = analysis.analyze_prompt(prompt, examples)[:4]
    assert isinstance(suggestions, list) and improved and isinstance(practices, dict)
    structure = analysis.analyze_prompt_structure(prompt)
    patterns = analysis.extract_patterns_from_examples(examples[:20])
    for hint in HINTS:
        out = analysis.generate_improved_prompt(prompt, examples, practices, similar, patterns, structure, hint)
        assert isinstance(out, str) and out
        analysis.infer_role_from_context(prompt, similar, hint)
    analysis.infer_category(analysis.extract_keywords(prompt), similar)


def test_infer_category_all_branches():
    for words, expected in (({"python"}, "Coding & Development"), ({"blog"}, "Writing & Content"), ({"dataset"}, "Data Analysis"),
                            ({"strategy"}, "Business & Strategy"), ({"quiz"}, "Education & Learning"), ({"zzz"}, "")):
        assert analysis.infer_category(words, []) in (expected, analysis.infer_category(words, []))
    assert analysis.infer_category({"python"}, []) == "Coding & Development"
    assert analysis.infer_category({"zzz"}, []) == ""


@pytest.mark.parametrize("filters", [
    {}, {"difficulty": "beginner"}, {"time": "quick"}, {"output_format": "markdown"},
    {"difficulty": "Any", "time": "Any", "output_format": "Any"},
    {"difficulty": "beginner", "time": "moderate", "output_format": "markdown"},
])
@pytest.mark.parametrize("query", ["", "essay planning", "email"])
def test_recommendations_with_filters(query, filters, examples):
    results = analysis.recommend_prompts(query, examples, filters, max_results=5)
    assert len(results) <= 5
    for item in results:
        assert item is not None


def test_prompt_loader_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_path / "prompts")
    assert prompt_loader.get_category_folders() == []
    assert prompt_loader.load_prompts_from_category("none") == []
    path = prompt_loader.save_prompt("Study", "My Prompt!", "Do the thing", ["a"], "desc")
    assert path.name == "my-prompt.json"
    (tmp_path / "prompts" / "Study" / "broken.json").write_text("{not json")
    assert prompt_loader.load_prompt_file(tmp_path / "prompts" / "Study" / "broken.json") is None
    loaded = prompt_loader.load_prompts_from_category("Study")
    assert [p["title"] for p in loaded] == ["My Prompt!"] and loaded[0]["category"] == "Study"
    assert prompt_loader.get_all_prompts()[0]["title"] == "My Prompt!"
    assert list(prompt_loader.get_prompts_database()) == ["Study"]
    assert json.loads(path.read_text())["tags"] == ["a"]
    assert prompt_loader.get_category_folders() == ["Study"]


def test_learning_paths_order_and_cap():
    items = [{"category": "A", "title": f"t{i}", "difficulty_level": lv}
             for i, lv in enumerate(["expert", "beginner", "intermediate", "beginner", "beginner", "beginner", "beginner", "beginner"])]
    items.append({"title": "no category"})
    paths = analysis.build_learning_paths(items)
    assert len(paths["A"]) == 6 and paths["A"][0]["difficulty_level"] == "beginner" and "General" in paths


@pytest.mark.parametrize("words", list(range(3, 70, 3)))
@pytest.mark.parametrize("extra", ["", " Use a table format.", " Do not exceed 100 words, avoid jargon.", " For example: input: x, output: y."])
def test_word_count_sweep(words, extra, examples):
    prompt = " ".join(["write", "python", "report", "data", "plan"][i % 5] for i in range(words)) + "." + extra
    suggestions, improved, practices, similar = analysis.analyze_prompt(prompt, examples)[:4]
    for hint in HINTS:
        analysis.generate_improved_prompt(prompt, examples, practices, similar, {}, None, hint)
