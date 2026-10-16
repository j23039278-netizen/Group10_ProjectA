"""
SEAGAS — Students Router
Handles student profile CRUD, skills, projects, certifications
Author: Soh Way Miin (Carl)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import date
from uuid import UUID

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────
# Limits match the database columns and CHECKs, so bad input gets a 422 with a
# clear message instead of a database error (500).
class ProfileCreate(BaseModel):
    programme: Optional[str] = Field(None, max_length=255)
    university: Optional[str] = Field(None, max_length=255)
    gpa: Optional[float] = Field(None, ge=0, le=4)
    expected_graduation: Optional[str] = Field(None, max_length=20)
    year_of_study: Optional[int] = Field(None, ge=1, le=5)
    target_role: Optional[str] = Field(None, max_length=100)
    career_interests: Optional[List[str]] = Field([], max_length=20)


class SkillAdd(BaseModel):
    skill_id: UUID
    proficiency_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    evidence_type: Optional[List[Literal["project", "certification", "coursework", "internship"]]] = []
    evidence_notes: Optional[str] = Field(None, max_length=1000)


class ProjectAdd(BaseModel):
    project_title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    technologies: Optional[List[str]] = Field([], max_length=30)
    project_type: Literal["academic", "personal", "internship", "competition"] = "academic"
    year_completed: Optional[int] = Field(None, ge=1990, le=2100)


class CertificationAdd(BaseModel):
    cert_name: str = Field(min_length=1, max_length=255)
    issuer: Optional[str] = Field(None, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = None


def sync_experience_counts(db, profile_id):
    """Update the profile's project / certification / internship counters from its records.

    internship_count never goes down: synthetic profiles set it directly, without
    internship-type projects.
    """
    db.execute(
        text("""
            UPDATE student_profiles sp SET
                project_count       = (SELECT COUNT(*) FROM student_projects p
                                        WHERE p.profile_id = sp.profile_id),
                certification_count = (SELECT COUNT(*) FROM student_certifications c
                                        WHERE c.profile_id = sp.profile_id),
                internship_count    = GREATEST(COALESCE(sp.internship_count, 0),
                                       (SELECT COUNT(*) FROM student_projects p
                                        WHERE p.profile_id = sp.profile_id
                                          AND p.project_type = 'internship')),
                updated_at          = CURRENT_TIMESTAMP
            WHERE sp.profile_id = :pid
        """),
        {"pid": str(profile_id)}
    )


# ── Profile Endpoints ─────────────────────────────────────────
@router.get("/profile")
def get_my_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT * FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")

    return dict(profile._mapping)


@router.post("/profile", status_code=201)
def create_profile(
    req: ProfileCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can create profiles")

    # Check if profile already exists
    existing = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")

    db.execute(
        text("""
            INSERT INTO student_profiles
                (user_id, programme, university, gpa, expected_graduation,
                 year_of_study, target_role, career_interests)
            VALUES
                (:uid, :prog, :uni, :gpa, :grad, :year, :role, :interests)
        """),
        {
            "uid": str(current_user.user_id),
            "prog": req.programme,
            "uni": req.university,
            "gpa": req.gpa,
            "grad": req.expected_graduation,
            "year": req.year_of_study,
            "role": req.target_role,
            "interests": req.career_interests
        }
    )
    db.commit()
    return {"message": "Profile created successfully"}


@router.put("/profile")
def update_profile(
    req: ProfileCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.execute(
        text("""
            UPDATE student_profiles SET
                programme = :prog,
                university = :uni,
                gpa = :gpa,
                expected_graduation = :grad,
                year_of_study = :year,
                target_role = :role,
                career_interests = :interests,
                updated_at = NOW()
            WHERE user_id = :uid
        """),
        {
            "uid": str(current_user.user_id),
            "prog": req.programme,
            "uni": req.university,
            "gpa": req.gpa,
            "grad": req.expected_graduation,
            "year": req.year_of_study,
            "role": req.target_role,
            "interests": req.career_interests
        }
    )
    db.commit()
    return {"message": "Profile updated successfully"}


# ── Skills Endpoints ──────────────────────────────────────────
@router.get("/skills")
def get_my_skills(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skills = db.execute(
        text("""
            SELECT ss.student_skill_id, ss.skill_id, sl.skill_name, sl.category,
                   ss.proficiency_level, ss.evidence_type, ss.evidence_notes
            FROM student_skills ss
            JOIN student_profiles sp ON sp.profile_id = ss.profile_id
            JOIN skills_library sl   ON sl.skill_id   = ss.skill_id
            WHERE sp.user_id = :uid
            ORDER BY sl.category, sl.skill_name
        """),
        {"uid": str(current_user.user_id)}
    ).fetchall()

    return [dict(s._mapping) for s in skills]


@router.post("/skills", status_code=201)
def add_skill(
    req: SkillAdd,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Create your profile first")

    # Check skill exists in library
    skill = db.execute(
        text("SELECT skill_id FROM skills_library WHERE skill_id = :sid"),
        {"sid": str(req.skill_id)}
    ).fetchone()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found in library")

    # Check duplicate
    existing = db.execute(
        text("""
            SELECT student_skill_id FROM student_skills
            WHERE profile_id = :pid AND skill_id = :sid
        """),
        {"pid": str(profile.profile_id), "sid": str(req.skill_id)}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Skill already added")

    db.execute(
        text("""
            INSERT INTO student_skills
                (profile_id, skill_id, proficiency_level, evidence_type, evidence_notes)
            VALUES (:pid, :sid, :level, :etype, :enotes)
        """),
        {
            "pid": str(profile.profile_id),
            "sid": str(req.skill_id),
            "level": req.proficiency_level,
            "etype": req.evidence_type,
            "enotes": req.evidence_notes
        }
    )
    db.commit()
    return {"message": "Skill added successfully"}


@router.delete("/skills/{skill_id}")
def remove_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.execute(
        text("""
            DELETE FROM student_skills
            WHERE profile_id = :pid AND skill_id = :sid
        """),
        {"pid": str(profile.profile_id), "sid": skill_id}
    )
    db.commit()
    return {"message": "Skill removed"}


# ── Skills Library ────────────────────────────────────────────
@router.get("/skills-library")
def get_skills_library(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if category:
        skills = db.execute(
            text("""
                SELECT skill_id, skill_name, category, aliases, description
                FROM skills_library
                WHERE is_active = TRUE AND category = :cat
                ORDER BY skill_name
            """),
            {"cat": category}
        ).fetchall()
    else:
        skills = db.execute(
            text("""
                SELECT skill_id, skill_name, category, aliases, description
                FROM skills_library
                WHERE is_active = TRUE
                ORDER BY category, skill_name
            """)
        ).fetchall()

    return [dict(s._mapping) for s in skills]


# ── Projects Endpoints ────────────────────────────────────────
@router.get("/projects")
def get_my_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    projects = db.execute(
        text("SELECT * FROM student_projects WHERE profile_id = :pid ORDER BY year_completed DESC"),
        {"pid": str(profile.profile_id)}
    ).fetchall()

    return [dict(p._mapping) for p in projects]


@router.post("/projects", status_code=201)
def add_project(
    req: ProjectAdd,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Create your profile first")

    db.execute(
        text("""
            INSERT INTO student_projects
                (profile_id, project_title, description, technologies, project_type, year_completed)
            VALUES (:pid, :title, :desc, :tech, :ptype, :year)
        """),
        {
            "pid": str(profile.profile_id),
            "title": req.project_title,
            "desc": req.description,
            "tech": req.technologies,
            "ptype": req.project_type,
            "year": req.year_completed
        }
    )
    sync_experience_counts(db, profile.profile_id)
    db.commit()
    return {"message": "Project added successfully"}


# ── Certifications Endpoints ──────────────────────────────────
@router.get("/certifications")
def get_my_certifications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    certs = db.execute(
        text("SELECT * FROM student_certifications WHERE profile_id = :pid ORDER BY issue_date DESC"),
        {"pid": str(profile.profile_id)}
    ).fetchall()

    return [dict(c._mapping) for c in certs]


@router.post("/certifications", status_code=201)
def add_certification(
    req: CertificationAdd,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Create your profile first")

    db.execute(
        text("""
            INSERT INTO student_certifications
                (profile_id, cert_name, issuer, issue_date, expiry_date, credential_url)
            VALUES (:pid, :name, :issuer, :idate, :edate, :url)
        """),
        {
            "pid": str(profile.profile_id),
            "name": req.cert_name,
            "issuer": req.issuer,
            "idate": req.issue_date,
            "edate": req.expiry_date,
            "url": req.credential_url
        }
    )
    sync_experience_counts(db, profile.profile_id)
    db.commit()
    return {"message": "Certification added successfully"}