"""
SEAGAS — Jobs Router
Handles job description input, NLP trigger, job role templates
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
class JDCreate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    raw_text: str
    role_id: Optional[str] = None  # optional link to a job role template


# ── Job Role Templates ────────────────────────────────────────
@router.get("/roles")
def get_job_roles(db: Session = Depends(get_db)):
    """Get all 6 pre-built IT job role templates"""
    roles = db.execute(
        text("""
            SELECT role_id, role_name, role_code, description, industry_level
            FROM job_roles
            WHERE is_active = TRUE
            ORDER BY role_name
        """)
    ).fetchall()

    return [dict(r._mapping) for r in roles]


@router.get("/roles/{role_id}/skills")
def get_role_required_skills(role_id: str, db: Session = Depends(get_db)):
    """Get required skills for a specific job role template"""
    role = db.execute(
        text("SELECT * FROM job_roles WHERE role_id = :rid"),
        {"rid": role_id}
    ).fetchone()

    if not role:
        raise HTTPException(status_code=404, detail="Job role not found")

    skills = db.execute(
        text("""
            SELECT sl.skill_id, sl.skill_name, sl.category,
                   jrs.importance
            FROM job_role_skills jrs
            JOIN skills_library sl ON sl.skill_id = jrs.skill_id
            WHERE jrs.role_id = :rid
            ORDER BY jrs.importance, sl.category, sl.skill_name
        """),
        {"rid": role_id}
    ).fetchall()

    return {
        "role": dict(role._mapping),
        "required_skills": [dict(s._mapping) for s in skills]
    }


# ── Job Description Endpoints ─────────────────────────────────
@router.post("/descriptions", status_code=201)
def submit_job_description(
    req: JDCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Student submits a job description for NLP analysis"""

    # Validate JD text length
    if len(req.raw_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short. Please provide at least 50 characters."
        )

    # Get student profile
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Create your student profile first")

    # Insert JD — NLP status starts as 'pending'
    result = db.execute(
        text("""
            INSERT INTO job_descriptions
                (profile_id, role_id, title, company, raw_text, source, nlp_status)
            VALUES (:pid, :rid, :title, :company, :text, 'student_input', 'pending')
            RETURNING jd_id
        """),
        {
            "pid": str(profile.profile_id),
            "rid": req.role_id,
            "title": req.title,
            "company": req.company,
            "text": req.raw_text
        }
    )
    db.commit()

    jd_id = str(result.fetchone().jd_id)

    return {
        "message": "Job description submitted successfully",
        "jd_id": jd_id,
        "nlp_status": "pending",
        "next_step": f"POST /api/jobs/descriptions/{jd_id}/analyse to run NLP"
    }


@router.get("/descriptions")
def get_my_job_descriptions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all JDs submitted by this student"""
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    jds = db.execute(
        text("""
            SELECT jd.jd_id, jd.title, jd.company, jd.nlp_status,
                   jd.created_at, jr.role_name
            FROM job_descriptions jd
            LEFT JOIN job_roles jr ON jr.role_id = jd.role_id
            WHERE jd.profile_id = :pid
            ORDER BY jd.created_at DESC
        """),
        {"pid": str(profile.profile_id)}
    ).fetchall()

    return [dict(j._mapping) for j in jds]


@router.get("/descriptions/{jd_id}")
def get_job_description(
    jd_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific JD with its extracted skills"""
    jd = db.execute(
        text("SELECT * FROM job_descriptions WHERE jd_id = :jid"),
        {"jid": jd_id}
    ).fetchone()

    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    extracted = db.execute(
        text("""
            SELECT jes.raw_skill_text, jes.extraction_method,
                   jes.confidence_score, jes.importance,
                   sl.skill_name, sl.category
            FROM jd_extracted_skills jes
            LEFT JOIN skills_library sl ON sl.skill_id = jes.skill_id
            WHERE jes.jd_id = :jid
            ORDER BY jes.confidence_score DESC
        """),
        {"jid": jd_id}
    ).fetchall()

    return {
        "jd": dict(jd._mapping),
        "extracted_skills": [dict(e._mapping) for e in extracted]
    }


@router.post("/descriptions/{jd_id}/analyse")
def trigger_nlp_analysis(
    jd_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger NLP analysis on a submitted JD.
    In Sprint 2, this will call Yong Hin's NLP module.
    For now, returns a placeholder response.
    """
    jd = db.execute(
        text("SELECT * FROM job_descriptions WHERE jd_id = :jid"),
        {"jid": jd_id}
    ).fetchone()

    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    if jd.nlp_status == "complete":
        return {"message": "NLP already completed for this JD", "jd_id": jd_id}

    # Update status to processing
    db.execute(
        text("""
            UPDATE job_descriptions
            SET nlp_status = 'processing', nlp_processed_at = NOW()
            WHERE jd_id = :jid
        """),
        {"jid": jd_id}
    )
    db.commit()

    # ── TODO Sprint 2: Call Yong Hin's NLP module here ──
    # from nlp.extractor import extract_skills
    # extracted = extract_skills(jd.raw_text)
    # ... insert into jd_extracted_skills ...

    # Placeholder: mark as complete
    db.execute(
        text("UPDATE job_descriptions SET nlp_status = 'complete' WHERE jd_id = :jid"),
        {"jid": jd_id}
    )
    db.commit()

    return {
        "message": "NLP analysis triggered",
        "jd_id": jd_id,
        "status": "complete",
        "note": "Full NLP integration coming in Sprint 2"
    }