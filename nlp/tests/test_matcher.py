"""Checks for match_skills(): the S2-12-01 rules, S2-12-02 cases (boundary
values, missing skills, weak matches, word traps) and S2-11-02 readiness on
representative synthetic students.

Run all:          python -m pytest nlp/tests -q
Skip model tests: python -m pytest nlp/tests -q -m "not model"

Tests without the model replace matcher.similarity_matrix with a table of
made-up similarities (fixture `similarity`).
"""

import csv
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from nlp import config, load_catalogue, match_skills, matcher  # noqa: E402
from nlp.types import VALID_METHODS, MatchResult  # noqa: E402

model = pytest.mark.model
MATCH, RELATED = config.MATCH_THRESHOLD, config.RELATED_THRESHOLD


def student(name, level="intermediate", evidence=(), skill_id=None):
    return {"skill_id": skill_id, "skill_name": name, "proficiency_level": level,
            "evidence_type": list(evidence)}


def required(name, importance="required", skill_id=None):
    return {"skill_id": skill_id, "skill_name": name, "importance": importance}


@pytest.fixture
def similarity(monkeypatch):
    """Made-up similarities: table[(required name, student name)], 0.0 when absent.
    calls records the required names each similarity_matrix() call was asked for."""
    fake = SimpleNamespace(table={}, calls=[])

    def similarity_matrix(required_names, student_names, catalogue):
        fake.calls.append(list(required_names))
        return [[fake.table.get((r, s), 0.0) for s in student_names] for r in required_names]

    monkeypatch.setattr(matcher, "similarity_matrix", similarity_matrix)
    return fake


# ── Same skill (keyword) ──────────────────────────────────────
def test_keyword_same_skill_by_name_alias_and_spelling():
    students = [student("Power BI"), student("Data Visualisation"), student("Node.js")]
    reqs = [required("PowerBI"), required("Data Visualization"), required("NodeJS"), required("Docker")]
    res = match_skills(students, reqs, "keyword")
    assert [r["match_status"] for r in res] == ["strong", "strong", "strong", "gap"]
    assert [r["matched_student_skill"] for r in res] == ["Power BI", "Data Visualisation", "Node.js", None]
    assert [r["similarity_score"] for r in res] == [1.0, 1.0, 1.0, 0.0]


def test_skill_id_decides_when_both_sides_have_one():
    def status(s, r):
        return match_skills([s], [r], "keyword")[0]["match_status"]
    assert status(student("SQL", skill_id="id-1"), required("Structured Query Language", skill_id="id-1")) == "strong"
    assert status(student("SQL", skill_id="id-1"), required("SQL", skill_id="id-2")) == "gap"
    assert status(student("SQL", skill_id="id-1"), required("T-SQL")) == "strong"     # id on one side: name


def test_keyword_method_never_uses_similarity(similarity):
    similarity.table[("Azure", "AWS")] = 0.99
    [r] = match_skills([student("AWS")], [required("Azure")], "keyword")
    assert r["match_status"] == "gap"
    assert similarity.calls == []


# ── Decision table ────────────────────────────────────────────
@pytest.mark.parametrize("method", VALID_METHODS)
@pytest.mark.parametrize("level, evidence, expected", [
    ("advanced", [], "strong"),
    ("intermediate", [], "strong"),
    ("beginner", ["project"], "strong"),
    ("beginner", ["certification"], "strong"),
    ("beginner", ["internship"], "strong"),
    ("beginner", ["coursework", "project"], "strong"),
    ("beginner", ["coursework"], "developing"),        # rule C: coursework alone is not enough
    ("beginner", [], "developing"),
    ("intermediate", ["coursework"], "strong"),
])
def test_same_skill_rules(similarity, method, level, evidence, expected):
    [r] = match_skills([student("SQL", level, evidence)], [required("SQL")], method)
    assert (r["match_status"], r["similarity_score"], r["matched_student_skill"]) == (expected, 1.0, "SQL")


@pytest.mark.parametrize("method", ["semantic", "hybrid"])
@pytest.mark.parametrize("sim, level, evidence, expected", [
    (1.0, "beginner", [], "developing"),
    (1.0, "advanced", ["project"], "developing"),    # rule A: a different skill is never Strong
    (MATCH, "intermediate", [], "developing"),
    (MATCH, "beginner", ["project"], "developing"),
    (MATCH, "beginner", [], "developing"),
    (MATCH - 0.001, "advanced", ["project"], "developing"),
    (MATCH - 1e-6, "advanced", ["project"], "developing"),
    (RELATED, "advanced", [], "developing"),
    (RELATED, "beginner", [], "developing"),
    (RELATED - 0.001, "advanced", ["project"], "gap"),
    (RELATED - 1e-6, "advanced", [], "gap"),
    (0.0, "advanced", ["project"], "gap"),
])
def test_similarity_boundaries(similarity, method, sim, level, evidence, expected):
    similarity.table[("Azure", "AWS")] = sim
    [r] = match_skills([student("AWS", level, evidence)], [required("Azure")], method)
    assert r["match_status"] == expected
    if expected == "gap":
        assert (r["similarity_score"], r["matched_student_skill"]) == (0.0, None)
    else:
        assert r["matched_student_skill"] == "AWS"
        assert sim - 0.001 - 1e-9 < r["similarity_score"] <= sim + 1e-9
        assert (r["similarity_score"] >= MATCH) == (sim >= MATCH)    # stored score explains the status


def test_score_is_cut_to_three_decimals(similarity):
    similarity.table[("Azure", "AWS")] = MATCH - 0.0004              # e.g. 0.5996
    [r] = match_skills([student("AWS")], [required("Azure")], "semantic")
    assert r["similarity_score"] == round(MATCH - 0.001, 3)
    assert r["match_status"] == "developing"


# ── Which student skill decides ───────────────────────────────
def test_hybrid_uses_similarity_only_for_unmatched_skills(similarity):
    similarity.table[("SQL", "MySQL")] = 0.95
    students = [student("SQL", "beginner"), student("MySQL", "advanced", ["project"])]
    [r] = match_skills(students, [required("SQL")], "hybrid")
    assert (r["match_status"], r["matched_student_skill"]) == ("developing", "SQL")
    assert similarity.calls == []
    match_skills(students, [required("SQL"), required("PostgreSQL")], "hybrid")
    assert similarity.calls == [["PostgreSQL"]]


def test_semantic_takes_the_most_similar_student_skill(similarity):
    similarity.table.update({("SQL", "MySQL"): 0.95, ("Azure", "AWS"): 0.55, ("Azure", "GCP"): 0.65})
    students = [student("SQL", "beginner"), student("MySQL", "advanced", ["project"]),
                student("AWS", "advanced", ["certification"]), student("GCP", "beginner")]
    sql, azure = match_skills(students, [required("SQL"), required("Azure")], "semantic")
    assert (sql["matched_student_skill"], sql["match_status"]) == ("SQL", "developing")      # 1.0 > 0.95
    assert (azure["matched_student_skill"], azure["match_status"]) == ("GCP", "developing")  # 0.65 > 0.55


def test_similarity_ties_go_to_the_better_backed_skill(similarity):
    similarity.table.update({("Azure", "AWS"): 0.65, ("Azure", "GCP"): 0.65})
    students = [student("GCP", "beginner"), student("AWS", "advanced")]
    [r] = match_skills(students, [required("Azure")], "semantic")
    assert (r["matched_student_skill"], r["match_status"]) == ("AWS", "developing")


# ── Missing skills ────────────────────────────────────────────
@pytest.mark.parametrize("method", VALID_METHODS)
def test_no_student_skills_makes_every_skill_a_gap(similarity, method):
    reqs = [required("SQL"), required("Python", "preferred"), required("Docker", "bonus")]
    res = match_skills([], reqs, method)
    assert [r["match_status"] for r in res] == ["gap"] * 3
    assert all(r["similarity_score"] == 0.0 and r["matched_student_skill"] is None for r in res)
    assert all(r["reason"] == matcher.REASONS["gap_empty"] for r in res)
    assert similarity.calls == []                                      # nothing to compare


@pytest.mark.parametrize("method", VALID_METHODS)
def test_no_required_skills_gives_an_empty_list(method):
    assert match_skills([student("SQL")], [], method) == []


def test_missing_skill_reason_names_the_skill(similarity):
    [kw] = match_skills([student("SQL")], [required("Docker")], "keyword")
    [hy] = match_skills([student("SQL")], [required("Docker")], "hybrid")
    assert kw["reason"] == "No skill in your profile is Docker or another name for it, so this is marked as a Gap."
    assert hy["reason"] == "No skill in your profile is Docker or close enough to it, so this is marked as a Gap."


# ── Word traps ────────────────────────────────────────────────
@pytest.mark.parametrize("have, need", [
    ("Java", "JavaScript"), ("JavaScript", "Java"), ("R", "Ruby"), ("R", "React"),
    ("MySQL", "SQL"), ("Go", "Google Cloud Platform"), ("C++", "C#"),
])
def test_word_traps_with_keyword(have, need):
    [r] = match_skills([student(have, "advanced", ["project"])], [required(need)], "keyword")
    assert r["match_status"] == "gap"


# ── Output contract ───────────────────────────────────────────
@pytest.mark.parametrize("method", VALID_METHODS)
def test_every_result_is_complete(similarity, method):
    similarity.table.update({("Azure", "AWS"): 0.55, ("Requirements Analysis", "Business Analysis"): 0.7})
    students = [student("SQL", "advanced", ["project"]), student("Python", "beginner"),
                student("AWS"), student("Business Analysis")]
    reqs = [required("SQL", skill_id="u-sql"), required("Python"), required("Azure", "preferred"),
            required("Requirements Analysis", "preferred"), required("Docker", "bonus"),
            required("SQL", "bonus")]
    res = match_skills(students, reqs, method)
    assert len(res) == len(reqs)
    for r, q in zip(res, reqs):
        assert set(r) == set(MatchResult.__annotations__)
        assert (r["skill_id"], r["skill_name"], r["importance"]) == (q["skill_id"], q["skill_name"], q["importance"])
        assert r["match_status"] in ("strong", "developing", "gap")
        assert 0.0 <= r["similarity_score"] <= 1.0
        assert r["matching_method"] == method
        assert (r["matched_student_skill"] is None) == (r["match_status"] == "gap")
        assert isinstance(r["reason"], str) and r["reason"].strip().endswith(".")


def test_reasons_follow_the_templates(similarity):
    similarity.table.update({("Requirements Analysis", "Business Analysis"): 0.7, ("Azure", "AWS"): 0.55})
    students = [student("SQL", "advanced", ["project", "coursework"]), student("Python", "beginner"),
                student("Excel", "beginner", ["coursework"]),
                student("Business Analysis"), student("AWS", "intermediate")]
    reqs = [required("SQL"), required("Python"), required("Excel"), required("Requirements Analysis"),
            required("Azure"), required("Docker")]
    assert [r["reason"] for r in match_skills(students, reqs, "hybrid")] == [
        "You list SQL (advanced, with project and coursework evidence), which matches this skill, "
        "so this is marked Strong.",
        "You list Python (beginner). A beginner skill needs project, certification or internship "
        "evidence to count as Strong, so this is marked Developing.",
        "You list Excel (beginner, with coursework evidence). A beginner skill needs project, "
        "certification or internship evidence to count as Strong, so this is marked Developing.",
        "You list Business Analysis (intermediate), which is very close to Requirements Analysis "
        "but not the same skill, so this is marked Developing.",
        "You list AWS (intermediate). It is closely related to Azure but not the same skill, "
        "so this is marked Developing.",
        "No skill in your profile is Docker or close enough to it, so this is marked as a Gap.",
    ]


# ── Input ─────────────────────────────────────────────────────
@pytest.mark.parametrize("students, reqs", [
    ([{"skill_id": None, "proficiency_level": "advanced", "evidence_type": []}], [required("SQL")]),
    ([student("SQL", level="expert")], [required("SQL")]),
    ([student("SQL", level=None)], [required("SQL")]),
    ([student("SQL")], [required("SQL", importance="must-have")]),
    (["SQL"], [required("SQL")]),
    ([student("SQL")], [required("   ")]),
])
def test_malformed_input_raises_value_error(students, reqs):
    with pytest.raises(ValueError):
        match_skills(students, reqs, "keyword")


def test_database_style_values_are_accepted():
    s = {"skill_id": None, "skill_name": "SQL", "proficiency_level": "Beginner",
         "evidence_type": "{project,coursework}"}                     # PostgreSQL array literal
    [r] = match_skills([s], [{"skill_id": None, "skill_name": "SQL", "importance": None}], "keyword")
    assert (r["match_status"], r["importance"]) == ("strong", "required")   # NULL -> DB default
    s["evidence_type"] = None
    assert match_skills([s], [required("SQL")], "keyword")[0]["match_status"] == "developing"


# ── Model ─────────────────────────────────────────────────────
@model
def test_similarity_matrix_with_the_model(monkeypatch):
    from nlp import model as nlp_model
    cat = load_catalogue()
    sims = matcher.similarity_matrix(["SQL", "Ruby"], ["SQL", "R", "Ruby"], cat)
    assert sims.shape == (2, 3)
    assert sims[0][0] == pytest.approx(1.0, abs=1e-5)     # catalogue skill against itself
    assert sims[1][2] == pytest.approx(1.0, abs=1e-5)     # "Ruby" is not in the catalogue

    def no_encoding(texts, **kw):
        raise AssertionError(f"encoded again: {texts}")
    monkeypatch.setattr(nlp_model, "encode", no_encoding)
    matcher.similarity_matrix(["Ruby", "Power BI"], ["SQL", "Tableau"], cat)   # all cached


def report(capsys, pairs):
    cat = load_catalogue()
    with capsys.disabled():
        for have, need, r in pairs:
            sim = float(matcher.similarity_matrix([cat.lookup(need) or need], [have], cat)[0][0])
            print(f"\n  {have} -> {need}: cosine {sim:.3f}, {r['match_status']}", end="")


@model
@pytest.mark.parametrize("method", ["semantic", "hybrid"])
def test_related_tools_with_the_model(capsys, method):
    """S2-12-02 weak matches: related tools are not the same skill."""
    pairs = [("Tableau", "Power BI"), ("MySQL", "PostgreSQL"), ("AWS", "Azure")]
    results = [(have, need, match_skills([student(have, "intermediate", ["project"])],
                                         [required(need)], method)[0]) for have, need in pairs]
    report(capsys, results)
    for have, need, r in results:
        assert r["match_status"] != "strong", f"{have} counted as {need}"
        assert r["similarity_score"] < MATCH
        expected = "developing" if r["similarity_score"] >= RELATED else "gap"
        assert r["match_status"] == expected


@model
@pytest.mark.parametrize("method", ["semantic", "hybrid"])
def test_word_traps_with_the_model(capsys, method):
    pairs = [("Java", "JavaScript"), ("R", "Ruby"), ("MySQL", "SQL")]
    results = [(have, need, match_skills([student(have, "advanced", ["project"])],
                                         [required(need)], method)[0]) for have, need in pairs]
    report(capsys, results)
    java, ruby, mysql = (r for _, _, r in results)
    assert java["match_status"] != "strong"
    assert ruby["match_status"] == "gap"
    assert mysql["match_status"] != "strong"


# ── Readiness on synthetic students (S2-11-02) ────────────────
DATA = ROOT / "data" / "output"
ROLE_SEED = ROOT / "database" / "seed_job_role_skills.sql"
ROLE_NAMES = {"DATA_ANALYST": "Data Analyst", "DATA_SCIENTIST": "Data Scientist",
              "SOFTWARE_DEV": "Software Developer", "CYBER_ANALYST": "Cybersecurity Analyst",
              "CLOUD_ENGINEER": "Cloud Engineer", "WEB_DEV": "Web Developer",
              "BUSINESS_ANALYST": "Business Analyst", "MARKETING_EXEC": "Marketing Executive",
              "FINANCIAL_ANALYST": "Financial Analyst", "HR_EXEC": "HR Executive"}
ARCHETYPES = ("strong", "average", "weak")
ROLES = ("Data Analyst", "Cybersecurity Analyst")

# Weighted score as in backend/routers/assessments.py (reimplemented, not imported).
WEIGHTS = {"required": 3, "preferred": 2, "bonus": 1}
CREDIT = {"strong": 1.0, "developing": 0.5, "gap": 0.0}


def readiness(results):
    earned = sum(WEIGHTS.get(r["importance"], 1) * CREDIT[r["match_status"]] for r in results)
    total = sum(WEIGHTS.get(r["importance"], 1) for r in results)
    return round(earned / total * 100, 2) if total else 0


@pytest.fixture(scope="module")
def role_skills():
    """RequiredSkill lists per role from seed_job_role_skills.sql, required -> preferred -> bonus."""
    sql = ROLE_SEED.read_text(encoding="utf-8")
    rows = re.findall(r"^\s*\('([A-Z_]+)',\s*'((?:[^']|'')+)',\s*'(required|preferred|bonus)'\)", sql, flags=re.M)
    roles = defaultdict(list)
    for code, name, importance in rows:
        roles[ROLE_NAMES[code]].append(required(name.replace("''", "'"), importance))
    for skills in roles.values():
        skills.sort(key=lambda r: ("required", "preferred", "bonus").index(r["importance"]))
    return roles


@pytest.fixture(scope="module")
def synthetic():
    """(students_meta rows, {profile_id: [StudentSkill]}) from data/output/."""
    if not (DATA / "students_meta.csv").exists():
        pytest.skip("synthetic data not generated (data/generate_synthetic_data.py)")
    with open(DATA / "students_meta.csv", encoding="utf-8", newline="") as f:
        meta = list(csv.DictReader(f))
    skills = defaultdict(list)
    with open(DATA / "student_skills.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            skills[row["profile_id"]].append(student(row["skill_name"], row["proficiency_level"]))
            skills[row["profile_id"]][-1]["evidence_type"] = row["evidence_type"]   # "{coursework}"
    return meta, skills


def representative(meta, role, archetype):
    """The student whose core-skill coverage is the median of their role and archetype."""
    group = [m for m in meta if m["target_role"] == role and m["archetype"] == archetype]
    median = statistics.median(float(m["core_coverage_pct"]) for m in group)
    return min(group, key=lambda m: (abs(float(m["core_coverage_pct"]) - median), m["email"]))


def check_ranking(capsys, synthetic, role_skills, role, method):
    meta, skills = synthetic
    picked = {a: representative(meta, role, a) for a in ARCHETYPES}
    scores = {a: readiness(match_skills(skills[m["profile_id"]], role_skills[role], method))
              for a, m in picked.items()}
    means = {}
    for a in ARCHETYPES:
        group = [m["profile_id"] for m in meta if m["target_role"] == role and m["archetype"] == a]
        means[a] = statistics.mean(readiness(match_skills(skills[p], role_skills[role], method))
                                   for p in group)
    with capsys.disabled():
        print(f"\n  {role} ({method}): " + ", ".join(
            f"{a} {picked[a]['email'].split('@')[0]} {scores[a]:.1f} (mean {means[a]:.1f})"
            for a in ARCHETYPES), end="")
    assert scores["strong"] > scores["average"] > scores["weak"]
    assert means["strong"] > means["average"] > means["weak"]


@pytest.mark.parametrize("role", ROLES)
def test_readiness_ranks_strong_average_weak_keyword(capsys, synthetic, role_skills, role):
    check_ranking(capsys, synthetic, role_skills, role, "keyword")


@model
@pytest.mark.parametrize("role", ROLES)
def test_readiness_ranks_strong_average_weak_hybrid(capsys, synthetic, role_skills, role):
    check_ranking(capsys, synthetic, role_skills, role, "hybrid")
