"""
SEAGAS — Job Readiness Score: tiered coverage

Coverage of an importance tier is the mean credit of its skills. Readiness is
100 x sum(tier weight x coverage) / sum(weights of the tiers this job has), so the
score does not fall as a template gets longer. The tier weights are a design choice;
reasoning and limits in docs/JOB_READINESS_SCORE.md. The seven dimension scores do
not use this: they stay on the points in assessment_service.py.

No database or NLP imports, so tests and scripts can use it on their own.
"""

TIER_WEIGHTS  = {"required": 0.70, "preferred": 0.25, "bonus": 0.05}
STATUS_CREDIT = {"strong": 1.0, "developing": 0.5, "gap": 0.0}


def tier_coverage(rows):
    """Mean credit (0 to 1) per tier, None for a tier the job does not have.

    rows have "importance" and "match_status"; a missing importance counts as required.
    """
    credits = {tier: [] for tier in TIER_WEIGHTS}
    for row in rows:
        credits[row.get("importance") or "required"].append(STATUS_CREDIT[row["match_status"]])
    return {tier: sum(c) / len(c) if c else None for tier, c in credits.items()}


def tiered_readiness(rows):
    """Readiness from 0 to 100, rounded to 2 decimals; 0 when there are no rows."""
    present = {tier: c for tier, c in tier_coverage(rows).items() if c is not None}
    if not present:
        return 0
    earned = sum(TIER_WEIGHTS[tier] * c for tier, c in present.items())
    return round(100 * earned / sum(TIER_WEIGHTS[tier] for tier in present), 2)
