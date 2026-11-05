"""
SEAGAS — JD fit on the synthetic students

Takes the latest role-template assessment of every synthetic student, works out
how many of the role's real JDs they cover (backend/jd_fit.py, from their current
skills) and reports the mean per archetype and the Spearman correlation with the
stored readiness score. Archetypes come from data/output/students_meta.csv, joined
by email. The transaction is read-only, so nothing can be written. Results and
their discussion: docs/JOB_READINESS_SCORE.md, section 7.

    python data/jd_fit_cohort.py
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA.parent / "backend"))

from sqlalchemy import text  # noqa: E402

import assessment_service  # noqa: E402  (backend/, needs the path above)
import jd_fit  # noqa: E402
from database import SessionLocal  # noqa: E402  (reads backend/.env)
from jrs_sensitivity import spearman  # noqa: E402

ARCHETYPES = ("strong", "average", "weak")


def load_archetypes():
    with open(DATA / "output" / "students_meta.csv", encoding="utf-8", newline="") as f:
        return {row["email"].lower(): row["archetype"] for row in csv.DictReader(f)}


def latest_assessments(db):
    return db.execute(text("""
        SELECT DISTINCT ON (a.profile_id) a.profile_id, a.readiness_score, jr.role_code, lower(u.email) AS email
        FROM assessments a
        JOIN job_roles jr ON jr.role_id = a.role_id
        JOIN student_profiles sp ON sp.profile_id = a.profile_id
        JOIN users u ON u.user_id = sp.user_id
        WHERE u.role = 'student' AND u.is_active AND a.jd_id IS NULL
        ORDER BY a.profile_id, a.created_at DESC
    """)).fetchall()


def measure(db, assessments, archetypes):
    """One (archetype, role code, covered, total, readiness) per synthetic student with JDs"""
    jds = jd_fit.load_jd_skill_sets()
    students = []
    for a in assessments:
        if a.email in archetypes and a.role_code in jds:
            fit = jd_fit.jd_fit(assessment_service.load_student_skills(db, a.profile_id), jds[a.role_code])
            students.append((archetypes[a.email], a.role_code, fit["covered"], fit["total"], float(a.readiness_score)))
    return students


def mean(xs):
    return sum(xs) / len(xs)


def print_group(name, rows):
    covered = [r[2] for r in rows]
    none = sum(c == 0 for c in covered)
    print(f"| {name} | {len(rows)} | {mean(covered):.1f} | {mean([r[3] for r in rows]):.1f} | "
          f"{mean([r[4] for r in rows]):.1f} | {none} ({100 * none / len(rows):.1f}%) | "
          f"{sorted(covered)[len(covered) // 2]} | {max(covered)} |")


def main():
    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        assessments = latest_assessments(db)
        students = measure(db, assessments, load_archetypes())
    finally:
        db.rollback()
        db.close()
    if not students:
        sys.exit("No assessments of synthetic students yet: run data/run_assessments.py first.")

    version = (DATA / "output" / "DATA_VERSION").read_text(encoding="utf-8").strip()
    print(f"Synthetic students: {len(students)} (data/output/DATA_VERSION {version})\n")
    print("| Group | Students | Mean X | Mean N | Mean readiness | X = 0 | Median X | Max X |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    groups = defaultdict(list)
    for s in students:
        groups[s[0]].append(s)
    for archetype in ARCHETYPES:
        print_group(archetype, groups[archetype])
    print_group("all", students)

    roles = defaultdict(list)
    for s in students:
        roles[s[1]].append(s)
    print("\n| Role | Students | Mean X | Mean N | Mean readiness | X = 0 | Median X | Max X |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for role in sorted(roles):
        print_group(role, roles[role])

    print(f"\nSpearman, X vs readiness: {spearman([s[2] for s in students], [s[4] for s in students]):.3f}")
    for archetype in ARCHETYPES:
        rows = groups[archetype]
        print(f"  within {archetype}: {spearman([s[2] for s in rows], [s[4] for s in rows]):.3f}")


if __name__ == "__main__":
    main()
