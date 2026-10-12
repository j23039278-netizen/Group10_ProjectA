"""
SEAGAS — Recommendation Engine
Rule-based engine that maps identified skill gaps to development resources.
Author: Tan Jun Xiong (Aaron) — Co-Leader & Recommendation Engine Developer
 
Logic:
  1. Receive skill gaps from assessment results (gap / developing)
  2. Look up matching resources in recommendations_library
  3. Prioritise by: gap > developing, difficulty order, resource type order
  4. Return ranked recommendations with explanation
"""
 
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
 
 
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
 
# ── Gap type priority (gaps first, then developing) ───────────
GAP_TYPE_PRIORITY = {
    "gap":        1,
    "developing": 2,
}
 
 
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
 
    # Step 1: Get skill gaps from assessment
    gap_filter = "('gap', 'developing')" if include_developing else "('gap')"
 
    gaps = db.execute(
        text(f"""
            SELECT
                smr.skill_id,
                sl.skill_name,
                sl.category,
                smr.match_status,
                smr.similarity_score
            FROM skill_match_results smr
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            WHERE smr.assessment_id = :aid
            AND smr.match_status IN {gap_filter}
            ORDER BY
                CASE smr.match_status
                    WHEN 'gap'        THEN 1
                    WHEN 'developing' THEN 2
                END,
                sl.skill_name
        """),
        {"aid": assessment_id}
    ).fetchall()
 
    if not gaps:
        return {
            "assessment_id": assessment_id,
            "total_gaps":    0,
            "recommendations": [],
            "message": "No skill gaps found — great job!"
        }
 
    # Step 2: Get resources for each gap
    recommendations = []
 
    for gap in gaps:
        resources = _get_resources_for_skill(
            skill_id=str(gap.skill_id),
            db=db,
            max_resources=max_resources_per_skill,
            gap_type=gap.match_status
        )
 
        explanation = _generate_explanation(
            skill_name=gap.skill_name,
            gap_type=gap.match_status,
            category=gap.category,
            similarity_score=gap.similarity_score,
            resource_count=len(resources)
        )
 
        recommendations.append({
            "skill_id":    str(gap.skill_id),
            "skill_name":  gap.skill_name,
            "category":    gap.category,
            "gap_type":    gap.match_status,
            "similarity":  gap.similarity_score,
            "explanation": explanation,
            "resources":   resources,
            "priority":    GAP_TYPE_PRIORITY.get(gap.match_status, 99)
        })
 
    # Step 3: Sort by priority (gaps first)
    recommendations.sort(key=lambda x: x["priority"])
 
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
        "summary": _generate_summary(gap_count, developing_count, total_resources)
    }
 
 
def _get_resources_for_skill(
    skill_id: str,
    db: Session,
    max_resources: int = 3,
    gap_type: str = "gap"
) -> List[Dict]:
    """
    Fetch and rank resources for a specific skill gap.
    Returns resources sorted by: difficulty → type priority
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
            ORDER BY
                CASE difficulty
                    WHEN 'beginner'     THEN 1
                    WHEN 'intermediate' THEN 2
                    WHEN 'advanced'     THEN 3
                    ELSE 4
                END,
                CASE resource_type
                    WHEN 'course'        THEN 1
                    WHEN 'certification' THEN 2
                    WHEN 'project'       THEN 3
                    WHEN 'workshop'      THEN 4
                    WHEN 'competition'   THEN 5
                    ELSE 6
                END
            LIMIT :limit
        """),
        {"sid": skill_id, "limit": max_resources}
    ).fetchall()
 
    return [
        {
            "resource_id":    str(r.resource_id),
            "resource_title": r.resource_title,
            "resource_type":  r.resource_type,
            "provider":       r.provider,
            "url":            r.url,
            "duration_hours": r.duration_hours,
            "cost":           r.cost,
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