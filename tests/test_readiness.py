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

from readiness import tier_coverage, tiered_readiness  # noqa: E402


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


def test_every_role_template_required_strong_rest_gap_is_70():
    sql = (ROOT / "database" / "seed_job_role_skills.sql").read_text(encoding="utf-8")
    seed = re.findall(r"^\s*\('([A-Z_]+)',\s*'(?:[^']|'')+',\s*'(required|preferred|bonus)'\)", sql, flags=re.M)
    templates = defaultdict(list)
    for role, importance in seed:
        templates[role].append(row(importance, "strong" if importance == "required" else "gap"))
    assert len(templates) == 10
    assert {role: tiered_readiness(r) for role, r in templates.items()} == {role: 70.0 for role in templates}
