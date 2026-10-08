"""Checks for the nlp/ public interface (run: python -m pytest nlp/tests -q)."""

import sys
import typing
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import nlp  # noqa: E402
from nlp import extract_skills, load_catalogue, match_skills  # noqa: E402
from nlp.normalise import normalise_text, singularise, skill_key, uk_spelling  # noqa: E402
from nlp.types import (  # noqa: E402
    VALID_METHODS, ExtractedSkill, MatchingMethod, MatchResult, RequiredSkill, StudentSkill,
)

JD = "We need a Junior Data Analyst with SQL, Power BI and Python. Docker is a plus."
STUDENT = [{"skill_id": None, "skill_name": "SQL",
            "proficiency_level": "advanced", "evidence_type": ["project"]}]
REQUIRED = [{"skill_id": None, "skill_name": "SQL", "importance": "required"}]


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue()


# ── Public API ────────────────────────────────────────────────
@pytest.mark.parametrize("bad", ["", "Keyword", "spacy_ner", "fuzzy", None])
def test_invalid_method_raises_value_error(bad):
    with pytest.raises(ValueError):
        extract_skills(JD, method=bad)
    with pytest.raises(ValueError):
        match_skills(STUDENT, REQUIRED, method=bad)


@pytest.mark.parametrize("method", VALID_METHODS)
def test_valid_methods_reach_the_stub(method):
    with pytest.raises(NotImplementedError):
        extract_skills(JD, method=method)
    with pytest.raises(NotImplementedError):
        match_skills(STUDENT, REQUIRED, method=method)


def test_default_method_is_hybrid():
    with pytest.raises(NotImplementedError):
        extract_skills(JD)
    with pytest.raises(NotImplementedError):
        match_skills(STUDENT, REQUIRED)


def test_empty_inputs_return_empty_list():
    assert extract_skills("   \n ") == []
    assert match_skills(STUDENT, []) == []


def test_extract_rejects_non_string_text():
    with pytest.raises(ValueError):
        extract_skills(None)


def test_methods_match_db_check_constraint():
    assert set(VALID_METHODS) == {"keyword", "semantic", "hybrid"}
    assert set(typing.get_args(MatchingMethod)) == set(VALID_METHODS)


def test_type_fields_line_up_with_contract():
    assert set(ExtractedSkill.__annotations__) == {
        "skill_id", "skill_name", "raw_skill_text", "method",
        "confidence_score", "start_char", "end_char"}
    assert set(StudentSkill.__annotations__) == {
        "skill_id", "skill_name", "proficiency_level", "evidence_type"}
    assert set(RequiredSkill.__annotations__) == {"skill_id", "skill_name", "importance"}
    assert set(MatchResult.__annotations__) == {
        "skill_id", "skill_name", "importance", "match_status", "similarity_score",
        "matching_method", "matched_student_skill", "reason"}


def test_public_names_exported():
    for name in ("extract_skills", "match_skills", "load_catalogue", "ExtractedSkill",
                 "StudentSkill", "RequiredSkill", "MatchResult"):
        assert name in nlp.__all__


# ── Skill catalogue ───────────────────────────────────────────
def test_default_catalogue_has_138_skills(catalogue):
    assert len(catalogue) == 138
    assert all(e["skill_id"] is None for e in catalogue)


def test_default_catalogue_is_cached(catalogue):
    assert load_catalogue() is catalogue


@pytest.mark.parametrize("term, expected", [
    ("ReactJS", "React"),
    ("reactjs", "React"),
    ("T-SQL", "SQL"),
    ("PowerBI", "Power BI"),
    ("K8s", "Kubernetes"),
    ("python", "Python"),
])
def test_alias_lookup(catalogue, term, expected):
    assert catalogue.canonical_name(term) == expected
    assert catalogue.lookup(term) == expected


@pytest.mark.parametrize("term, expected", [
    ("Power-BI", "Power BI"),
    ("Node JS", "Node.js"),
    ("data visualization", "Data Visualisation"),
])
def test_normalised_lookup(catalogue, term, expected):
    assert catalogue.lookup(term) == expected


def test_unknown_term_returns_none(catalogue):
    assert catalogue.canonical_name("Underwater basket weaving") is None
    assert catalogue.lookup("Underwater basket weaving") is None


def test_get_entry_by_canonical_name(catalogue):
    entry = catalogue.get("power bi")
    assert entry["skill_name"] == "Power BI"
    assert entry["category"] == "Technical"


@pytest.mark.parametrize("term", ["R", "Go", "Excel", "CV", "REST", "node", "TS"])
def test_ambiguous_aliases_reported(catalogue, term):
    assert catalogue.is_ambiguous(term)


@pytest.mark.parametrize("term", ["R programming", "Golang", "Microsoft Excel", "Python", "RESTful API"])
def test_unambiguous_terms_not_reported(catalogue, term):
    assert not catalogue.is_ambiguous(term)


def test_ambiguous_alias_still_resolves(catalogue):
    assert catalogue.canonical_name("CV") == "Computer Vision"
    assert catalogue.canonical_name("REST") == "REST API"


def test_db_rows_use_real_ids_and_taxonomy_metadata():
    rows = [
        {"skill_id": "11111111-1111-1111-1111-111111111111", "skill_name": "React",
         "category": "Technical", "aliases": ["React.js", "ReactJS"], "description": "UI library"},
        {"skill_id": "22222222-2222-2222-2222-222222222222", "skill_name": "Go",
         "category": "Technical", "aliases": None, "description": None},
        {"skill_id": "33333333-3333-3333-3333-333333333333", "skill_name": "Old Skill",
         "category": "Technical", "aliases": [], "is_active": False},
    ]
    cat = load_catalogue(rows)
    assert len(cat) == 2
    assert cat.skill_id("ReactJS") == "11111111-1111-1111-1111-111111111111"
    assert cat.is_ambiguous("Go")                     # from the taxonomy
    assert cat.canonical_name("Golang") == "Go"       # NULL aliases -> taxonomy aliases
    assert cat.get("Go")["subcategory"] == "Programming Language"
    assert cat.get("Old Skill") is None
    assert load_catalogue() is not cat


def test_alias_claimed_by_two_skills_is_dropped():
    # e.g. the v1 seed listed "AWS" as an alias of Cloud Computing and as a skill
    rows = [
        {"skill_id": "a", "skill_name": "Cloud Computing", "aliases": ["AWS", "Cloud platforms", "Shared"]},
        {"skill_id": "b", "skill_name": "AWS", "aliases": ["Amazon Web Services"]},
        {"skill_id": "c", "skill_name": "Other", "aliases": ["Shared"]},
    ]
    cat = load_catalogue(rows)
    assert cat.canonical_name("AWS") == "AWS"
    assert cat.canonical_name("Shared") is None


def test_bad_rows_raise_value_error():
    with pytest.raises(ValueError):
        load_catalogue([{"skill_id": "x", "skill_name": ""}])
    with pytest.raises(ValueError):
        load_catalogue([{"skill_name": "SQL"}, {"skill_name": "sql"}])
    with pytest.raises(ValueError):
        extract_skills(JD, skills=[{"skill_name": None}])


# ── Normalisation ─────────────────────────────────────────────
def test_normalise_text():
    assert normalise_text("  Power–BI   Developer ") == "power-bi developer"
    assert normalise_text(None) == ""


@pytest.mark.parametrize("variants", [
    ["Power-BI", "PowerBI", "Power BI", "power bi"],
    ["Node.js", "NodeJS", "node js", "Node-JS"],
    ["Data Visualisation", "data visualization", "Data-Visualizations"],
    ["Statistical Modelling", "statistical modeling"],
    ["Unit Testing", "unit-testing"],
])
def test_skill_key_unifies_variants(variants):
    assert len({skill_key(v) for v in variants}) == 1


def test_skill_key_keeps_meaningful_symbols():
    assert skill_key("C++") != skill_key("C")
    assert skill_key("C#") != skill_key("C")
    assert skill_key("CI/CD") == "ci/cd"


@pytest.mark.parametrize("us, uk", [
    ("visualization", "visualisation"),
    ("visualize", "visualise"),
    ("analyze", "analyse"),
    ("analyzing", "analysing"),
    ("modeling", "modelling"),
    ("organizational", "organisational"),
    ("security operations center", "security operations centre"),
    ("analysis", "analysis"),
    ("size", "size"),
])
def test_uk_spelling(us, uk):
    assert uk_spelling(us) == uk


@pytest.mark.parametrize("word, expected", [
    ("skills", "skill"),
    ("dashboards", "dashboard"),
    ("libraries", "library"),
    ("processes", "process"),
    ("analytics", "analytics"),
    ("statistics", "statistics"),
    ("pandas", "pandas"),
    ("kubernetes", "kubernetes"),
    ("nodejs", "nodejs"),
    ("devops", "devops"),
    ("business", "business"),
    ("aws", "aws"),
    ("analysis", "analysis"),
])
def test_singularise(word, expected):
    assert singularise(word) == expected
