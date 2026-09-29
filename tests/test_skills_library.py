"""Checks for data/skills/skills_library.csv (run: python -m pytest tests/test_skills_library.py -q)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data" / "skills"))
from skills_lib import (  # noqa: E402
    MAX_NAME_LEN, MAX_SKILLS, MIN_SKILLS, VALID_CATEGORIES,
    load_skills, load_v1_skill_names, validate,
)


@pytest.fixture(scope="module")
def rows():
    return load_skills()


def test_skill_names_unique_case_insensitive(rows):
    names = [r["skill_name"].lower() for r in rows]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes


def test_categories_valid(rows):
    bad = {r["skill_name"]: r["category"] for r in rows if r["category"] not in VALID_CATEGORIES}
    assert not bad


def test_no_alias_conflicts(rows):
    names = {r["skill_name"].strip().lower(): r["skill_name"] for r in rows}
    owner = {}
    conflicts = []
    for r in rows:
        for a in r["aliases"] + r["ambiguous_aliases"]:
            key = a.strip().lower()
            if a in r["ambiguous_aliases"] and key == r["skill_name"].lower():
                continue  # e.g. "R": the name itself is flagged as ambiguous
            if key in names:
                conflicts.append(f"{r['skill_name']}: {a!r} is the skill {names[key]!r}")
            if key in owner:
                conflicts.append(f"{a!r}: {owner[key]!r} and {r['skill_name']!r}")
            owner[key] = r["skill_name"]
    assert not conflicts, "\n".join(conflicts)


def test_all_v1_skills_present_unchanged(rows):
    v1 = load_v1_skill_names()
    assert len(v1) == 32
    names = {r["skill_name"] for r in rows}
    assert not [n for n in v1 if n not in names]


def test_skill_count_in_range(rows):
    assert MIN_SKILLS <= len(rows) <= MAX_SKILLS


def test_descriptions_and_name_length(rows):
    assert all(r["description"].strip() for r in rows)
    assert all(len(r["skill_name"]) <= MAX_NAME_LEN for r in rows)


def test_known_conflicts_resolved(rows):
    by_name = {r["skill_name"]: r for r in rows}
    lower = lambda xs: {x.lower() for x in xs}  # noqa: E731
    assert not lower(by_name["SQL"]["aliases"]) & {"mysql", "sqlite", "postgresql"}
    assert not lower(by_name["Linux"]["aliases"]) & {"bash", "shell scripting"}
    assert not lower(by_name["Cloud Computing"]["aliases"]) & {"aws", "azure", "gcp"}
    assert "critical thinking" not in lower(by_name["Problem Solving"]["aliases"])
    assert "presentation skills" not in lower(by_name["Communication"]["aliases"])
    assert not lower(by_name["Project Management"]["aliases"]) & {"agile", "scrum", "kanban"}
    assert "CV" in by_name["Computer Vision"]["ambiguous_aliases"]


def test_validator_reports_nothing(rows):
    assert validate(rows, load_v1_skill_names()) == []
