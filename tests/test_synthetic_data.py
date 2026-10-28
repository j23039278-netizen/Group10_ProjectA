"""Checks for data/generate_synthetic_data.py (run: python -m pytest tests/test_synthetic_data.py -q)."""

import csv
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("faker")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
from generate_synthetic_data import (  # noqa: E402
    BLOCKED_NAMES, BUSINESS_ROLE_ORDER, ROLE_WEIGHTS, ROLES, generate, name_key,
)

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "output"


@pytest.fixture(scope="module")
def dataset():
    return generate(5000, 42)


def test_names_unique_5000_seed_42(dataset):
    users = dataset[0]
    assert len(users) == 5000
    keys = {name_key(u["full_name"]) for u in users}
    assert len(keys) == 5000
    assert not keys & {name_key(n) for n in BLOCKED_NAMES}


def test_same_seed_same_output(dataset):
    assert generate(5000, 42) == dataset


def student_number(email):
    return int(re.match(r"student(\d+)@", email).group(1))


def test_courses_and_roles_follow_the_database_rules(dataset):
    """N mod 3 -> course and N mod 4 -> Business role, as in migrate_existing_db.sql"""
    users, profiles, _, _, _, meta = dataset
    email = {u["user_id"]: u["email"] for u in users}
    assert Counter(m["course"] for m in meta) == {"CS": 1667, "BUSINESS": 1667, "ICT": 1666}
    for p, m in zip(profiles, meta):
        n = student_number(email[p["user_id"]])
        assert m["course"] == {1: "CS", 2: "BUSINESS", 0: "ICT"}[n % 3]
        if m["course"] == "BUSINESS":
            assert p["target_role"] == BUSINESS_ROLE_ORDER[n % 4]
            assert p["programme"].startswith("Bachelor of Business")
        else:
            assert p["target_role"] in ROLE_WEIGHTS


def test_business_students_hold_business_skills(dataset):
    _, profiles, skills, _, _, meta = dataset
    business = {m["profile_id"]: m["target_role"] for m in meta if m["course"] == "BUSINESS"}
    held = Counter()
    for s in skills:
        role = business.get(s["profile_id"])
        if role:
            held[s["skill_name"] in ROLES[role]["core"] + ROLES[role]["secondary"]] += 1
    assert held[True] / sum(held.values()) > 0.6      # mostly the role's own skills
    coverage = {a: [m["core_coverage_pct"] for m in meta if m["course"] == "BUSINESS" and m["archetype"] == a]
                for a in ("strong", "average", "weak")}
    mean = {a: sum(v) / len(v) for a, v in coverage.items()}
    assert mean["strong"] > mean["average"] > mean["weak"]


def test_committed_output_is_current(dataset):
    """data/output/ was regenerated after the last generator change"""
    with open(OUTPUT / "students_meta.csv", newline="", encoding="utf-8") as f:
        committed = list(csv.DictReader(f))
    assert [m["profile_id"] for m in committed] == [m["profile_id"] for m in dataset[5]]
    assert ([(m["target_role"], m["course"]) for m in committed]
            == [(m["target_role"], m["course"]) for m in dataset[5]])
