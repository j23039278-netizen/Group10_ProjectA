"""
SEAGAS — JD fit: of a role's real job descriptions, how many does a student cover?

A second number beside the Job Readiness Score. It never feeds into readiness.
It is worked out from the student's current skills when it is read, so it can
differ from a stored assessment. Meaning and limits: docs/JOB_READINESS_SCORE.md,
section 7.

Skills match by exact name only: a similar skill earns nothing here, though it
can be Developing in the readiness score (rule A). Credit follows rule C
(docs/NLP_CLASSIFICATION_RULES.md).
"""

import csv
from functools import lru_cache

from nlp_service import REPO_ROOT  # also puts the repo root on the path
from nlp import STRONG_EVIDENCE

EVIDENCE_CSV = REPO_ROOT / "data" / "jd_dataset" / "jd_skill_evidence.csv"

# A design choice from an offline pilot on synthetic students. It has not been
# validated with employers, advisors or real students.
JD_FIT_THRESHOLD = 0.60

SOLID_LEVELS = ("intermediate", "advanced")


@lru_cache(maxsize=None)
def load_jd_skill_sets(path=EVIDENCE_CSV):
    """{role_code: [set of skill names of one JD, ...]}, read from the CSV once."""
    jds = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            skills = jds.setdefault(row["role_code"], {}).setdefault(row["jd_ref"], set())
            if row["skill_name"]:
                skills.add(row["skill_name"])
    return {role: list(by_ref.values()) for role, by_ref in jds.items()}


def skill_credit(skill):
    """1.0 for intermediate / advanced, or a project, certification or internship
    behind the skill; 0.5 for a beginner without that evidence."""
    solid = (skill.get("proficiency_level") in SOLID_LEVELS
             or not STRONG_EVIDENCE.isdisjoint(skill.get("evidence_type") or ()))
    return 1.0 if solid else 0.5


def jd_fit(student_skills, jd_skill_sets):
    """How many JDs the student covers. A JD with no skills is skipped.

    student_skills: dicts with skill_name, proficiency_level and evidence_type,
                    stored or from nlp.derive_evidence().
    jd_skill_sets:  one set of skill names per JD.
    """
    credits = {}
    for skill in student_skills:
        name = skill["skill_name"]
        credits[name] = max(credits.get(name, 0.0), skill_credit(skill))
    jds = [skills for skills in jd_skill_sets if skills]
    covered = sum(sum(credits.get(name, 0.0) for name in skills) / len(skills) >= JD_FIT_THRESHOLD
                  for skills in jds)
    return {"covered": covered, "total": len(jds), "threshold": JD_FIT_THRESHOLD}
