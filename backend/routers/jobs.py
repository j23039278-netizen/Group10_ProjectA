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

import access
import nlp_service
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
            ORDER BY
                CASE jrs.importance
                    WHEN 'required'  THEN 1
                    WHEN 'preferred' THEN 2
                    WHEN 'bonus'     THEN 3
                END,
                sl.category, sl.skill_name
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
    """Get a specific JD with its extracted skills (own or shared, any for staff)"""
    jd = access.get_jd_or_404(db, current_user, jd_id)

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
    method: str = nlp_service.DEFAULT_METHOD,   # keyword | semantic | hybrid
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract the skills a JD asks for with the NLP module (Ng Yong Hin, nlp/)
    and store them in jd_extracted_skills. Running it again replaces the
    previous results, so a JD can be re-analysed with another method.
    Contract: docs/NLP_INTERFACE.md.
    """
    # Students can only re-analyse their own JDs; shared dataset JDs are staff-only
    jd = access.get_jd_or_404(db, current_user, jd_id, for_update=True)

    try:
        nlp_service.check_method(method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.execute(
        text("""
            UPDATE job_descriptions
            SET nlp_status = 'processing', nlp_processed_at = NOW()
            WHERE jd_id = :jid
        """),
        {"jid": jd_id}
    )
    db.commit()

    # Pass the skills_library rows so every result carries the real skill_id
    skills = db.execute(text("""
        SELECT skill_id, skill_name, category, aliases, description, is_active
        FROM skills_library
    """)).fetchall()
    try:
        extracted, method_used, note = nlp_service.extract_skills(
            jd.raw_text, method, [dict(r._mapping) for r in skills])
    except Exception:
        db.execute(text("UPDATE job_descriptions SET nlp_status = 'failed' WHERE jd_id = :jid"),
                   {"jid": jd_id})
        db.commit()
        raise HTTPException(status_code=500, detail="Skill extraction failed")

    db.execute(text("DELETE FROM jd_extracted_skills WHERE jd_id = :jid"), {"jid": jd_id})
    for s in extracted:
        db.execute(text("""
            INSERT INTO jd_extracted_skills
                (jd_id, skill_id, raw_skill_text, extraction_method, confidence_score)
            VALUES (:jid, :sid, :raw, :method, :conf)
        """), {"jid": jd_id, "sid": s["skill_id"], "raw": s["raw_skill_text"][:255],
               # per-skill extractor: always keyword or semantic, never hybrid
               "method": s["method"], "conf": round(s["confidence_score"], 3)})

    db.execute(
        text("UPDATE job_descriptions SET nlp_status = 'complete', nlp_processed_at = NOW() WHERE jd_id = :jid"),
        {"jid": jd_id}
    )
    db.commit()

    return {
        "jd_id": jd_id,
        "status": "complete",
        "method_requested": method,
        "method_used": method_used,
        "note": note,
        "skill_count": len(extracted),
        "extracted_skills": [
            {"skill_id": s["skill_id"], "skill_name": s["skill_name"],
             "raw_skill_text": s["raw_skill_text"], "extraction_method": s["method"],
             "confidence_score": round(s["confidence_score"], 3)}
            for s in extracted
        ],
    }
