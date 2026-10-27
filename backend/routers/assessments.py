"""
SEAGAS — Assessments Router
Handles skill matching, readiness score, skill gap analysis, recommendations
Author: Soh Way Miin (Carl) — Backend Developer
Recommendation Engine: Tan Jun Xiong (Aaron) — Co-Leader
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add project root to path so recommendation/ module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import access
import assessment_service
import audit
import nlp_service
from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────
class AssessmentRequest(BaseModel):
    jd_id: Optional[str] = None       # if student uploaded a JD
    role_id: Optional[str] = None     # if student selected a template
    matching_method: str = nlp_service.DEFAULT_METHOD  # keyword | semantic | hybrid


# ── Assessment Endpoints ──────────────────────────────────────
@router.post("/run", status_code=201)
def run_assessment(
    req: AssessmentRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run skill matching and generate the readiness score (assessment_service.py).
    Scoring weights: required=3, preferred=2, bonus=1; strong = full points,
    developing = half, gap = 0. Strong / Developing / Gap comes from the NLP
    matcher (Ng Yong Hin, nlp/); rules in docs/NLP_CLASSIFICATION_RULES.md.
    """
    profile = db.execute(
        text("SELECT * FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail="Create your student profile first")
    if req.jd_id:
        access.get_jd_or_404(db, current_user, req.jd_id)
    elif req.role_id and current_user.role == "student":
        # Role templates are offered per course (job_roles.courses)
        try:
            offered = db.execute(text("SELECT CAST(:c AS VARCHAR) = ANY(courses) FROM job_roles WHERE role_id = CAST(:r AS uuid)"),
                                 {"c": current_user.course, "r": req.role_id}).scalar()
        except Exception:
            db.rollback()
            offered = None
        if offered is None:
            raise HTTPException(status_code=404, detail="Job role not found")
        if not offered:
            raise HTTPException(status_code=400, detail="This role is not offered to your course.")

    try:
        result = assessment_service.run_for_profile(
            db, profile, role_id=req.role_id, jd_id=req.jd_id,
            method=req.matching_method, commit=False)
    except assessment_service.AssessmentError as e:
        raise HTTPException(status_code=e.status, detail=e.detail)

    audit.record(db, "assessment.run", user=current_user, request=request,
                 target_type="assessment", target_id=result["assessment_id"],
                 details={"role_id": req.role_id, "jd_id": req.jd_id,
                          "method": result["matching_method"],
                          "readiness_score": result["readiness_score"]})
    db.commit()
    return result


@router.get("/my/history")
def get_assessment_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all past assessments for this student"""
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    history = db.execute(
        text("""
            SELECT a.assessment_id, a.readiness_score, a.matching_method,
                   a.created_at, jr.role_name,
                   a.score_technical, a.score_ai_digital, a.score_analytical,
                   a.score_communication, a.score_industry_exp,
                   a.score_project_exp, a.score_certification
            FROM assessments a
            LEFT JOIN job_roles jr ON jr.role_id = a.role_id
            WHERE a.profile_id = :pid
            ORDER BY a.created_at DESC
        """),
        {"pid": str(profile.profile_id)}
    ).fetchall()

    return [dict(h._mapping) for h in history]


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific assessment with full skill breakdown (own, or any for staff)"""
    assessment = access.get_assessment_or_404(db, current_user, assessment_id)

    match_results = db.execute(
        text("""
            SELECT sl.skill_name, sl.category,
                   smr.match_status, smr.similarity_score, smr.matching_method,
                   smr.matched_student_skill, smr.reason
            FROM skill_match_results smr
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            WHERE smr.assessment_id = :aid
            ORDER BY
                CASE smr.match_status
                    WHEN 'strong'     THEN 1
                    WHEN 'developing' THEN 2
                    WHEN 'gap'        THEN 3
                END,
                sl.skill_name
        """),
        {"aid": assessment_id}
    ).fetchall()

    return {
        "assessment":    dict(assessment._mapping),
        "match_results": [dict(m._mapping) for m in match_results]
    }


@router.get("/{assessment_id}/recommendations")
def get_assessment_recommendations(
    assessment_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalised recommendations for skill gaps in this assessment.
    Uses Aaron's rule-based recommendation engine (recommendation/engine.py).
    Author: Tan Jun Xiong (Aaron)
    """
    access.get_assessment_or_404(db, current_user, assessment_id)
    try:
        from recommendation.engine import get_recommendations_for_assessment
        return get_recommendations_for_assessment(
            assessment_id=assessment_id,
            db=db,
            max_resources_per_skill=3,
            include_developing=True
        )
    except ImportError:
        # Fallback if engine module not found
        gaps = db.execute(
            text("""
                SELECT smr.skill_id, sl.skill_name, smr.match_status
                FROM skill_match_results smr
                JOIN skills_library sl ON sl.skill_id = smr.skill_id
                WHERE smr.assessment_id = :aid
                AND smr.match_status IN ('gap', 'developing')
                ORDER BY smr.match_status, sl.skill_name
            """),
            {"aid": assessment_id}
        ).fetchall()

        recommendations = []
        for gap in gaps:
            resources = db.execute(
                text("""
                    SELECT resource_id, resource_title, resource_type,
                           provider, url, duration_hours, cost, difficulty, description
                    FROM recommendations_library
                    WHERE skill_id = :sid AND is_active = TRUE
                    ORDER BY difficulty
                    LIMIT 3
                """),
                {"sid": str(gap.skill_id)}
            ).fetchall()

            recommendations.append({
                "skill_name": gap.skill_name,
                "gap_type":   gap.match_status,
                "resources":  [dict(r._mapping) for r in resources]
            })

        return {"assessment_id": assessment_id, "recommendations": recommendations}