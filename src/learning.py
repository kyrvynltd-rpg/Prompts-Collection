"""Structured learning modules with deterministic, explainable grading, and progress tracking.

A module has lessons and exercises. A learner writes a prompt; each exercise has weighted checks (keyword, regex,
length). Grading is local and instant and returns a score plus per-check feedback, so there is no model call, no
cost and no data leaving the app. It rewards structure, not length or luck.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from db import Database

MODULES_DIR = Path(__file__).resolve().parent.parent / "data" / "modules"
MAX_PROMPT_CHARS = 4000


@dataclass(frozen=True)
class CheckResult:
    label: str
    passed: bool
    weight: int
    hint: str


@dataclass(frozen=True)
class Grade:
    score: int  # 0-100
    passed: bool
    checks: list[CheckResult]

    @property
    def missing_hints(self) -> list[str]:
        return [c.hint for c in self.checks if not c.passed]


def load_modules(directory: Path = MODULES_DIR) -> list[dict[str, Any]]:
    modules = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]
    return sorted(modules, key=lambda m: (m["level"], m["id"]))


def exercise_ids(modules: list[dict[str, Any]]) -> list[str]:
    return [e["id"] for m in modules for e in m["exercises"]]


def _run_check(check: dict[str, Any], text: str) -> bool:
    kind = check["type"]
    low = text.lower()
    if kind == "contains_any":
        return any(t.lower() in low for t in check["terms"])
    if kind == "count_at_least":
        return sum(low.count(t.lower()) for t in check["terms"]) >= check.get("n", 1)
    if kind == "regex":
        return re.search(check["pattern"], text, re.IGNORECASE) is not None
    if kind == "min_words":
        return len(text.split()) >= check["n"]
    if kind == "max_words":
        return len(text.split()) <= check["n"]
    raise ValueError(f"unknown check type {kind!r}")


def grade(exercise: dict[str, Any], text: str) -> Grade:
    text = (text or "")[:MAX_PROMPT_CHARS]
    results = [CheckResult(c["label"], _run_check(c, text), int(c.get("weight", 1)), c.get("hint", "")) for c in exercise["checks"]]
    total = sum(r.weight for r in results) or 1
    score = round(100 * sum(r.weight for r in results if r.passed) / total)
    return Grade(score=score, passed=score >= exercise.get("pass_mark", 70), checks=results)


class ProgressStore:
    def __init__(self, db: Database):
        self.db = db

    def record(self, user_id: str, exercise_id: str, score: int, passed: bool, now: float | None = None) -> None:
        now_i = int(now if now is not None else time.time())
        row = self.db.one("SELECT best_score, attempts, passed FROM progress WHERE user_id=? AND exercise_id=?", (user_id, exercise_id))
        if row:
            self.db.execute(
                "UPDATE progress SET best_score=?, attempts=?, passed=?, updated_at=? WHERE user_id=? AND exercise_id=?",
                (max(row[0], score), row[1] + 1, int(bool(row[2]) or passed), now_i, user_id, exercise_id),
            )
        else:
            self.db.execute(
                "INSERT INTO progress (user_id, exercise_id, best_score, attempts, passed, updated_at) VALUES (?,?,?,?,?,?)",
                (user_id, exercise_id, score, 1, int(passed), now_i),
            )
        self.db.commit()

    def for_user(self, user_id: str) -> dict[str, dict[str, int]]:
        rows = self.db.all("SELECT exercise_id, best_score, attempts, passed FROM progress WHERE user_id=?", (user_id,))
        return {r[0]: {"best_score": r[1], "attempts": r[2], "passed": r[3]} for r in rows}


def module_summary(module: dict[str, Any], progress: dict[str, dict[str, int]]) -> dict[str, Any]:
    ids = [e["id"] for e in module["exercises"]]
    done = sum(1 for i in ids if progress.get(i, {}).get("passed"))
    scores = [progress[i]["best_score"] for i in ids if i in progress]
    return {"id": module["id"], "title": module["title"], "done": done, "total": len(ids),
            "percent": round(100 * done / len(ids)) if ids else 0,
            "average_best": round(sum(scores) / len(scores)) if scores else 0}


def overall_percent(modules: list[dict[str, Any]], progress: dict[str, dict[str, int]]) -> int:
    ids = exercise_ids(modules)
    return round(100 * sum(1 for i in ids if progress.get(i, {}).get("passed")) / len(ids)) if ids else 0


def certificate_ready(module: dict[str, Any], progress: dict[str, dict[str, int]]) -> bool:
    return module_summary(module, progress)["percent"] == 100
