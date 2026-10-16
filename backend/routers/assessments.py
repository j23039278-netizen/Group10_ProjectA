"""
SEAGAS — Assessments Router
Handles skill matching, readiness score, skill gap analysis, recommendations
Author: Soh Way Miin (Carl) — Backend Developer
Recommendation Engine: Tan Jun Xiong (Aaron) — Co-Leader
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add project root to path so recommendation/ module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import access
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run skill matching and generate readiness score.
    Scoring weights: required=3pts, preferred=2pts, bonus=1pt.
    Strong match = full points, Developing = half points, Gap = 0.
    Strong / Developing / Gap comes from the NLP matcher (Ng Yong Hin, nlp/);
    rules in docs/NLP_CLASSIFICATION_RULES.md.
    """
    try:
        nlp_service.check_method(req.matching_method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        access.get_jd_or_404(db, current_user, req.jd_id)
        required_skills = db.execute(
            text("""
                SELECT jes.skill_id,
                       COALESCE(sl.skill_name, jes.raw_skill_text) AS skill_name,
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
                ORDER BY
                    CASE jrs.importance
                        WHEN 'required'  THEN 1
                        WHEN 'preferred' THEN 2
                        WHEN 'bonus'     THEN 3
                    END
            """),
            {"rid": req.role_id}
        ).fetchall()

    if not required_skills:
        raise HTTPException(
            status_code=400,
            detail="No skills were found in this job description. Run the analysis first, "
                   "or paste a longer description." if req.jd_id
                   else "No required skills found for this role"
        )

    # ── Matching Logic (nlp/, rules in docs/NLP_CLASSIFICATION_RULES.md) ──
    students = [{"skill_id": str(sk.skill_id), "skill_name": sk.skill_name,
                 "proficiency_level": sk.proficiency_level,
                 "evidence_type": list(sk.evidence_type or [])} for sk in student_skills]
    required = [{"skill_id": str(r.skill_id) if r.skill_id else None,
                 "skill_name": r.skill_name,
                 "importance": r.importance or "required"} for r in required_skills]
    try:
        match_results, method_used, matching_note = nlp_service.match_skills(
            students, required, req.matching_method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Weighted scoring: required=3, preferred=2, bonus=1; strong=1, developing=0.5, gap=0
    IMPORTANCE_WEIGHTS = {"required": 3, "preferred": 2, "bonus": 1}
    STATUS_CREDIT      = {"strong": 1.0, "developing": 0.5, "gap": 0.0}

    earned_points = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) * STATUS_CREDIT[m["match_status"]]
                        for m in match_results)
    max_points    = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) for m in match_results)
    strong_count     = sum(m["match_status"] == "strong" for m in match_results)
    developing_count = sum(m["match_status"] == "developing" for m in match_results)
    gap_count        = sum(m["match_status"] == "gap" for m in match_results)

    # ── Calculate Readiness Score (weighted) ──────────────────
    readiness_score = round(
        earned_points / max_points * 100, 2
    ) if max_points > 0 else 0

    # ── Calculate 7-Dimension Scores ─────────────────────────
    # match_results are in the same order as required_skills
    def category_score(category):
        """Weighted score within one skill category; developing counts half"""
        rows = [m for r, m in zip(required_skills, match_results) if r.category == category]
        if not rows:
            return None
        cat_max    = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) for m in rows)
        cat_earned = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) * STATUS_CREDIT[m["match_status"]]
                         for m in rows)
        return round(cat_earned / cat_max * 100, 2) if cat_max > 0 else 0

    score_technical     = category_score("Technical")
    score_ai_digital    = category_score("AI_Digital")
    score_analytical    = category_score("Analytical")
    score_communication = category_score("Soft")

    # Experience-based scores, counted from the student's records so that adding a
    # project or certification changes them. internship_count is also a profile
    # field (synthetic data sets it directly), so the larger of the two is used.
    exp = db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM student_projects WHERE profile_id = :pid)       AS projects,
                (SELECT COUNT(*) FROM student_projects
                  WHERE profile_id = :pid AND project_type = 'internship')            AS internship_projects,
                (SELECT COUNT(*) FROM student_certifications WHERE profile_id = :pid) AS certifications
        """),
        {"pid": str(profile.profile_id)}
    ).fetchone()
    internships = max(profile.internship_count or 0, exp.internship_projects)
    score_industry_exp  = min(internships * 50, 100)
    score_project_exp   = min(exp.projects * 25, 100)
    score_certification = min(exp.certifications * 33, 100)

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
            "pid":        str(profile.profile_id),
            "jid":        req.jd_id,
            "rid":        req.role_id,
            "method":     method_used,
            "score":      readiness_score,
            "tech":       score_technical,
            "ai":         score_ai_digital,
            "analytical": score_analytical,
            "comm":       score_communication,
            "ind":        score_industry_exp,
            "proj":       score_project_exp,
            "cert":       score_certification
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
                        (assessment_id, skill_id, match_status, similarity_score,
                         matching_method, matched_student_skill, reason)
                    VALUES (:aid, :sid, :status, :score, :method, :matched, :reason)
                    ON CONFLICT (assessment_id, skill_id) DO NOTHING
                """),
                {
                    "aid":     assessment_id,
                    "sid":     mr["skill_id"],
                    "status":  mr["match_status"],
                    "score":   mr["similarity_score"],      # already 3 decimals
                    "method":  mr["matching_method"],
                    "matched": mr["matched_student_skill"],
                    "reason":  mr["reason"]
                }
            )
    db.commit()

    return {
        "assessment_id":   assessment_id,
        "readiness_score": readiness_score,
        "scoring_method":  "weighted (required=3, preferred=2, bonus=1)",
        "matching_method": method_used,
        "matching_note":   matching_note,
        "dimension_scores": {
            "technical_skills":    score_technical,
            "ai_digital_skills":   score_ai_digital,
            "analytical_skills":   score_analytical,
            "communication":       score_communication,
            "industry_experience": score_industry_exp,
            "project_experience":  score_project_exp,
            "certification":       score_certification
        },
        "skill_summary": {
            "strong":     strong_count,
            "developing": developing_count,
            "gaps":       gap_count,
            "total":      len(required_skills),
            "earned_points": earned_points,
            "max_points":    max_points
        },
        "match_results": match_results
    }


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