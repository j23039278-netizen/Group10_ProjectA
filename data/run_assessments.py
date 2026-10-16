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

The method defaults to hybrid; without nlp/requirements.txt installed it falls
back to keyword (the stored matching_method says which one ran).
start_backend.bat runs this once when the synthetic students have no assessments.
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

SYNTHETIC_EMAIL = "%@synthetic.example.com"
BATCH = 200


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("--method", default=nlp_service.DEFAULT_METHOD, choices=nlp_service.METHODS)
    ap.add_argument("--limit", type=int, default=None, help="assess at most this many students")
    ap.add_argument("--force", action="store_true", help="also assess students who already have one")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        students = db.execute(
            text(f"""
                SELECT sp.*, jr.role_id
                FROM users u
                JOIN student_profiles sp ON sp.user_id = u.user_id
                JOIN job_roles jr        ON jr.role_name = sp.target_role AND jr.is_active
                WHERE u.role = 'student' AND u.email LIKE :synthetic
                  {"" if args.force else "AND NOT EXISTS (SELECT 1 FROM assessments a WHERE a.profile_id = sp.profile_id)"}
                ORDER BY u.email
                {"LIMIT :limit" if args.limit else ""}
            """),
            {"synthetic": SYNTHETIC_EMAIL, "limit": args.limit}
        ).fetchall()
        if not students:
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
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
