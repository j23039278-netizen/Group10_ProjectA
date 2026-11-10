"""
SEAGAS — Sensitivity of the Job Readiness Score to its weights and the Developing credit

Re-scores the latest role-template assessment of every active student from the stored
match statuses (skill_match_results) and the role's importance (job_role_skills) under
alternative schemes, and compares each with the scheme in backend/readiness.py:
mean score, Spearman rank correlation, and how many students change readiness band.
A scheme is either tiers (mean credit per importance tier, then the tier weights) or
points (one shared denominator over all skills, the formula used until November 2026).
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
from readiness import TIER_WEIGHTS  # noqa: E402

ON_TRACK, NEEDS_SUPPORT = 70, 40   # default readiness bands (System Settings)
CURRENT = "current tiers 70/25/5, developing 0.5"
SCHEMES = {     # (kind, weights, developing credit)
    CURRENT:                              ("tiers",  TIER_WEIGHTS, 0.5),
    "old points 3/2/1, developing 0.5":   ("points", {"required": 3, "preferred": 2, "bonus": 1}, 0.5),
    "tiers 75/20/5, developing 0.5":      ("tiers",  {"required": .75, "preferred": .20, "bonus": .05}, 0.5),
    "tiers 60/30/10, developing 0.5":     ("tiers",  {"required": .60, "preferred": .30, "bonus": .10}, 0.5),
    "tiers 50/35/15, developing 0.5":     ("tiers",  {"required": .50, "preferred": .35, "bonus": .15}, 0.5),
    "tiers 70/25/5, developing 0.25":     ("tiers",  TIER_WEIGHTS, 0.25),
    "tiers 70/25/5, developing 0.75":     ("tiers",  TIER_WEIGHTS, 0.75),
    "required skills only":               ("tiers",  {"required": 1, "preferred": 0, "bonus": 0}, 0.5),
}


def score(items, scheme):
    kind, weights, developing = scheme
    credit = {"strong": 1.0, "developing": developing, "gap": 0.0}
    return (tier_score if kind == "tiers" else point_score)(items, weights, credit)


def point_score(items, weights, credit):
    top = sum(weights[i] for i, _ in items)
    return 100 * sum(weights[i] * credit[s] for i, s in items) / top if top else 0


def tier_score(items, weights, credit):
    tiers = defaultdict(list)
    for i, s in items:
        tiers[i].append(credit[s])
    top = sum(weights[t] for t in tiers)
    return 100 * sum(weights[t] * sum(c) / len(c) for t, c in tiers.items()) / top if top else 0


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

    base = [score(by_assessment[i], SCHEMES[CURRENT]) for i in ids]
    check = max(abs(b - stored[i]) for b, i in zip(base, ids))
    stale = sum(abs(b - stored[i]) > 0.01 for b, i in zip(base, ids))
    print(f"Assessments: {len(ids)} (current scheme re-scored vs stored: max difference {check:.2f}, "
          f"{stale} stored under an older formula)\n")
    print("| Scheme | Mean | Spearman ρ vs current | Students changing band (70 / 40) |")
    print("|---|---:|---:|---:|")
    for name, scheme in SCHEMES.items():
        xs = [score(by_assessment[i], scheme) for i in ids]
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
