from pathlib import Path

from streamlit.testing.v1 import AppTest

from library import access_of, search_prompts
from prompt_loader import get_all_prompts

PAGE = str(Path(__file__).resolve().parent.parent / "src" / "pages" / "2_Library.py")
PROMPTS = get_all_prompts()


def test_search_title_ranks_first():
    r = search_prompts(PROMPTS, "essay planner")
    assert r and r[0]["title"] == "Essay Planner"


def test_all_words_must_match():
    assert search_prompts(PROMPTS, "essay zzzzqqq") == []


def test_filters():
    r = search_prompts(PROMPTS, category="Student Success", access="free")
    assert r and all(p["category"] == "Student Success" and access_of(p) == "free" for p in r)
    assert all(p["difficulty_level"] == "beginner" for p in search_prompts(PROMPTS, difficulty="beginner"))


def test_default_access_is_free():
    assert access_of({"title": "x"}) == "free"
    assert access_of({"access": "premium"}) == "premium"


def test_library_page_renders_and_searches():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    assert not at.exception
    at.text_input[0].set_value("debugging").run()
    assert not at.exception
    assert any("prompts" in c.value for c in at.caption)
