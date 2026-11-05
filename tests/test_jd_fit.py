"""
JD fit (backend/jd_fit.py). No database. API tests are in test_backend_api.py (TestJdFit).

    python -m pytest tests/test_jd_fit.py -q
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from jd_fit import JD_FIT_THRESHOLD, jd_fit, load_jd_skill_sets, skill_credit  # noqa: E402


def skill(name, level="intermediate", evidence=()):
    return {"skill_name": name, "proficiency_level": level, "evidence_type": list(evidence)}


def covered(student_skills, jd):
    return jd_fit(student_skills, [jd])["covered"]


def test_threshold_is_named_and_returned():
    assert JD_FIT_THRESHOLD == 0.60
    assert jd_fit([], [{"SQL"}]) == {"covered": 0, "total": 1, "threshold": 0.60}


def test_exactly_at_the_threshold_counts():
    jd = {"A", "B", "C", "D", "E"}
    assert covered([skill("A"), skill("B"), skill("C")], jd) == 1                  # 3 / 5
    assert covered([skill("A"), skill("B")], jd) == 0                              # 2 / 5
    halves = [skill("A"), skill("B"), skill("C", "beginner"), skill("D", "beginner")]
    assert covered(halves, jd) == 1                                                # (1 + 1 + .5 + .5) / 5
    assert covered([skill(c) for c in "ABCDEF"], set("ABCDEFGHIJ")) == 1           # 6 / 10


def test_just_below_the_threshold_does_not_count():
    jd = {"A", "B", "C", "D", "E", "F", "G", "H", "I", "J"}
    five_and_half = [skill(c) for c in "ABCDE"] + [skill("F", "beginner")]
    assert covered(five_and_half, jd) == 0                                         # 5.5 / 10


def test_beginner_without_evidence_counts_half():
    assert skill_credit(skill("SQL", "beginner")) == 0.5
    assert covered([skill("A", "beginner")], {"A"}) == 0                           # 0.5
    assert covered([skill("A", "beginner"), skill("B")], {"A", "B"}) == 1          # 0.75


def test_beginner_with_evidence_counts_in_full():
    for kind in ("project", "certification", "internship"):
        assert skill_credit(skill("SQL", "beginner", [kind])) == 1.0
    assert covered([skill("A", "beginner", ["project"])], {"A"}) == 1


def test_coursework_alone_is_not_evidence():
    assert skill_credit(skill("SQL", "beginner", ["coursework"])) == 0.5           # rule C


def test_intermediate_and_advanced_count_in_full_without_evidence():
    assert skill_credit(skill("SQL", "intermediate")) == skill_credit(skill("SQL", "advanced")) == 1.0


def test_a_skill_the_student_lacks_earns_nothing():
    assert covered([skill("B")], {"A"}) == 0
    assert covered([skill("A")], {"A", "B"}) == 0                                  # 0.5


def test_only_the_exact_name_matches():
    assert covered([skill("PostgreSQL")], {"SQL"}) == 0
    assert covered([skill("sql")], {"SQL"}) == 0


def test_empty_jd_is_skipped():
    assert jd_fit([skill("A")], [set(), {"A"}, set()]) == {"covered": 1, "total": 1, "threshold": 0.60}
    assert jd_fit([skill("A")], []) == {"covered": 0, "total": 0, "threshold": 0.60}


def test_counts_each_jd_separately():
    jds = [{"A"}, {"A", "B"}, {"C"}]
    assert jd_fit([skill("A"), skill("B")], jds)["covered"] == 2


def test_listing_a_skill_twice_uses_the_better_entry():
    assert covered([skill("A", "beginner"), skill("A", "advanced")], {"A"}) == 1


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        out = csv.writer(f)
        out.writerow(["role_code", "skill_name", "jd_ref", "method", "matched_text", "context"])
        out.writerows(rows)


def test_loader_groups_by_role_and_jd(tmp_path):
    path = tmp_path / "evidence.csv"
    write_csv(path, [["R1", "SQL", "J1", "keyword", "sql", "…<<sql>>…"],
                     ["R1", "Excel", "J1", "keyword", "excel", "x"],
                     ["R1", "SQL", "J1", "semantic", "queries", "x"],     # one set, no repeats
                     ["R1", "SQL", "J2", "keyword", "sql", "x"],
                     ["R2", "Java", "J3", "keyword", "java", "x"],
                     ["R2", "", "J4", "keyword", "", "x"]])
    sets = load_jd_skill_sets(path)
    assert sorted(sets["R1"], key=len) == [{"SQL"}, {"SQL", "Excel"}]
    assert jd_fit([skill("Java")], sets["R2"]) == {"covered": 1, "total": 1, "threshold": 0.60}


def test_loader_reads_the_file_once(tmp_path):
    path = tmp_path / "once.csv"
    write_csv(path, [["R1", "SQL", "J1", "keyword", "sql", "x"]])
    first = load_jd_skill_sets(path)
    path.unlink()
    assert load_jd_skill_sets(path) is first


def test_committed_dataset_has_every_role():
    sets = load_jd_skill_sets()
    assert set(sets) == {"DATA_ANALYST", "DATA_SCIENTIST", "SOFTWARE_DEV", "CYBER_ANALYST", "CLOUD_ENGINEER",
                         "WEB_DEV", "BUSINESS_ANALYST", "FINANCIAL_ANALYST", "HR_EXEC", "MARKETING_EXEC"}
    assert all(30 <= len(jds) <= 35 and all(jds) for jds in sets.values())
