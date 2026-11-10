"""
Job Readiness Score, tiered coverage (backend/readiness.py). No database.

Expected values are worked by hand, as in docs/JOB_READINESS_SCORE.md:
Readiness = 100 x (0.70 C_required + 0.25 C_preferred + 0.05 C_bonus) / (weights of the tiers present).

    python -m pytest tests/test_readiness.py -q
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from readiness import (  # noqa: E402
    STATUS_CREDIT, expected_gain, gain_between, skill_points, tier_coverage, tiered_readiness)


def row(importance, status):
    return {"importance": importance, "match_status": status}


def rows(importance, status, n):
    return [row(importance, status)] * n


DOCS_REQUIRED = [row("required", "strong"), row("required", "developing"), row("required", "gap")]
DOCS_EXAMPLE = DOCS_REQUIRED + [row("preferred", "developing"), row("bonus", "gap")]


def test_docs_example():
    assert tiered_readiness(DOCS_EXAMPLE) == 47.5


def test_docs_example_required_only_is_the_pasted_jd_case():
    assert tiered_readiness(DOCS_REQUIRED) == 50.0


def test_required_strong_preferred_gap_no_bonus_tier():
    assert tiered_readiness(rows("required", "strong", 4) + rows("preferred", "gap", 9)) == 73.68


@pytest.mark.parametrize("required, preferred, bonus", [(1, 1, 1), (6, 16, 13), (10, 8, 9), (50, 200, 300)])
def test_three_tiers_required_strong_rest_gap_is_70_whatever_the_row_count(required, preferred, bonus):
    assert tiered_readiness(rows("required", "strong", required) + rows("preferred", "gap", preferred)
                            + rows("bonus", "gap", bonus)) == 70.0


def test_only_a_preferred_tier_at_coverage_06():
    assert tiered_readiness(rows("preferred", "strong", 3) + rows("preferred", "gap", 2)) == 60.0


def test_all_strong():
    assert tiered_readiness(rows("required", "strong", 3) + rows("preferred", "strong", 5)
                            + rows("bonus", "strong", 2)) == 100.0


def test_all_gap():
    assert tiered_readiness(rows("required", "gap", 3) + rows("preferred", "gap", 5)
                            + rows("bonus", "gap", 2)) == 0.0


def test_empty():
    assert tiered_readiness([]) == 0


@pytest.mark.parametrize("missing", [{}, {"importance": None}])
def test_missing_importance_counts_as_required(missing):
    # Half of a required tier, and all of a preferred tier at 0: 100 x 0.70 x 0.5 / 0.95
    assert tiered_readiness([{"match_status": "strong", **missing}, row("required", "gap"),
                             row("preferred", "gap")]) == 36.84


def test_tier_coverage_is_none_for_an_absent_tier():
    assert tier_coverage(DOCS_REQUIRED + [row("preferred", "developing")]) == {
        "required": 0.5, "preferred": 0.5, "bonus": None}


def earned(rows_):
    points = skill_points(rows_)
    return sum(points[r.get("importance") or "required"] * STATUS_CREDIT[r["match_status"]] for r in rows_)


def test_skill_points_three_tiers():
    assert skill_points(rows("required", "gap", 10) + rows("preferred", "gap", 5) + rows("bonus", "gap", 2)) == pytest.approx(
        {"required": 7.0, "preferred": 5.0, "bonus": 2.5})


def test_skill_points_job_with_a_missing_tier():
    # No bonus tier: the weights of the tiers it has are 0.95, and bonus is not in the answer
    assert skill_points(rows("required", "gap", 2) + rows("preferred", "gap", 1)) == pytest.approx(
        {"required": 100 * .70 / .95 / 2, "preferred": 100 * .25 / .95})


def test_skill_points_required_only_is_the_pasted_jd_case():
    assert skill_points(rows("required", "gap", 4)) == pytest.approx({"required": 25.0})


def test_skill_points_no_rows():
    assert skill_points([]) == {}


@pytest.mark.parametrize("missing", [{}, {"importance": None}])
def test_skill_points_missing_importance_counts_as_required(missing):
    assert skill_points([{"match_status": "gap", **missing}, row("required", "gap")]) == pytest.approx({"required": 50.0})


@pytest.mark.parametrize("hand_made", [
    DOCS_EXAMPLE,
    DOCS_REQUIRED,
    rows("required", "strong", 4) + rows("preferred", "gap", 9),
    rows("required", "developing", 7) + rows("bonus", "strong", 3),
    rows("preferred", "strong", 3) + rows("preferred", "gap", 2),
    rows("required", "strong", 6) + rows("required", "gap", 1) + rows("preferred", "developing", 16)
    + rows("bonus", "gap", 12) + rows("bonus", "strong", 1),
])
def test_points_times_credit_is_the_readiness(hand_made):
    assert earned(hand_made) == pytest.approx(tiered_readiness(hand_made), abs=0.005)


def test_expected_gain():
    assert (expected_gain(7.0, "gap"), expected_gain(7.0, "developing"), expected_gain(7.0, "strong")) == (7.0, 3.5, 0.0)


def test_gain_between_is_never_negative():
    assert gain_between(7.0, "gap", "developing") == 3.5
    assert gain_between(7.0, "gap", "strong") == 7.0
    assert gain_between(7.0, "developing", "developing") == 0
    assert gain_between(7.0, "strong", "developing") == 0


def test_every_role_template_required_strong_rest_gap_is_70():
    sql = (ROOT / "database" / "seed_job_role_skills.sql").read_text(encoding="utf-8")
    seed = re.findall(r"^\s*\('([A-Z_]+)',\s*'(?:[^']|'')+',\s*'(required|preferred|bonus)'\)", sql, flags=re.M)
    templates = defaultdict(list)
    for role, importance in seed:
        templates[role].append(row(importance, "strong" if importance == "required" else "gap"))
    assert len(templates) == 10
    assert {role: tiered_readiness(r) for role, r in templates.items()} == {role: 70.0 for role in templates}
