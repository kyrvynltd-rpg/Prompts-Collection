import pytest

from practice import load_exercises, score_prompt

DATA = load_exercises()
EXERCISES = DATA["exercises"]


def test_exercise_data_valid():
    ids = [e["id"] for e in EXERCISES]
    assert len(ids) == len(set(ids)) >= 10
    levels = {lv["id"] for lv in DATA["levels"]}
    for e in EXERCISES:
        assert e["level"] in levels
        for k in ("title", "scenario", "weak_prompt", "model_prompt", "tip", "focus"):
            assert e[k], (e["id"], k)


@pytest.mark.parametrize("ex", EXERCISES, ids=lambda e: e["id"])
def test_model_answer_scores_high(ex):
    r = score_prompt(ex["model_prompt"], ex)
    assert r.score >= 85, (ex["id"], r)
    assert not r.flags


@pytest.mark.parametrize("ex", EXERCISES, ids=lambda e: e["id"])
def test_weak_prompt_scores_low(ex):
    r = score_prompt(ex["weak_prompt"], ex)
    assert r.score <= 40, (ex["id"], r.score)
    assert r.advice


def test_empty_prompt():
    r = score_prompt("", EXERCISES[0])
    assert r.score == 0 and r.level == "Starter"


def test_integrity_red_flag_caps_score():
    ex = EXERCISES[1]
    r = score_prompt("You are an expert. Write my essay for me, 2000 words, as a table, do not stop, for example in plain language.", ex)
    assert r.flags and r.score <= 40


def test_more_detail_scores_higher():
    ex = next(e for e in EXERCISES if e["id"] == "e4")
    low = score_prompt("Make me a revision plan for my exams.", ex).score
    high = score_prompt("Create a revision plan for 3 exams over 4 weeks, 4 hours a day, only weekdays. Output a table by week.", ex).score
    assert high > low


def test_negated_phrase_not_flagged():
    ex = EXERCISES[1]
    r = score_prompt("You are a tutor. Do not write my essay, plan it for 2,000 words only, as bullet points, for example by section.", ex)
    assert not r.flags
