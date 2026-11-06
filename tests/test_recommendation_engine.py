"""
The pure parts of recommendation/engine.py: the order of the skills, what a resource is
worth, and first_steps. No database.

    python -m pytest tests/test_recommendation_engine.py -q
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recommendation.engine import (  # noqa: E402
    cost_tier, first_steps, gain_if_completed, priority_key, skills_to_do, with_gains)

CREATED = datetime(2026, 11, 6, 12, 0)
BEFORE, AFTER = CREATED - timedelta(days=1), CREATED + timedelta(days=1)


def row(name, importance, status):
    return {"skill_id": name, "skill_name": name, "category": "Technical", "match_status": status,
            "similarity_score": 0, "importance": importance}


def resource(rid, cost="Free", difficulty="beginner", kind="course"):
    return {"resource_id": rid, "resource_title": rid, "resource_type": kind, "cost": cost,
            "cost_tier": cost_tier(cost), "difficulty": difficulty}


def skill(name="S", gap_type="gap", importance="required", points=10.0):
    return {"skill_id": name, "skill_name": name, "category": "Technical", "gap_type": gap_type,
            "importance": importance, "points": points, "expected_gain": points}


def steps(skills, resources, completed=()):
    by_skill = {s["skill_id"]: with_gains(resources.get(s["skill_id"], []), s) for s in skills}
    return first_steps(skills, by_skill, list(completed), CREATED)


def done(rid, skill_id="S", at=BEFORE):
    return {"resource_id": rid, "skill_id": skill_id, "completed_at": at}


# ── Order ─────────────────────────────────────────────────────
def test_order_is_importance_then_gap_then_name():
    rows = [row("Zig", "required", "gap"), row("Ada", "required", "developing"), row("Bash", "preferred", "gap"),
            row("Awk", "preferred", "developing"), row("C", "bonus", "gap"), row("Dart", "bonus", "developing"),
            row("Excel", "required", "gap"), row("Go", "required", "strong")]
    assert [s["skill_name"] for s in skills_to_do(rows)] == ["Excel", "Zig", "Ada", "Bash", "Awk", "C", "Dart"]


def test_required_before_preferred_before_bonus():
    keys = [priority_key(skill("A", "developing", "required")), priority_key(skill("A", "gap", "preferred")),
            priority_key(skill("A", "gap", "bonus"))]
    assert keys == sorted(keys)


def test_gap_before_developing_within_a_tier():
    assert priority_key(skill("Z", "gap")) < priority_key(skill("A", "developing"))


def test_name_ignores_case():
    assert priority_key(skill("dbt")) < priority_key(skill("Excel"))


def test_points_count_the_strong_rows_too():
    rows = [row("A", "required", "gap"), row("B", "required", "strong"), row("C", "required", "strong"),
            row("D", "required", "strong")]
    assert skills_to_do(rows)[0]["expected_gain"] == 25.0


def test_expected_gain_of_a_developing_skill_is_half():
    assert skills_to_do([row("A", "required", "developing"), row("B", "required", "gap")])[0]["expected_gain"] == 50.0


def test_gaps_only():
    rows = [row("A", "required", "developing"), row("B", "required", "gap")]
    assert [s["skill_name"] for s in skills_to_do(rows, include_developing=False)] == ["B"]


def test_no_rows():
    assert skills_to_do([]) == []


# ── What completing a resource adds ───────────────────────────
@pytest.mark.parametrize("gap_type, difficulty, kind, gain", [
    ("gap", "beginner", "course", 5.0),           # Gap + beginner course = half
    ("gap", "beginner", "workshop", 5.0),
    ("gap", "beginner", "project", 10.0),         # Gap + beginner project = all
    ("gap", "beginner", "certification", 10.0),
    ("gap", "beginner", "internship", 10.0),
    ("gap", "beginner", "competition", 10.0),     # counts as a project
    ("gap", "intermediate", "course", 10.0),
    ("gap", "advanced", "course", 10.0),
    ("developing", "beginner", "course", 0),      # Developing + beginner course = nothing
    ("developing", "intermediate", "course", 5.0),   # Developing + intermediate course = half
    ("developing", "beginner", "project", 5.0),
    ("gap", None, "course", 5.0),                 # a missing difficulty counts as beginner
    ("developing", None, "course", 0),
    ("gap", None, "project", 10.0),
    ("gap", "beginner", "unknown", 5.0),          # an unknown type gives coursework
])
def test_gain_if_completed(gap_type, difficulty, kind, gain):
    assert gain_if_completed(10.0, gap_type, {"difficulty": difficulty, "resource_type": kind}) == gain


def test_gain_is_rounded_to_one_decimal():
    assert gain_if_completed(11.67, "gap", {"difficulty": "beginner", "resource_type": "course"}) == 5.8


def test_with_gains_does_not_change_the_resources():
    original = [resource("r")]
    assert with_gains(original, skill())[0]["gain_if_completed"] == 5.0
    assert "gain_if_completed" not in original[0]


# ── first_steps ───────────────────────────────────────────────
def test_no_skills():
    assert steps([], {}) == []


def test_fewer_than_three_skills():
    assert [s["skill_name"] for s in steps([skill("A"), skill("B")], {"A": [resource("a")], "B": [resource("b")]})] == ["A", "B"]


def test_takes_the_first_three_in_order():
    skills = [skill(n) for n in "ABCD"]
    got = steps(skills, {n: [resource(n)] for n in "ABCD"})
    assert [s["skill_name"] for s in got] == ["A", "B", "C"]


def test_item_fields():
    got = steps([skill("A", "developing", "preferred", points=4.0)],
                {"A": [resource("a", difficulty="intermediate")]})[0]
    assert {k: got[k] for k in ("skill_id", "skill_name", "category", "gap_type", "importance", "expected_gain")} == {
        "skill_id": "A", "skill_name": "A", "category": "Technical", "gap_type": "developing",
        "importance": "preferred", "expected_gain": 4.0}
    assert got["resource"]["resource_id"] == "a" and got["resource"]["gain_if_completed"] == 2.0


def test_uses_a_resource_outside_the_three_listed():
    resources = [resource(f"course{i}") for i in range(3)] + [resource("project", kind="project")]
    assert steps([skill()], {"S": resources})[0]["resource"]["resource_id"] == "project"


def test_a_completed_resource_is_not_picked():
    resources = [resource("project", kind="project"), resource("course")]
    got = steps([skill()], {"S": resources}, [done("project")])
    assert got[0]["resource"]["resource_id"] == "course"


def test_a_skill_with_only_completed_resources_is_skipped():
    assert steps([skill()], {"S": [resource("a")]}, [done("a")]) == []


def test_a_skill_with_a_resource_completed_after_the_assessment_is_skipped():
    skills = [skill("A"), skill("B")]
    resources = {"A": [resource("a1"), resource("a2")], "B": [resource("b")]}
    got = steps(skills, resources, [done("a1", "A", AFTER)])
    assert [s["skill_name"] for s in got] == ["B"]


def test_a_resource_completed_before_the_assessment_does_not_skip_the_skill():
    resources = {"A": [resource("a1"), resource("a2")]}
    got = steps([skill("A")], resources, [done("a1", "A", BEFORE)])
    assert got[0]["resource"]["resource_id"] == "a2"


def test_a_paid_resource_is_not_picked_over_a_free_one_that_also_adds_points():
    # The paid project is worth more, but the free course adds points too
    resources = [resource("course"), resource("paid", cost="$150 USD", kind="project")]
    assert steps([skill()], {"S": resources})[0]["resource"]["resource_id"] == "course"


def test_free_to_learn_counts_as_free():
    resources = [resource("audit", cost="Free to audit", kind="project"), resource("paid", cost="$150 USD", kind="project")]
    assert steps([skill()], {"S": resources})[0]["resource"]["resource_id"] == "audit"


def test_a_paid_resource_is_picked_when_no_free_one_adds_points():
    resources = [resource("course"), resource("paid", cost="$150 USD", kind="certification")]
    got = steps([skill(gap_type="developing")], {"S": resources})
    assert got[0]["resource"]["resource_id"] == "paid"


def test_a_paid_resource_is_picked_when_there_is_no_free_one():
    assert steps([skill()], {"S": [resource("paid", cost="Free trial")]})[0]["resource"]["resource_id"] == "paid"


def test_highest_gain_wins_among_the_free_ones():
    resources = [resource("course"), resource("project", kind="project")]
    assert steps([skill()], {"S": resources})[0]["resource"]["resource_id"] == "project"


def test_ties_keep_the_existing_order():
    resources = [resource("first", kind="project"), resource("second", kind="project")]
    assert steps([skill()], {"S": resources})[0]["resource"]["resource_id"] == "first"


def test_a_skill_where_nothing_adds_points_is_skipped():
    skills = [skill("A", "developing"), skill("B")]
    got = steps(skills, {"A": [resource("a")], "B": [resource("b")]})
    assert [s["skill_name"] for s in got] == ["B"]


def test_a_skill_with_no_resources_is_skipped():
    assert [s["skill_name"] for s in steps([skill("A"), skill("B")], {"B": [resource("b")]})] == ["B"]
