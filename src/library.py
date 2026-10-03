"""Pure filtering and ranking helpers for browsing the prompt library (no Streamlit imports)."""
from __future__ import annotations

import re

STUDENT_CATEGORY = "Student Success"


def access_of(prompt: dict) -> str:
    """Prompts are free unless explicitly marked premium."""
    return "premium" if prompt.get("access") == "premium" else "free"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _score(prompt: dict, tokens: list[str]) -> int:
    if not tokens:
        return 1
    title = prompt.get("title", "").lower()
    tags = " ".join(prompt.get("tags", [])).lower()
    desc = prompt.get("description", "").lower()
    body = prompt.get("prompt", "").lower()
    total = 0
    for t in tokens:
        hit = 0
        if t in title:
            hit += 5
        if t in tags:
            hit += 3
        if t in desc:
            hit += 2
        if t in body:
            hit += 1
        if hit == 0:
            return 0  # every search word must match somewhere
        total += hit
    return total


def search_prompts(prompts: list[dict], query: str = "", category: str = "All", difficulty: str = "Any",
                   access: str = "Any", tags: list[str] | None = None) -> list[dict]:
    tokens = _tokens(query)
    out = []
    for p in prompts:
        if category not in ("All", "All Categories") and p.get("category") != category:
            continue
        if difficulty != "Any" and p.get("difficulty_level") != difficulty:
            continue
        if access != "Any" and access_of(p) != access:
            continue
        if tags and not set(tags) <= set(p.get("tags", [])):
            continue
        s = _score(p, tokens)
        if s:
            out.append((s, p))
    out.sort(key=lambda sp: (-sp[0], sp[1].get("title", "")))
    return [p for _, p in out]


def category_counts(prompts: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in prompts:
        counts[p.get("category", "Other")] = counts.get(p.get("category", "Other"), 0) + 1
    return dict(sorted(counts.items()))
