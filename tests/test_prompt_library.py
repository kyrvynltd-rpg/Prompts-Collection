"""Schema and integrity checks for the prompt library."""
import json
from pathlib import Path

import pytest

from prompt_loader import PROMPTS_DIR, get_all_prompts, get_category_folders

REQUIRED = ["title", "prompt", "tags", "description", "difficulty_level", "time_estimate", "output_format"]
DIFFICULTY = {"beginner", "intermediate", "expert"}
TIME = {"quick", "moderate", "thorough"}
FILES = sorted(Path(PROMPTS_DIR).glob("*/*.json"))


def test_library_not_empty():
    assert len(FILES) >= 100
    assert len(get_category_folders()) >= 12


@pytest.mark.parametrize("path", FILES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_prompt_file_valid(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in REQUIRED:
        assert data.get(key), f"{path.name}: missing {key}"
    assert data["difficulty_level"] in DIFFICULTY
    assert data["time_estimate"] in TIME
    assert isinstance(data["tags"], list) and data["tags"]
    assert len(data["prompt"].split()) >= 20, "prompt text too short to be useful"


def test_titles_unique_per_category():
    seen = {}
    for p in get_all_prompts():
        key = (p["category"], p["title"].strip().lower())
        assert key not in seen, f"duplicate title {key}"
        seen[key] = True


def test_related_prompts_resolve():
    slugs = {f.stem for f in FILES}
    for f in FILES:
        rel = json.loads(f.read_text(encoding="utf-8")).get("related_prompts", {})
        for group in ("after_this", "before_this"):
            for slug in rel.get(group, []):
                assert slug in slugs, f"{f.name}: unknown related prompt {slug}"


def test_no_secrets_in_prompts():
    import re
    pattern = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})")
    for f in FILES:
        assert not pattern.search(f.read_text(encoding="utf-8")), f.name
