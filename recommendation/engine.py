"""
SEAGAS — Recommendation Engine
Rule-based engine that maps identified skill gaps to development resources.
Author: Tan Jun Xiong (Aaron) — Co-Leader & Recommendation Engine Developer

Logic:
  1. Receive the match rows of an assessment (assessment_service.load_match_rows)
  2. Order the skills to work on: required gap, required developing, preferred gap,
     preferred developing, bonus gap, bonus developing, then skill name (priority_key)
  3. Look up matching resources in recommendations_library; within a skill: cost tier
     (free first), difficulty order, resource type order
  4. Say what each is worth on the readiness score: expected_gain on a skill (the most it
     can add, when it reaches Strong), gain_if_completed on a resource (what completing
     that resource adds; the rule is nlp.status_after_activity)
  5. Pick first_steps: up to 3 skills, each with the resource worth doing first
  6. Return ranked recommendations with explanation

The gains are arithmetic on the score, not a claim about learning or employability:
docs/JOB_READINESS_SCORE.md, section 8.
"""

import sys
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional

# backend/ holds the modules below; recommendation/ is also imported from tests and data scripts
BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if BACKEND not in sys.path:
    sys.path.append(BACKEND)

from assessment_service import load_match_rows  # noqa: E402
from nlp import status_after_activity  # noqa: E402  (nlp/ sits next to recommendation/)
from readiness import expected_gain, gain_between, skill_points  # noqa: E402


# ── Resource type priority (what to recommend first) ──────────
RESOURCE_TYPE_PRIORITY = {
    "course":        1,
    "certification": 2,
    "project":       3,
    "workshop":      4,
    "competition":   5,
    "internship":    6,
}
 
# ── Difficulty order ──────────────────────────────────────────
DIFFICULTY_ORDER = {
    "beginner":     1,
    "intermediate": 2,
    "advanced":     3,
}
 
# ── Cost tier (free first) ────────────────────────────────────
# recommendations_library.cost is free text ("Free", "Free to audit", "$150 USD").
#   free           completely free
#   free_to_learn  learning is free; a certificate, more usage or extra features
#                  cost money ("Free to audit", "Free tier", "Free / $14/mo")
#   paid           costs money, including short free trials ("Free trial")
COST_TIER_ORDER = {"free": 1, "free_to_learn": 2, "paid": 3}


def cost_tier(cost: Optional[str]) -> str:
    c = (cost or "Free").strip().lower()
    if c == "free":
        return "free"
    if "trial" in c:
        return "paid"
    if c.startswith("free"):
        return "free_to_learn"
    return "paid"


# ── Gap type priority (gaps first, then developing) ───────────
GAP_TYPE_PRIORITY = {
    "gap":        1,
    "developing": 2,
}

# ── Importance priority (required first) ──────────────────────
IMPORTANCE_PRIORITY = {
    "required":  1,
    "preferred": 2,
    "bonus":     3,
}

FIRST_STEPS = 3


def priority_key(skill: Dict) -> tuple:
    """Sort key of a skill to work on: importance, then gap before developing, then name."""
    return (
        IMPORTANCE_PRIORITY[skill["importance"]],
        GAP_TYPE_PRIORITY[skill["gap_type"]],
        skill["skill_name"].casefold(),
    )


def skills_to_do(rows: List[Dict], include_developing: bool = True) -> List[Dict]:
    """The skills still to work on from an assessment's match rows, in priority order.
    Points come from all the rows: a skill's worth depends on how many share its tier."""
    points = skill_points(rows)
    statuses = ("gap", "developing") if include_developing else ("gap",)
    skills = [
        {
            "skill_id":      row["skill_id"],
            "skill_name":    row["skill_name"],
            "category":      row["category"],
            "gap_type":      row["match_status"],
            "similarity":    row["similarity_score"],
            "importance":    row["importance"],
            "points":        points[row["importance"]],
            "expected_gain": round(expected_gain(points[row["importance"]], row["match_status"]), 1),
        }
        for row in rows if row["match_status"] in statuses
    ]
    return sorted(skills, key=priority_key)


def gain_if_completed(points: float, gap_type: str, resource: Dict) -> float:
    """What completing this resource adds to the score, rounded to 1 decimal."""
    after = status_after_activity(resource.get("difficulty"), resource.get("resource_type"))
    return round(gain_between(points, gap_type, after), 1)


def with_gains(resources: List[Dict], skill: Dict) -> List[Dict]:
    """Copies of a skill's resources with gain_if_completed for this student's status."""
    return [{**r, "gain_if_completed": gain_if_completed(skill["points"], skill["gap_type"], r)}
            for r in resources]


def _best_resource(resources: List[Dict]) -> Optional[Dict]:
    """The resource worth doing: highest gain among free and free-to-learn ones, or among
    all when those add nothing. max() keeps the first on a tie, so the existing order holds.
    None when nothing adds points."""
    free = [r for r in resources if r["cost_tier"] != "paid"]
    for choices in (free, resources):
        best = max(choices, key=lambda r: r["gain_if_completed"], default=None)
        if best and best["gain_if_completed"] > 0:
            return best
    return None


def first_steps(
    skills: List[Dict],
    resources_by_skill: Dict[str, List[Dict]],
    completed: List[Dict],
    assessment_created_at,
    limit: int = FIRST_STEPS
) -> List[Dict]:
    """
    What to do first: walks the ordered skills and takes the first `limit` with a resource
    worth doing. A completed resource is never picked. A skill with a resource completed
    after the assessment was created is skipped, because its status is out of date until
    the student runs the assessment again.

    Args:
        skills: from skills_to_do, in order
        resources_by_skill: {skill_id: all active resources of the skill, with gains}
        completed: the student's completed resources {resource_id, skill_id, completed_at}
        assessment_created_at: when this assessment was created
    """
    done = {c["resource_id"] for c in completed}
    out_of_date = {c["skill_id"] for c in completed
                   if c["completed_at"] and c["completed_at"] > assessment_created_at}
    steps = []
    for skill in skills:
        if skill["skill_id"] in out_of_date:
            continue
        resource = _best_resource([r for r in resources_by_skill.get(skill["skill_id"], [])
                                   if r["resource_id"] not in done])
        if resource:
            steps.append({key: skill[key] for key in ("skill_id", "skill_name", "category", "gap_type",
                                                      "importance", "expected_gain")}
                         | {"resource": resource})
        if len(steps) == limit:
            break
    return steps
 
 
def get_recommendations_for_assessment(
    assessment_id: str,
    db: Session,
    max_resources_per_skill: int = 3,
    include_developing: bool = True
) -> Dict:
    """
    Main recommendation engine function.
    Given an assessment_id, returns personalised recommendations for all skill gaps.
 
    Args:
        assessment_id: UUID of the assessment
        db: SQLAlchemy database session
        max_resources_per_skill: max resources to return per skill (default 3)
        include_developing: whether to include developing skills (default True)
 
    Returns:
        Dict with recommendations list and summary stats
    """
 
    # Step 1: Get the skills to work on, in priority order
    skills = skills_to_do(load_match_rows(db, assessment_id), include_developing)

    if not skills:
        return {
            "assessment_id": assessment_id,
            "total_gaps":    0,
            "recommendations": [],
            "first_steps":   [],
            "message": "No skill gaps found — great job!"
        }

    # Step 2: Get resources for each skill
    recommendations = []
    resources_by_skill = {}

    for position, skill in enumerate(skills, start=1):
        resources_by_skill[skill["skill_id"]] = with_gains(ranked_resources(skill["skill_id"], db), skill)
        resources = resources_by_skill[skill["skill_id"]][:max_resources_per_skill]

        explanation = _generate_explanation(
            skill_name=skill["skill_name"],
            gap_type=skill["gap_type"],
            category=skill["category"],
            similarity_score=skill["similarity"],
            resource_count=len(resources)
        )

        recommendations.append({
            "skill_id":      skill["skill_id"],
            "skill_name":    skill["skill_name"],
            "category":      skill["category"],
            "gap_type":      skill["gap_type"],
            "similarity":    skill["similarity"],
            "importance":    skill["importance"],
            "expected_gain": skill["expected_gain"],
            "explanation":   explanation,
            "resources":     resources,
            "priority":      position
        })

    # Step 3: What to do first
    assessment = db.execute(
        text("SELECT profile_id, created_at FROM assessments WHERE assessment_id = :aid"),
        {"aid": assessment_id}
    ).fetchone()
    steps = first_steps(skills, resources_by_skill, load_completed(db, assessment.profile_id), assessment.created_at)

    # Step 4: Generate summary
    gap_count        = sum(1 for r in recommendations if r["gap_type"] == "gap")
    developing_count = sum(1 for r in recommendations if r["gap_type"] == "developing")
    total_resources  = sum(len(r["resources"]) for r in recommendations)

    return {
        "assessment_id":    assessment_id,
        "total_gaps":       gap_count,
        "total_developing": developing_count,
        "total_resources":  total_resources,
        "recommendations":  recommendations,
        "first_steps":      steps,
        "summary": _generate_summary(gap_count, developing_count, total_resources)
    }


def load_completed(db: Session, profile_id) -> List[Dict]:
    """The student's completed resources. Starting one again changes its status but keeps
    completed_at, and the skill it added stays, so it still counts as completed."""
    rows = db.execute(
        text("""
            SELECT srp.resource_id, rl.skill_id, srp.completed_at
            FROM student_resource_progress srp
            JOIN recommendations_library rl ON rl.resource_id = srp.resource_id
            WHERE srp.profile_id = :pid
            AND (srp.status = 'completed' OR srp.completed_at IS NOT NULL)
        """),
        {"pid": str(profile_id)}
    ).fetchall()
    return [{"resource_id": str(r.resource_id), "skill_id": str(r.skill_id), "completed_at": r.completed_at}
            for r in rows]


def ranked_resources(skill_id: str, db: Session) -> List[Dict]:
    """
    Fetch and rank all active resources for a skill.
    Returns resources sorted by: cost tier (free first) → difficulty → type priority.
    Sorted here rather than in SQL so cost_tier() is the only place that reads cost.
    """
    resources = db.execute(
        text("""
            SELECT
                resource_id,
                resource_title,
                resource_type,
                provider,
                url,
                duration_hours,
                cost,
                difficulty,
                description
            FROM recommendations_library
            WHERE skill_id = :sid
            AND is_active = TRUE
        """),
        {"sid": skill_id}
    ).fetchall()
    resources = sorted(resources, key=lambda r: (
        COST_TIER_ORDER[cost_tier(r.cost)],
        DIFFICULTY_ORDER.get(r.difficulty, 4),
        RESOURCE_TYPE_PRIORITY.get(r.resource_type, 7),
        r.resource_title,
    ))

    return [
        {
            "resource_id":    str(r.resource_id),
            "resource_title": r.resource_title,
            "resource_type":  r.resource_type,
            "provider":       r.provider,
            "url":            r.url,
            "duration_hours": r.duration_hours,
            "cost":           r.cost,
            "cost_tier":      cost_tier(r.cost),
            "difficulty":     r.difficulty,
            "description":    r.description,
        }
        for r in resources
    ]


def _generate_explanation(
    skill_name: str,
    gap_type: str,
    category: str,
    similarity_score: float,
    resource_count: int
) -> str:
    """
    Generate a plain-English explanation for why this skill was flagged.
    This is the 'explainable AI' component for transparency.
    """
    if gap_type == "gap":
        base = f"No evidence of {skill_name} was found in your profile."
        if resource_count > 0:
            base += f" {resource_count} learning resource{'s' if resource_count > 1 else ''} recommended below to get started."
        else:
            base += " Search online for introductory courses or tutorials."
 
    elif gap_type == "developing":
        pct = round(similarity_score * 100)
        base = f"You have some evidence of {skill_name} (similarity: {pct}%), but it needs further development to meet job requirements."
        if resource_count > 0:
            base += f" {resource_count} resource{'s' if resource_count > 1 else ''} recommended to strengthen this skill."
 
    else:
        base = f"{skill_name} has been flagged for development."
 
    return base
 
 
def _generate_summary(
    gap_count: int,
    developing_count: int,
    total_resources: int
) -> str:
    """Generate an overall summary message for the student."""
    if gap_count == 0 and developing_count == 0:
        return "You have no skill gaps for this role. Consider applying!"
 
    parts = []
    if gap_count > 0:
        parts.append(
            f"{gap_count} skill gap{'s' if gap_count > 1 else ''} identified "
            f"(skills not found in your profile)"
        )
    if developing_count > 0:
        parts.append(
            f"{developing_count} skill{'s' if developing_count > 1 else ''} "
            f"that need further development"
        )
 
    summary = "You have " + " and ".join(parts) + "."
 
    if total_resources > 0:
        summary += (
            f" We have found {total_resources} learning resource"
            f"{'s' if total_resources > 1 else ''} to help you close these gaps."
        )
 
    return summary
 
 
def get_career_path_recommendations(
    student_skills: List[Dict],
    db: Session,
    top_n: int = 5
) -> List[Dict]:
    """
    Optional (Sprint 3): Career path recommendation.
    Compares student skills against all job roles and ranks by match %.
 
    Args:
        student_skills: list of {skill_id, skill_name, proficiency_level}
        db: database session
        top_n: number of career paths to return
 
    Returns:
        List of career paths with match percentage
    """
    roles = db.execute(
        text("SELECT role_id, role_name, description FROM job_roles ORDER BY role_name")
    ).fetchall()
 
    student_skill_ids = {s["skill_id"] for s in student_skills}
    career_matches = []
 
    for role in roles:
        role_skills = db.execute(
            text("""
                SELECT skill_id, importance
                FROM job_role_skills
                WHERE role_id = :rid
            """),
            {"rid": str(role.role_id)}
        ).fetchall()
 
        if not role_skills:
            continue
 
        # Weighted match: required = 1.0, preferred = 0.6, bonus = 0.3
        importance_weights = {"required": 1.0, "preferred": 0.6, "bonus": 0.3}
        total_weight = 0
        matched_weight = 0
 
        for rs in role_skills:
            weight = importance_weights.get(rs.importance, 0.5)
            total_weight += weight
            if str(rs.skill_id) in student_skill_ids:
                matched_weight += weight
 
        match_pct = round(matched_weight / total_weight * 100, 1) if total_weight > 0 else 0
 
        career_matches.append({
            "role_id":     str(role.role_id),
            "role_name":   role.role_name,
            "match_pct":   match_pct,
            "description": role.description,
        })
 
    # Sort by match % descending
    career_matches.sort(key=lambda x: x["match_pct"], reverse=True)
    return career_matches[:top_n]