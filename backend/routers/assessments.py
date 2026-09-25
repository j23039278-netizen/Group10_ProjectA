"""
SEAGAS — Assessments Router
Handles skill matching, readiness score, skill gap analysis, recommendations
Author: Soh Way Miin (Carl)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────
class AssessmentRequest(BaseModel):
    jd_id: Optional[str] = None      # if student uploaded a JD
    role_id: Optional[str] = None    # if student selected a template
    matching_method: str = "semantic" # keyword | semantic | hybrid


# ── Assessment Endpoints ──────────────────────────────────────
@router.post("/run", status_code=201)
def run_assessment(
    req: AssessmentRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run skill matching and generate readiness score.
    Sprint 1: placeholder scoring logic.
    Sprint 2: connects to Yong Hin's matching engine.
    """
    if not req.jd_id and not req.role_id:
        raise HTTPException(
            status_code=400,
            detail="Provide either a jd_id or a role_id"
        )

    # Get student profile
    profile = db.execute(
        text("SELECT * FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Create your student profile first")

    # Get student skills
    student_skills = db.execute(
        text("""
            SELECT sl.skill_id, sl.skill_name, sl.category,
                   ss.proficiency_level, ss.evidence_type
            FROM student_skills ss
            JOIN skills_library sl ON sl.skill_id = ss.skill_id
            WHERE ss.profile_id = :pid
        """),
        {"pid": str(profile.profile_id)}
    ).fetchall()

    if not student_skills:
        raise HTTPException(
            status_code=400,
            detail="Add at least one skill to your profile before running assessment"
        )

    # Get required skills — from JD or role template
    if req.jd_id:
        required_skills = db.execute(
            text("""
                SELECT jes.skill_id, jes.raw_skill_text AS skill_name,
                       sl.category, jes.importance
                FROM jd_extracted_skills jes
                LEFT JOIN skills_library sl ON sl.skill_id = jes.skill_id
                WHERE jes.jd_id = :jid
            """),
            {"jid": req.jd_id}
        ).fetchall()
    else:
        required_skills = db.execute(
            text("""
                SELECT sl.skill_id, sl.skill_name, sl.category, jrs.importance
                FROM job_role_skills jrs
                JOIN skills_library sl ON sl.skill_id = jrs.skill_id
                WHERE jrs.role_id = :rid
            """),
            {"rid": req.role_id}
        ).fetchall()

    if not required_skills:
        raise HTTPException(
            status_code=400,
            detail="No required skills found for this job/role"
        )

    # ── Placeholder Matching Logic (Sprint 1) ─────────────────
    # Sprint 2: replace with Yong Hin's NLP matching engine
    student_skill_ids = {str(s.skill_id) for s in student_skills}
    student_skill_names = {s.skill_name.lower() for s in student_skills}

    match_results = []
    strong_count = 0
    developing_count = 0
    gap_count = 0

    for req_skill in required_skills:
        skill_id = str(req_skill.skill_id) if req_skill.skill_id else None
        skill_name = req_skill.skill_name.lower() if req_skill.skill_name else ""

        # Level 1: exact ID match
        if skill_id and skill_id in student_skill_ids:
            status = "strong"
            similarity = 1.0
            strong_count += 1
        # Level 1: keyword match on name
        elif any(skill_name in sn or sn in skill_name for sn in student_skill_names):
            status = "developing"
            similarity = 0.6
            developing_count += 1
        else:
            status = "gap"
            similarity = 0.0
            gap_count += 1

        match_results.append({
            "skill_id": skill_id,
            "skill_name": req_skill.skill_name,
            "match_status": status,
            "similarity_score": similarity,
            "matching_method": req.matching_method
        })

    # ── Calculate 7-Dimension Scores ─────────────────────────
    total = len(required_skills)
    readiness_score = round(
        (strong_count * 1.0 + developing_count * 0.5) / total * 100, 2
    ) if total > 0 else 0

    # Dimension scores based on category
    def category_score(category):
        cat_required = [r for r in required_skills if r.category == category]
        if not cat_required:
            return None
        cat_student = [s for s in student_skills if s.category == category]
        student_cat_ids = {str(s.skill_id) for s in cat_student}
        matched = sum(1 for r in cat_required if str(r.skill_id) in student_cat_ids)
        return round(matched / len(cat_required) * 100, 2)

    score_technical     = category_score("Technical")
    score_ai_digital    = category_score("AI_Digital")
    score_analytical    = category_score("Analytical")
    score_communication = category_score("Soft")

    # Experience-based scores (from profile counts)
    score_industry_exp  = min(profile.internship_count * 50, 100) if profile.internship_count else 0
    score_project_exp   = min(profile.project_count * 25, 100) if profile.project_count else 0
    score_certification = min(profile.certification_count * 33, 100) if profile.certification_count else 0

    # ── Save Assessment to DB ─────────────────────────────────
    result = db.execute(
        text("""
            INSERT INTO assessments (
                profile_id, jd_id, role_id, matching_method,
                readiness_score,
                score_technical, score_ai_digital, score_analytical,
                score_communication, score_industry_exp,
                score_project_exp, score_certification
            ) VALUES (
                :pid, :jid, :rid, :method,
                :score,
                :tech, :ai, :analytical,
                :comm, :ind, :proj, :cert
            ) RETURNING assessment_id
        """),
        {
            "pid": str(profile.profile_id),
            "jid": req.jd_id,
            "rid": req.role_id,
            "method": req.matching_method,
            "score": readiness_score,
            "tech": score_technical,
            "ai": score_ai_digital,
            "analytical": score_analytical,
            "comm": score_communication,
            "ind": score_industry_exp,
            "proj": score_project_exp,
            "cert": score_certification
        }
    )
    db.commit()
    assessment_id = str(result.fetchone().assessment_id)

    # Save individual skill match results
    for mr in match_results:
        if mr["skill_id"]:
            db.execute(
                text("""
                    INSERT INTO skill_match_results
                        (assessment_id, skill_id, match_status,
                         similarity_score, matching_method)
                    VALUES (:aid, :sid, :status, :score, :method)
                    ON CONFLICT (assessment_id, skill_id) DO NOTHING
                """),
                {
                    "aid": assessment_id,
                    "sid": mr["skill_id"],
                    "status": mr["match_status"],
                    "score": mr["similarity_score"],
                    "method": mr["matching_method"]
                }
            )
    db.commit()

    return {
        "assessment_id": assessment_id,
        "readiness_score": readiness_score,
        "dimension_scores": {
            "technical_skills":   score_technical,
            "ai_digital_skills":  score_ai_digital,
            "analytical_skills":  score_analytical,
            "communication":      score_communication,
            "industry_experience": score_industry_exp,
            "project_experience": score_project_exp,
            "certification":      score_certification
        },
        "skill_summary": {
            "strong":     strong_count,
            "developing": developing_count,
            "gaps":       gap_count,
            "total":      total
        },
        "match_results": match_results
    }


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific assessment with full skill breakdown"""
    assessment = db.execute(
        text("SELECT * FROM assessments WHERE assessment_id = :aid"),
        {"aid": assessment_id}
    ).fetchone()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    match_results = db.execute(
        text("""
            SELECT sl.skill_name, sl.category,
                   smr.match_status, smr.similarity_score, smr.matching_method
            FROM skill_match_results smr
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            WHERE smr.assessment_id = :aid
            ORDER BY smr.match_status, sl.skill_name
        """),
        {"aid": assessment_id}
    ).fetchall()

    return {
        "assessment": dict(assessment._mapping),
        "match_results": [dict(m._mapping) for m in match_results]
    }


@router.get("/{assessment_id}/recommendations")
def get_assessment_recommendations(
    assessment_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommendations for skill gaps in this assessment"""
    gaps = db.execute(
        text("""
            SELECT smr.skill_id, sl.skill_name, smr.match_status
            FROM skill_match_results smr
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            WHERE smr.assessment_id = :aid
            AND smr.match_status IN ('gap', 'developing')
            ORDER BY smr.match_status
        """),
        {"aid": assessment_id}
    ).fetchall()

    recommendations = []
    for gap in gaps:
        resources = db.execute(
            text("""
                SELECT resource_id, resource_title, resource_type,
                       provider, url, duration_hours, cost, difficulty
                FROM recommendations_library
                WHERE skill_id = :sid AND is_active = TRUE
                ORDER BY difficulty
                LIMIT 2
            """),
            {"sid": str(gap.skill_id)}
        ).fetchall()

        recommendations.append({
            "skill_name": gap.skill_name,
            "gap_type": gap.match_status,
            "resources": [dict(r._mapping) for r in resources]
        })

    return {"assessment_id": assessment_id, "recommendations": recommendations}


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
                   a.created_at, jr.role_name
            FROM assessments a
            LEFT JOIN job_roles jr ON jr.role_id = a.role_id
            WHERE a.profile_id = :pid
            ORDER BY a.created_at DESC
        """),
        {"pid": str(profile.profile_id)}
    ).fetchall()

    return [dict(h._mapping) for h in history]