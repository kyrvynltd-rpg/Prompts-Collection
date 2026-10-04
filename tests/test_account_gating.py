from pathlib import Path

from streamlit.testing.v1 import AppTest

from entitlements import issue_code

SRC = Path(__file__).resolve().parent.parent / "src" / "pages"
SECRET = "z" * 32


def _unlock(at):
    [b for b in at.button if b.label == "Unlock with code"][0].click().run()


def test_account_page_rejects_bad_code(monkeypatch):
    monkeypatch.setenv("ENTITLEMENT_SECRET", SECRET)
    at = AppTest.from_file(str(SRC / "3_Account.py"), default_timeout=60).run()
    at.text_input(key="access_code").set_value("PL1.bad.code").run()
    _unlock(at)
    assert at.error and "entitlement" not in at.session_state


def test_account_page_accepts_valid_code(monkeypatch):
    monkeypatch.setenv("ENTITLEMENT_SECRET", SECRET)
    code = issue_code(SECRET, "a@b.co", "student", 4_000_000_000)
    at = AppTest.from_file(str(SRC / "3_Account.py"), default_timeout=60).run()
    at.text_input(key="access_code").set_value(code).run()
    _unlock(at)
    assert at.session_state["entitlement"].plan == "student"


def test_no_secret_means_locked(monkeypatch):
    monkeypatch.delenv("ENTITLEMENT_SECRET", raising=False)
    at = AppTest.from_file(str(SRC / "3_Account.py"), default_timeout=60).run()
    at.text_input(key="access_code").set_value("PL1.a.b").run()
    _unlock(at)
    assert at.error and "entitlement" not in at.session_state


def test_library_hides_premium_text_when_locked():
    at = AppTest.from_file(str(SRC / "2_Library.py"), default_timeout=60).run()
    at.text_input(key="lib_query").set_value("referencing checker").run()
    assert not at.exception
    assert any("Premium prompt" in w.value for w in at.warning)
    full = "never invent authors, titles, page numbers"
    assert not any(full in c.value for c in at.code)


def test_new_pages_render_and_lock_for_anonymous():
    for page, text in (("4_Learn.py", None), ("5_Workspace.py", "Sign in"), ("6_AI_Feedback.py", "Sign in"), ("3_Account.py", None)):
        at = AppTest.from_file(str(SRC / page), default_timeout=60).run()
        assert not at.exception, page
        if text:
            assert any(text in i.value for i in at.info), page


def test_learn_page_locks_paid_modules_for_free_visitors():
    at = AppTest.from_file(str(SRC / "4_Learn.py"), default_timeout=60).run()
    assert sum("module. Upgrade" in w.value for w in at.warning) == 4  # m2-m4 need Plus, m5 needs Pro; m1 is free
    assert any("🔒" in e.label for e in at.expander)
