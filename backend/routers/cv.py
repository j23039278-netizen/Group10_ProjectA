"""
SEAGAS — Student CV: upload a CV and pick up the skills it mentions

POST   /api/students/cv          upload (PDF / .docx, 5 MB); replaces the old CV;
                                 returns the skills found in it
GET    /api/students/cv          the stored CV and the skills found in it
GET    /api/students/cv/file     download the stored CV
DELETE /api/students/cv          remove it
POST   /api/students/cv/skills   add the skills the student ticked

Skills are found with the NLP module (nlp_service.extract_skills, the same call as
the job-description analysis). Only skills in the skills library can be found:
student skills must point to a library skill so skill-gap analysis can use them.
A found skill outside the student's course list is shown but cannot be added.
Nothing is added without the student's confirmation.
"""

from typing import List, Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import evidence
import nlp_service
from cv_text import read_cv
from database import get_db
from routers.auth import get_current_user
from routers.students import ensure_profile, refresh_profile_complete

router = APIRouter()

MIN_TEXT = 30                   # fewer characters than this: probably a scanned image
CONTEXT = 50                    # characters of CV text shown around each found skill


class PickedSkill(BaseModel):
    skill_id: UUID
    proficiency_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"


class PickedSkills(BaseModel):
    skills: List[PickedSkill] = Field(min_length=1, max_length=200)


def require_student(user):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a CV here.")


def stored_cv(db, profile_id):
    return db.execute(text("""
        SELECT file_name, content_type, size_bytes, extracted_text, uploaded_at
        FROM student_cvs WHERE profile_id = :pid
    """), {"pid": str(profile_id)}).fetchone()


def snippet(cv, start, end):
    """The found text with a little context, on one line"""
    a, b = max(0, start - CONTEXT), min(len(cv), end + CONTEXT)
    return ("…" if a else "") + " ".join(cv[a:b].split()) + ("…" if b < len(cv) else "")


def found_skills(db, user, profile_id, cv, method):
    """Library skills mentioned in the CV, one entry per skill"""
    rows = [dict(r._mapping) for r in db.execute(text("""
        SELECT skill_id, skill_name, category, aliases, description, is_active, courses FROM skills_library
    """)).fetchall()]
    by_id = {str(r["skill_id"]): r for r in rows}
    catalogue = [{k: v for k, v in r.items() if k != "courses"} for r in rows]
    try:
        extracted, method_used, note = nlp_service.extract_skills(cv, method, catalogue)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    have = {str(r[0]) for r in db.execute(text("SELECT skill_id FROM student_skills WHERE profile_id = :pid"),
                                          {"pid": str(profile_id)}).fetchall()}
    skills = {}
    for s in extracted:
        sid = s["skill_id"] and str(s["skill_id"])
        if not sid or sid not in by_id:
            continue
        if sid in skills and skills[sid]["confidence"] >= s["confidence_score"]:
            continue
        lib = by_id[sid]
        skills[sid] = {
            "skill_id": sid, "skill_name": lib["skill_name"], "category": lib["category"],
            "found_text": s["raw_skill_text"], "context": snippet(cv, s["start_char"], s["end_char"]),
            "confidence": round(float(s["confidence_score"]), 2),
            "in_course": user.course in (lib["courses"] or []),
            "already_added": sid in have,
        }
    ordered = sorted(skills.values(), key=lambda x: (x["category"], x["skill_name"]))
    return ordered, method_used, note


def cv_out(row, skills, method_used, note):
    return {
        "file_name": row.file_name, "content_type": row.content_type, "size_bytes": row.size_bytes,
        "uploaded_at": row.uploaded_at, "method": method_used, "note": note, "skills": skills,
    }


@router.post("", status_code=201)
def upload_cv(file: UploadFile = File(...), method: str = nlp_service.DEFAULT_METHOD,
              current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Store the CV (replacing an older one) and return the library skills it mentions"""
    require_student(current_user)
    data = file.file.read(evidence.MAX_BYTES + 1)
    if len(data) > evidence.MAX_BYTES:
        raise HTTPException(status_code=413, detail="The CV is larger than 5 MB.")
    content_type, cv = read_cv(data)
    if len(cv) < MIN_TEXT:
        raise HTTPException(status_code=400, detail=(
            "No text could be read from this file. If it is a scanned image, upload a PDF or Word "
            "file with selectable text."))
    profile = ensure_profile(db, current_user)
    db.execute(text("""
        INSERT INTO student_cvs (profile_id, file_name, content_type, size_bytes, data, extracted_text)
        VALUES (:pid, :name, :type, :size, :data, :text)
        ON CONFLICT (profile_id) DO UPDATE SET
            file_name = EXCLUDED.file_name, content_type = EXCLUDED.content_type,
            size_bytes = EXCLUDED.size_bytes, data = EXCLUDED.data,
            extracted_text = EXCLUDED.extracted_text, uploaded_at = NOW()
    """), {"pid": str(profile.profile_id), "name": evidence.clean_name(file.filename, content_type),
           "type": content_type, "size": len(data), "data": data, "text": cv})
    db.commit()
    skills, method_used, note = found_skills(db, current_user, profile.profile_id, cv, method)
    return cv_out(stored_cv(db, profile.profile_id), skills, method_used, note)


@router.get("")
def get_cv(method: str = nlp_service.DEFAULT_METHOD,
           current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_student(current_user)
    profile = ensure_profile(db, current_user)
    row = stored_cv(db, profile.profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="No CV uploaded yet.")
    skills, method_used, note = found_skills(db, current_user, profile.profile_id, row.extracted_text, method)
    return cv_out(row, skills, method_used, note)


@router.get("/file")
def download_cv(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_student(current_user)
    row = db.execute(text("""
        SELECT c.file_name, c.content_type, c.data FROM student_cvs c
        JOIN student_profiles sp ON sp.profile_id = c.profile_id WHERE sp.user_id = :uid
    """), {"uid": str(current_user.user_id)}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No CV uploaded yet.")
    return Response(content=bytes(row.data), media_type=row.content_type, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(row.file_name)}",
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


@router.delete("")
def delete_cv(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove the stored CV. Skills already added from it stay on the profile."""
    require_student(current_user)
    deleted = db.execute(text("""
        DELETE FROM student_cvs c USING student_profiles sp
        WHERE sp.profile_id = c.profile_id AND sp.user_id = :uid RETURNING c.profile_id
    """), {"uid": str(current_user.user_id)}).fetchone()
    if not deleted:
        raise HTTPException(status_code=404, detail="No CV uploaded yet.")
    db.commit()
    return {"message": "CV removed. Skills you added from it stay on your profile."}


@router.post("/skills")
def add_cv_skills(req: PickedSkills, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add the skills the student ticked (library skills of their course they do not have yet)"""
    require_student(current_user)
    profile = ensure_profile(db, current_user)
    added, skipped = [], []
    for picked in req.skills:
        skill = db.execute(text("SELECT skill_id, skill_name, courses, is_active FROM skills_library WHERE skill_id = :sid"),
                           {"sid": str(picked.skill_id)}).fetchone()
        if not skill or not skill.is_active:
            skipped.append({"skill_id": str(picked.skill_id), "reason": "not in the skills library"})
            continue
        if current_user.course not in (skill.courses or []):
            skipped.append({"skill_id": str(skill.skill_id), "skill_name": skill.skill_name,
                            "reason": "not in the skill list of your course"})
            continue
        row = db.execute(text("""
            INSERT INTO student_skills (profile_id, skill_id, proficiency_level, evidence_notes)
            SELECT :pid, :sid, :level, 'Found in CV'
            WHERE NOT EXISTS (SELECT 1 FROM student_skills WHERE profile_id = :pid AND skill_id = :sid)
            RETURNING skill_id
        """), {"pid": str(profile.profile_id), "sid": str(skill.skill_id), "level": picked.proficiency_level}).fetchone()
        if row:
            added.append(skill.skill_name)
        else:
            skipped.append({"skill_id": str(skill.skill_id), "skill_name": skill.skill_name, "reason": "already added"})
    refresh_profile_complete(db, current_user.user_id)
    db.commit()
    return {"added": added, "skipped": skipped}
