"""
SEAGAS — Student work experience (internships, part-time and full-time jobs, freelance, volunteering)

GET    /api/students/experiences
POST   /api/students/experiences
PUT    /api/students/experiences/{experience_id}
DELETE /api/students/experiences/{experience_id}

Paid / professional experience (everything but volunteering) counts towards the
Industry Experience dimension of an assessment (assessment_service.py).
"""

from datetime import date
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user
from routers.students import ensure_profile, get_profile_id, sync_experience_counts

router = APIRouter()

EXPERIENCE_TYPES = Literal["internship", "part_time", "full_time", "freelance", "volunteer"]
COLUMNS = """experience_id, job_title, company, experience_type, location, start_date, end_date,
             description, created_at"""


class ExperienceIn(BaseModel):
    job_title: str = Field(min_length=1, max_length=150)
    company: str = Field(min_length=1, max_length=150)
    experience_type: EXPERIENCE_TYPES = "internship"
    location: Optional[str] = Field(None, max_length=150)
    start_date: date
    end_date: Optional[date] = None          # empty: still working there
    description: Optional[str] = Field(None, max_length=3000)

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date > date.today():
            raise ValueError("The start date cannot be in the future.")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("The end date cannot be before the start date.")
        return self


def values(req, **extra):
    return {"title": req.job_title.strip(), "company": req.company.strip(), "type": req.experience_type,
            "location": (req.location or "").strip() or None, "start": req.start_date, "end": req.end_date,
            "desc": (req.description or "").strip() or None, **extra}


def list_experiences(db, profile_id):
    rows = db.execute(text(f"""
        SELECT {COLUMNS} FROM student_experiences WHERE profile_id = :pid
        ORDER BY (end_date IS NULL) DESC, COALESCE(end_date, start_date) DESC, start_date DESC
    """), {"pid": str(profile_id)}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("")
def get_my_experiences(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.execute(text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
                         {"uid": str(current_user.user_id)}).fetchone()
    return list_experiences(db, profile.profile_id) if profile else []


@router.post("", status_code=201)
def add_experience(req: ExperienceIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = ensure_profile(db, current_user)
    row = db.execute(text("""
        INSERT INTO student_experiences
            (profile_id, job_title, company, experience_type, location, start_date, end_date, description)
        VALUES (:pid, :title, :company, :type, :location, :start, :end, :desc)
        RETURNING experience_id
    """), values(req, pid=str(profile.profile_id))).fetchone()
    sync_experience_counts(db, profile.profile_id)
    db.commit()
    return {"message": "Experience added", "experience_id": str(row.experience_id)}


@router.put("/{experience_id}")
def update_experience(experience_id: UUID, req: ExperienceIn,
                      current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile_id = get_profile_id(db, current_user)
    updated = db.execute(text("""
        UPDATE student_experiences SET job_title = :title, company = :company, experience_type = :type,
               location = :location, start_date = :start, end_date = :end, description = :desc
        WHERE experience_id = :eid AND profile_id = :pid
        RETURNING experience_id
    """), values(req, eid=str(experience_id), pid=str(profile_id))).fetchone()
    if not updated:
        raise HTTPException(status_code=404, detail="Experience not found")
    sync_experience_counts(db, profile_id)
    db.commit()
    return {"message": "Experience updated"}


@router.delete("/{experience_id}")
def delete_experience(experience_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile_id = get_profile_id(db, current_user)
    deleted = db.execute(text("""
        DELETE FROM student_experiences WHERE experience_id = :eid AND profile_id = :pid RETURNING experience_id
    """), {"eid": str(experience_id), "pid": str(profile_id)}).fetchone()
    if not deleted:
        raise HTTPException(status_code=404, detail="Experience not found")
    sync_experience_counts(db, profile_id)
    db.commit()
    return {"message": "Experience deleted"}
