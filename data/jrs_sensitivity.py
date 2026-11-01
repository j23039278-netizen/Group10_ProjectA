"""
SEAGAS — Sensitivity of the Job Readiness Score to its weights and the Developing credit

Re-scores the latest role-template assessment of every active student from the stored
match statuses (skill_match_results) and the role's importance (job_role_skills) under
alternative schemes, and compares each with the scheme in backend/assessment_service.py:
mean score, Spearman rank correlation, and how many students change readiness band.
Nothing is written. Results and their discussion: docs/JOB_READINESS_SCORE.md.

    python data/jrs_sensitivity.py
"""
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import text  # noqa: E402
from database import SessionLocal  # noqa: E402  (reads backend/.env)

ON_TRACK, NEEDS_SUPPORT = 70, 40   # default readiness bands (System Settings)
CURRENT = "current 3/2/1, developing 0.5"
SCHEMES = {
    CURRENT:                         ({"required": 3, "preferred": 2, "bonus": 1}, 0.5),
    "equal 1/1/1, developing 0.5":   ({"required": 1, "preferred": 1, "bonus": 1}, 0.5),
    "steeper 4/2/1, developing 0.5": ({"required": 4, "preferred": 2, "bonus": 1}, 0.5),
    "3/2/1, developing 0.25":        ({"required": 3, "preferred": 2, "bonus": 1}, 0.25),
    "3/2/1, developing 0.75":        ({"required": 3, "preferred": 2, "bonus": 1}, 0.75),
    "required skills only":          ({"required": 1, "preferred": 0, "bonus": 0}, 0.5),
}


def score(items, weights, developing):
    credit = {"strong": 1.0, "developing": developing, "gap": 0.0}
    top = sum(weights[i] for i, _ in items)
    return 100 * sum(weights[i] * credit[s] for i, s in items) / top if top else 0


def ranks(xs):
    """Ranks with ties sharing their average rank"""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return cov / (sum((x - ma) ** 2 for x in ra) ** 0.5 * sum((y - mb) ** 2 for y in rb) ** 0.5)


def band(s):
    return "on_track" if s >= ON_TRACK else "needs_support" if s < NEEDS_SUPPORT else "developing"


def main():
    db = SessionLocal()
    rows = db.execute(text("""
        WITH latest AS (
            SELECT DISTINCT ON (a.profile_id) a.assessment_id, a.role_id, a.readiness_score
            FROM assessments a
            JOIN student_profiles sp ON sp.profile_id = a.profile_id
            JOIN users u ON u.user_id = sp.user_id
            WHERE u.role = 'student' AND u.is_active AND a.role_id IS NOT NULL
            ORDER BY a.profile_id, a.created_at DESC
        )
        SELECT l.assessment_id, l.readiness_score, jrs.importance, smr.match_status
        FROM latest l
        JOIN skill_match_results smr ON smr.assessment_id = l.assessment_id
        JOIN job_role_skills jrs ON jrs.role_id = l.role_id AND jrs.skill_id = smr.skill_id
    """)).fetchall()
    db.close()

    by_assessment, stored = defaultdict(list), {}
    for r in rows:
        by_assessment[r.assessment_id].append((r.importance, r.match_status))
        stored[r.assessment_id] = float(r.readiness_score)
    ids = sorted(by_assessment)
    if not ids:
        sys.exit("No assessments yet: run data/run_assessments.py first.")

    base = [score(by_assessment[i], *SCHEMES[CURRENT]) for i in ids]
    check = max(abs(b - stored[i]) for b, i in zip(base, ids))
    print(f"Assessments: {len(ids)} (current scheme re-scored vs stored: max difference {check:.2f})\n")
    print("| Scheme | Mean | Spearman ρ vs current | Students changing band (70 / 40) |")
    print("|---|---:|---:|---:|")
    for name, (weights, developing) in SCHEMES.items():
        xs = [score(by_assessment[i], weights, developing) for i in ids]
        moved = sum(band(x) != band(b) for x, b in zip(xs, base))
        print(f"| {name} | {sum(xs) / len(xs):.1f} | {spearman(xs, base):.3f} | {moved} ({100 * moved / len(ids):.1f}%) |")

    bands = defaultdict(int)
    for b in base:
        bands[band(b)] += 1
    mix = defaultdict(int)
    for r in rows:
        mix[r.importance] += 1
    print(f"\nBands (current scheme): {dict(bands)}")
    print(f"Required-skill rows by importance: {dict(mix)}")


if __name__ == "__main__":
    main()
