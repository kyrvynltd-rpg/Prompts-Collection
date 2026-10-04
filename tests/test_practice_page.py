from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = str(Path(__file__).resolve().parent.parent / "src" / "pages" / "1_Practice.py")


def test_practice_page_scores_attempt():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    assert not at.exception
    at.text_area[0].set_value("You are a statistics tutor. Explain p-values to a first-year student with one everyday example.").run()
    at.button[0].click().run()
    assert not at.exception
    assert any("Score" in m.label for m in at.metric)
    assert at.session_state["progress"]


def test_empty_attempt_warns():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.button[0].click().run()
    assert at.warning
