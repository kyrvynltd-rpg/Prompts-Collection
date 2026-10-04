"""Prompt practice engine: deterministic, offline scoring of a student's prompt against a rubric.

Scoring is heuristic and explained to the user. It checks structure, not truth.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "exercises.json"

# criterion -> (label, regex list, advice when missing)
CRITERIA: dict[str, tuple[str, list[str], str]] = {
    "role": ("Role", [r"\byou are\b", r"\bact as\b", r"\bas (a|an) [a-z]+", r"\bpretend\b", r"\bplay the role\b"],
             "Give the model a role, for example 'You are a statistics tutor'."),
    "task": ("Clear task", [r"\b(explain|tell|summari[sz]e|list|suggest|create|build|write|give|check|compare|ask|score|find|outline|plan|design|draft)\b"],
             "Start with a specific verb that says what you want done."),
    "audience": ("Audience or level", [r"\b(first|second|third)[- ]year\b", r"\bbeginner\b", r"\bstudent\b", r"\bundergraduate\b",
                                        r"\bmasters?\b", r"\bplain language\b", r"\bfor (a|an) [a-z]+\b", r"\bi am (a|an)\b"],
                 "Say who the answer is for or what level you are at."),
    "context": ("Context",
                [r"\b\d+\b", r"\bdeadline\b", r"\bbecause\b", r"\bso that\b", r"\bweakest\b", r"\bmodule\b", r"\bexam"],
                "Add the facts that matter: numbers, dates, subject, what you already tried."),
    "constraints": ("Constraints", [r"\bdo not\b", r"\bdon't\b", r"\bnever\b", r"\bonly\b", r"\bwithout\b", r"\bunder \d+", r"\bat most\b",
                                     r"\bno more than\b", r"\bmaximum\b", r"\bwithin\b"],
                    "Set limits: length, what to avoid, what to use only."),
    "format": ("Output format", [r"\btable\b", r"\bbullet", r"\bnumbered\b", r"\bsteps?\b", r"\bjson\b", r"\bcsv\b", r"\bunder \d+ words\b",
                                  r"\bparagraphs?\b", r"\boutput\b", r"\bheadings?\b"],
               "Say what shape the answer should take, such as a table or 5 bullets."),
    "examples": ("Example or method", [r"\bfor example\b", r"\be\.g\.", r"\bsuch as\b", r"\bone (everyday )?example\b", r"\bstep by step\b",
                                         r"\bone at a time\b", r"\bwait for my\b"],
                 "Add an example or tell the model how to work, such as one step at a time."),
    "verification": ("Checkable and honest", [r"\bverify\b", r"\bcheck\b", r"\bsources?\b", r"\bif you (do not|don't) know\b", r"\bdo not (invent|guess)\b",
                                                r"\bsay so\b", r"\bevidence\b", r"\b(module|university|course) policy\b", r"\bmay be wrong\b"],
                     "Ask for sources or evidence, and tell the model to say when it is unsure."),
}

RED_FLAGS: list[tuple[str, str]] = [
    (r"\bwrite (my|the) (whole )?(essay|dissertation|assignment|report)( for me)?\b", "Asking for the assessed work to be written for you can breach academic integrity rules."),
    (r"\b(without|so)( it)? (gets?|being) detected\b|\bundetectable\b|\bbypass (turnitin|detection)", "Do not ask for help to avoid AI detection. Be honest about how you used AI."),
    (r"\binvent (a )?(references|sources|citations)\b|\bmake up (references|sources)\b", "Models can invent sources. Ask for search strategies instead."),
]


@dataclass
class Result:
    score: int
    level: str
    checks: dict[str, bool]
    advice: list[str]
    flags: list[str]
    missing_terms: list[str] = field(default_factory=list)


def _hit(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


_NEGATION = re.compile(r"(do not|don't|never|must not|won't|without)\s+(\w+\s+){0,2}$", re.IGNORECASE)


def _unnegated(pattern: str, text: str) -> bool:
    """True if the pattern matches somewhere that is not directly preceded by a negation."""
    for m in re.finditer(pattern, text, re.IGNORECASE):
        if not _NEGATION.search(text[max(0, m.start() - 25):m.start()]):
            return True
    return False


def load_exercises() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def level_for(score: int) -> str:
    if score >= 90:
        return "Expert"
    if score >= 70:
        return "Solid"
    if score >= 40:
        return "Developing"
    return "Starter"


def score_prompt(text: str, exercise: dict) -> Result:
    """Score a student prompt. Weighted: focus criteria 70%, task-specific terms 30% (if any)."""
    text = (text or "").strip()
    focus = exercise["focus"]
    checks = {c: bool(text) and _hit(text, CRITERIA[c][1]) for c in focus}
    # A bare one-liner cannot really contain a role or context even if a keyword slips in.
    if len(text.split()) < 6:
        checks = {c: False for c in focus}

    terms = exercise.get("must_mention", [])
    missing = [t.split("|")[0] for t in terms if not _hit(text, [t])]
    term_ratio = 1.0 if not terms else (len(terms) - len(missing)) / len(terms)
    focus_ratio = sum(checks.values()) / len(focus)
    raw = focus_ratio * (0.7 if terms else 1.0) + (term_ratio * 0.3 if terms else 0)
    flags = [msg for pat, msg in RED_FLAGS if _unnegated(pat, text)]
    score = round(raw * 100)
    if flags:
        score = min(score, 40)
    advice = [CRITERIA[c][2] for c, ok in checks.items() if not ok]
    if missing:
        advice.append("Mention the details that matter for this task: " + ", ".join(missing) + ".")
    return Result(score=score, level=level_for(score), checks=checks, advice=advice, flags=flags, missing_terms=missing)


def criterion_label(key: str) -> str:
    return CRITERIA[key][0]
