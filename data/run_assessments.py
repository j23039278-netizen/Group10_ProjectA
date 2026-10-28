"""
SEAGAS — Batch assessments for the synthetic students

Runs one assessment per synthetic student against the target role in their
profile, with the same code the website uses (backend/assessment_service.py),
so the advisor dashboard has real cohort data: readiness scores, skill gaps,
students who need support.

Usage (from the repo root or anywhere):
    python data/run_assessments.py                  # students with no assessment yet
    python data/run_assessments.py --method keyword # faster; no NLP model needed
    python data/run_assessments.py --limit 100      # try a few first
    python data/run_assessments.py --force          # add a new assessment for everyone
    python data/run_assessments.py --auto           # what start_backend.bat runs

The method defaults to hybrid; without nlp/requirements.txt installed it falls
back to keyword (the stored matching_method says which one ran).

--auto assesses students with no assessment yet, and adds a new assessment for
every synthetic student when nlp/config.py MATCH_RULES_VERSION differs from the
version this machine last ran (kept in backend/.assessment_rules_version, not in
git). The advisor dashboard reads each student's latest assessment, so the old
ones stay as history.
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text  # noqa: E402

import assessment_service  # noqa: E402  (backend/, needs the path above)
import nlp_service  # noqa: E402
from database import SessionLocal  # noqa: E402  (reads backend/.env)
from nlp.config import MATCH_RULES_VERSION  # noqa: E402  (repo root is on the path via nlp_service)

SYNTHETIC_EMAIL = "%@synthetic.example.com"
BATCH = 200
RULES_FILE = BACKEND / ".assessment_rules_version"   # local to this machine, not in git


def stored_rules_version():
    try:
        return RULES_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("--method", default=nlp_service.DEFAULT_METHOD, choices=nlp_service.METHODS)
    ap.add_argument("--limit", type=int, default=None, help="assess at most this many students")
    ap.add_argument("--force", action="store_true", help="also assess students who already have one")
    ap.add_argument("--auto", action="store_true",
                    help="new students only, or everyone once when the matching rules changed")
    args = ap.parse_args()
    if args.auto and (args.force or args.limit):
        ap.error("--auto cannot be combined with --force or --limit")

    db = SessionLocal()
    try:
        force = args.force
        if args.auto:
            assessed = db.execute(
                text("""
                    SELECT count(DISTINCT a.profile_id)
                    FROM assessments a
                    JOIN student_profiles sp USING (profile_id)
                    JOIN users u USING (user_id)
                    WHERE u.email LIKE :synthetic
                """),
                {"synthetic": SYNTHETIC_EMAIL}
            ).scalar()
            stored = stored_rules_version()
            if assessed and stored != MATCH_RULES_VERSION:
                print(f"      matching rules changed ({stored or 'older'} -> {MATCH_RULES_VERSION}): "
                      f"re-assessing every synthetic student once")
                force = True
            elif assessed:
                print(f"      {assessed} synthetic students already assessed (rules {MATCH_RULES_VERSION})")

        students = db.execute(
            text(f"""
                SELECT sp.*, jr.role_id
                FROM users u
                JOIN student_profiles sp ON sp.user_id = u.user_id
                JOIN job_roles jr        ON jr.role_name = sp.target_role AND jr.is_active
                WHERE u.role = 'student' AND u.email LIKE :synthetic
                  {"" if force else "AND NOT EXISTS (SELECT 1 FROM assessments a WHERE a.profile_id = sp.profile_id)"}
                ORDER BY u.email
                {"LIMIT :limit" if args.limit else ""}
            """),
            {"synthetic": SYNTHETIC_EMAIL, "limit": args.limit}
        ).fetchall()
        if not students:
            if args.auto:
                RULES_FILE.write_text(MATCH_RULES_VERSION + "\n", encoding="utf-8")
            else:
                print("      no synthetic students left to assess")
            return 0

        print(f"      assessing {len(students)} synthetic students ({args.method}) ...")
        started, done, skipped = time.time(), 0, Counter()
        methods, scores = Counter(), []
        for i, sp in enumerate(students, 1):
            try:
                r = assessment_service.run_for_profile(
                    db, sp, role_id=sp.role_id, method=args.method, commit=False)
            except assessment_service.AssessmentError as e:
                skipped[e.detail] += 1
                continue
            done += 1
            methods[r["matching_method"]] += 1
            scores.append(r["readiness_score"])
            if i % BATCH == 0:
                db.commit()
                print(f"      {i}/{len(students)}  ({time.time() - started:.0f} s)")
        db.commit()

        took = time.time() - started
        print(f"      done: {done} assessments in {took:.0f} s "
              f"(method used: {dict(methods)}); mean readiness {sum(scores) / max(len(scores), 1):.1f}%")
        for reason, n in skipped.items():
            print(f"      skipped {n}: {reason}")
        if args.auto:
            RULES_FILE.write_text(MATCH_RULES_VERSION + "\n", encoding="utf-8")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
