"""
SEAGAS — Students Router
Handles student profile CRUD, skills, projects, certifications
Author: Soh Way Miin (Carl)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────
class ProfileCreate(BaseModel):
    programme: Optional[str] = None
    university: Optional[str] = None
    gpa: Optional[float] = None
    expected_graduation: Optional[str] = None
    year_of_study: Optional[int] = None
    target_role: Optional[str] = None
    career_interests: Optional[List[str]] = []


class SkillAdd(BaseModel):
    skill_id: str
    proficiency_level: str = "intermediate"  # beginner | intermediate | advanced
    evidence_type: Optional[List[str]] = []
    evidence_notes: Optional[str] = None


class ProjectAdd(BaseModel):
    project_title: str
    description: Optional[str] = None
    technologies: Optional[List[str]] = []
    project_type: str = "academic"
    year_completed: Optional[int] = None


class CertificationAdd(BaseModel):
    cert_name: str
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = None


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
            SELECT ss.student_skill_id, sl.skill_name, sl.category,
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
        {"sid": req.skill_id}
    ).fetchone()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found in library")

    # Check duplicate
    existing = db.execute(
        text("""
            SELECT student_skill_id FROM student_skills
            WHERE profile_id = :pid AND skill_id = :sid
        """),
        {"pid": str(profile.profile_id), "sid": req.skill_id}
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
            "sid": req.skill_id,
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
    db.commit()
    return {"message": "Certification added successfully"}