import json
from pathlib import Path

from prompt_loader import PROMPTS_DIR

FILES = sorted((Path(PROMPTS_DIR) / "Student Success").glob("*.json"))


def test_pack_size_and_split():
    data = [json.loads(f.read_text(encoding="utf-8")) for f in FILES]
    assert len(data) >= 15
    free = [d for d in data if d["access"] == "free"]
    assert 4 <= len(free) < len(data), "need a free sample and a paid remainder"


def test_each_prompt_has_student_fields():
    for f in FILES:
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["access"] in {"free", "premium"}, f.name
        assert d["integrity_note"].strip(), f.name
        assert d["example_input"].strip(), f.name
        assert "[" in d["prompt"], f"{f.name}: needs a placeholder the student fills"


def test_prompts_do_not_ghostwrite():
    banned = ["write my essay", "write the essay for me", "humanise", "undetectable"]
    for f in FILES:
        text = f.read_text(encoding="utf-8").lower()
        for b in banned:
            assert b not in text, f"{f.name}: contains '{b}'"
