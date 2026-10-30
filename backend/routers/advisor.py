"""
SEAGAS — Advisor Router
Cohort overview, skill gaps, student list and detail, learning progress, advisor
notes (human review of the AI results) and student CVs.
Author: Soh Way Miin (Carl)

Every query is limited to the courses of the signed-in advisor (advisor_scope.py).
"""

from typing import Literal, Optional
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

import audit
import evidence
from advisor_scope import ALL_COURSES, courses_of
from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Permission Check ──────────────────────────────────────────
def require_advisor(current_user):
    if current_user.role not in ("advisor", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Advisor or Admin role required."
        )


# ── Course filter ─────────────────────────────────────────────
# An advisor sees only the students of their courses (Dean / Head of Programme,
# see advisor_scope.py). course narrows that to one of them; none = all of them.
COURSE_FILTER = "u.course = ANY(CAST(:courses AS VARCHAR[]))"


def course_param(course, current_user):
    """The courses to include, as a list"""
    allowed = courses_of(current_user)
    if course is None or course == "":
        return allowed
    c = course.upper()
    if c not in ALL_COURSES:
        raise HTTPException(status_code=400, detail="course must be CS, BUSINESS or ICT")
    if c not in allowed:
        raise HTTPException(status_code=403, detail="You can only see students of your own courses.")
    return [c]


# Each student's latest assessment, limited to the courses in :courses and, when
# :role_id is set, to assessments against that job role
LATEST_ASSESSMENTS = f"""
    SELECT DISTINCT ON (a.profile_id) a.assessment_id, a.profile_id, a.readiness_score, a.role_id
    FROM assessments a
    JOIN student_profiles sp ON sp.profile_id = a.profile_id
    JOIN users u             ON u.user_id     = sp.user_id
    WHERE u.role = 'student' AND u.is_active
      AND {COURSE_FILTER}
      AND (CAST(:role_id AS uuid) IS NULL OR a.role_id = CAST(:role_id AS uuid))
    ORDER BY a.profile_id, a.created_at DESC
"""

# Readiness bands, the same as the dashboard's status labels
ON_TRACK, NEEDS_SUPPORT = 70, 40


def role_param(role_id):
    if not role_id:
        return None
    try:
        return str(UUID(role_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="role_id is not valid")


# ── Cohort Overview ───────────────────────────────────────────
@router.get("/cohort/overview")
def get_cohort_overview(
    course: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cohort-level summary for the advisor dashboard (one course, or all of the advisor's)"""
    require_advisor(current_user)
    params = {"courses": course_param(course, current_user), "role_id": None}

    counts = db.execute(
        text(f"""
            SELECT COUNT(*)                                   AS total,
                   COUNT(*) FILTER (WHERE sp.is_complete)     AS complete
            FROM users u
            LEFT JOIN student_profiles sp ON sp.user_id = u.user_id
            WHERE u.role = 'student' AND u.is_active = TRUE
              AND {COURSE_FILTER}
        """),
        params
    ).fetchone()

    scores = db.execute(
        text(f"""
            SELECT ROUND(AVG(readiness_score), 1)                            AS avg_score,
                   COUNT(*) FILTER (WHERE readiness_score < {NEEDS_SUPPORT})  AS needs_support,
                   COUNT(*) FILTER (WHERE readiness_score >= {NEEDS_SUPPORT}
                                      AND readiness_score < {ON_TRACK})      AS developing,
                   COUNT(*) FILTER (WHERE readiness_score >= {ON_TRACK})      AS on_track,
                   COUNT(*)                                                  AS assessed
            FROM ({LATEST_ASSESSMENTS}) latest
        """),
        params
    ).fetchone()

    # Readiness distribution: ten bands of 10 points (90-100 includes 100)
    bins = {r.band: r.n for r in db.execute(text(f"""
        SELECT LEAST(FLOOR(readiness_score / 10)::int, 9) AS band, COUNT(*) AS n
        FROM ({LATEST_ASSESSMENTS}) latest GROUP BY 1
    """), params).fetchall()}
    distribution = [{"band": f"{b * 10}-{b * 10 + (10 if b == 9 else 9)}", "from": b * 10, "students": bins.get(b, 0)}
                    for b in range(10)]

    # Students per target role, with the average of their latest readiness score
    roles = db.execute(text(f"""
        SELECT COALESCE(NULLIF(TRIM(sp.target_role), ''), 'Not set') AS target_role,
               COUNT(*)                                         AS students,
               COUNT(latest.assessment_id)                      AS assessed,
               ROUND(AVG(latest.readiness_score), 1)            AS avg_score
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.user_id
        LEFT JOIN ({LATEST_ASSESSMENTS}) latest ON latest.profile_id = sp.profile_id
        WHERE u.role = 'student' AND u.is_active AND {COURSE_FILTER}
        GROUP BY 1 ORDER BY students DESC, target_role
    """), params).fetchall()

    activity = db.execute(text(f"""
        SELECT COUNT(*) FILTER (WHERE srp.status = 'completed')   AS completed,
               COUNT(*) FILTER (WHERE srp.status = 'in_progress') AS in_progress,
               COUNT(DISTINCT sp.profile_id) FILTER (WHERE srp.status = 'completed') AS students_completed
        FROM student_resource_progress srp
        JOIN student_profiles sp ON sp.profile_id = srp.profile_id
        JOIN users u ON u.user_id = sp.user_id
        WHERE u.role = 'student' AND u.is_active AND {COURSE_FILTER}
    """), params).fetchone()

    return {
        "course":              course.upper() if course else None,
        "courses":             params["courses"],
        "total_students":      counts.total,
        "profiles_complete":   counts.complete,
        "students_assessed":   scores.assessed,
        "avg_readiness_score": float(scores.avg_score) if scores.avg_score else 0,
        "students_at_risk":    scores.needs_support,     # below 40: "Needs support" on the dashboard
        "status_counts": {
            "on_track": scores.on_track, "developing": scores.developing,
            "needs_support": scores.needs_support, "not_assessed": counts.total - scores.assessed,
        },
        "distribution":        distribution,
        "target_roles":        [{**dict(r._mapping), "avg_score": float(r.avg_score) if r.avg_score is not None else None}
                                for r in roles],
        "activities": {"completed": activity.completed, "in_progress": activity.in_progress,
                       "students_completed": activity.students_completed},
    }


# ── Skill Gap Report ──────────────────────────────────────────
@router.get("/cohort/skill-gaps")
def get_cohort_skill_gaps(
    course: Optional[str] = None,
    role_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Top skill gaps across the latest assessments of one course (or all of the advisor's),
    optionally only assessments against one job role"""
    require_advisor(current_user)

    gaps = db.execute(
        text(f"""
            SELECT sl.skill_name, sl.category,
                   COUNT(*) FILTER (WHERE smr.match_status = 'gap')        AS gap_count,
                   COUNT(*) FILTER (WHERE smr.match_status = 'developing') AS developing_count,
                   COUNT(*) FILTER (WHERE smr.match_status = 'strong')     AS strong_count,
                   COUNT(*)                                                 AS total_assessments,
                   ROUND(COUNT(*) FILTER (WHERE smr.match_status = 'gap') * 100.0
                         / NULLIF(COUNT(*), 0), 1)                          AS gap_percentage
            FROM skill_match_results smr
            JOIN ({LATEST_ASSESSMENTS}) latest ON latest.assessment_id = smr.assessment_id
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            GROUP BY sl.skill_id, sl.skill_name, sl.category
            ORDER BY gap_percentage DESC, gap_count DESC
            LIMIT 20
        """),
        {"courses": course_param(course, current_user), "role_id": role_param(role_id)}
    ).fetchall()

    return [dict(g._mapping) for g in gaps]


# ── Student List ──────────────────────────────────────────────
@router.get("/students")
def get_all_students(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """The students of the advisor's courses with their latest readiness score and progress"""
    require_advisor(current_user)

    students = db.execute(
        text(f"""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.student_number,
                u.course,
                sp.programme,
                sp.target_role,
                sp.year_of_study,
                sp.gpa,
                sp.cgpa,
                COALESCE(sp.is_complete, FALSE) AS profile_complete,
                a.readiness_score   AS latest_score,
                a.created_at        AS last_assessed,
                jr.role_name        AS assessed_role,
                (SELECT COUNT(*) FROM student_resource_progress srp
                  WHERE srp.profile_id = sp.profile_id AND srp.status = 'completed') AS activities_completed,
                (SELECT COUNT(*) FROM advisor_notes n WHERE n.student_id = u.user_id) AS note_count
            FROM users u
            LEFT JOIN student_profiles sp ON sp.user_id = u.user_id
            LEFT JOIN LATERAL (
                SELECT * FROM assessments
                WHERE profile_id = sp.profile_id
                ORDER BY created_at DESC
                LIMIT 1
            ) a ON TRUE
            LEFT JOIN job_roles jr ON jr.role_id = a.role_id
            WHERE u.role = 'student' AND u.is_active = TRUE AND {COURSE_FILTER}
            ORDER BY u.full_name
        """),
        {"courses": courses_of(current_user)}
    ).fetchall()

    return [dict(s._mapping) for s in students]


@router.get("/students/{user_id}")
def get_student_detail(
    user_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Full employability profile for one student"""
    require_advisor(current_user)

    # A malformed id is just "not found", the same as the other ID routes
    try:
        user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Student not found")

    # Basic info
    student = db.execute(
        text(f"""
            SELECT u.full_name, u.email, u.student_number, u.course, sp.*
            FROM users u
            JOIN student_profiles sp ON sp.user_id = u.user_id
            WHERE u.user_id = CAST(:uid AS uuid) AND u.role = 'student' AND {COURSE_FILTER}
        """),
        {"uid": str(user_id), "courses": courses_of(current_user)}
    ).fetchone()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    audit.record(db, "advisor.view_student", user=current_user, request=request,
                 target_type="user", target_id=user_id, commit=True)

    # Latest assessment
    assessment = db.execute(
        text("""
            SELECT * FROM assessments
            WHERE profile_id = :pid
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"pid": str(student.profile_id)}
    ).fetchone()

    # Skills
    skills = db.execute(
        text("""
            SELECT sl.skill_name, sl.category, ss.proficiency_level
            FROM student_skills ss
            JOIN skills_library sl ON sl.skill_id = ss.skill_id
            WHERE ss.profile_id = :pid
            ORDER BY sl.category, sl.skill_name
        """),
        {"pid": str(student.profile_id)}
    ).fetchall()

    # Skill gaps from latest assessment
    gaps = []
    if assessment:
        gaps = db.execute(
            text("""
                SELECT sl.skill_name, sl.category, smr.match_status, smr.reason
                FROM skill_match_results smr
                JOIN skills_library sl ON sl.skill_id = smr.skill_id
                WHERE smr.assessment_id = :aid
                ORDER BY smr.match_status
            """),
            {"aid": str(assessment.assessment_id)}
        ).fetchall()

    pid = {"pid": str(student.profile_id)}

    # Every assessment, oldest first, for the readiness-over-time chart
    history = db.execute(
        text("""
            SELECT a.assessment_id, a.readiness_score, a.matching_method,
                   a.created_at, jr.role_name
            FROM assessments a
            LEFT JOIN job_roles jr ON jr.role_id = a.role_id
            WHERE a.profile_id = :pid
            ORDER BY a.created_at
        """),
        pid
    ).fetchall()

    role_name = None
    if assessment and assessment.role_id:
        role_name = db.execute(text("SELECT role_name FROM job_roles WHERE role_id = :rid"),
                               {"rid": str(assessment.role_id)}).scalar()

    projects = db.execute(
        text("""
            SELECT project_id, project_title, description, technologies, project_type, year_completed
            FROM student_projects WHERE profile_id = :pid
            ORDER BY year_completed DESC NULLS LAST
        """),
        pid
    ).fetchall()

    certifications = db.execute(
        text("""
            SELECT cert_id, cert_name, issuer, issue_date, expiry_date
            FROM student_certifications WHERE profile_id = :pid
            ORDER BY issue_date DESC NULLS LAST
        """),
        pid
    ).fetchall()

    # Recommended activities the student started or finished
    progress = db.execute(
        text("""
            SELECT srp.progress_id, rl.resource_title, rl.resource_type, sl.skill_name,
                   srp.status, srp.started_at, srp.completed_at
            FROM student_resource_progress srp
            JOIN recommendations_library rl ON rl.resource_id = srp.resource_id
            LEFT JOIN skills_library sl     ON sl.skill_id    = srp.skill_id
            WHERE srp.profile_id = :pid
            ORDER BY srp.updated_at DESC
        """),
        pid
    ).fetchall()

    latest = None
    if assessment:
        latest = dict(assessment._mapping)
        latest["role_name"] = role_name

    cv = db.execute(text("SELECT file_name, size_bytes, uploaded_at FROM student_cvs WHERE profile_id = :pid"),
                    pid).fetchone()

    return {
        "student":        dict(student._mapping),
        "assessment":     latest,
        "skills":         [dict(s._mapping) for s in skills],
        "skill_gaps":     [dict(g._mapping) for g in gaps],
        "history":        [dict(h._mapping) for h in history],
        "projects":       evidence.attach_files(db, [dict(p._mapping) for p in projects], "project_id"),
        "certifications": evidence.attach_files(db, [dict(c._mapping) for c in certifications], "cert_id"),
        "progress":       evidence.attach_files(db, [dict(p._mapping) for p in progress], "progress_id"),
        "cv":             dict(cv._mapping) if cv else None,
        "notes":          list_notes(db, user_id, current_user),
    }


# ── Development Tracking ──────────────────────────────────────
@router.get("/cohort/progress")
def get_cohort_progress(
    course: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recommended-activity progress of the advisor's students: totals, the resources
    completed most often, and one row per student who saved or started an activity"""
    require_advisor(current_user)
    params = {"courses": course_param(course, current_user)}
    scope = f"""
        FROM student_resource_progress srp
        JOIN student_profiles sp ON sp.profile_id = srp.profile_id
        JOIN users u ON u.user_id = sp.user_id
        WHERE u.role = 'student' AND u.is_active AND {COURSE_FILTER}
    """
    totals = db.execute(text(f"""
        SELECT COUNT(*) FILTER (WHERE srp.status = 'completed')   AS completed,
               COUNT(*) FILTER (WHERE srp.status = 'in_progress') AS in_progress,
               COUNT(*) FILTER (WHERE srp.status = 'saved')       AS saved,
               COUNT(DISTINCT sp.profile_id)                      AS students_active,
               COUNT(DISTINCT sp.profile_id) FILTER (WHERE srp.status = 'completed') AS students_completed
        {scope}
    """), params).fetchone()
    top = db.execute(text(f"""
        SELECT rl.resource_title, rl.resource_type, rl.provider, sl.skill_name,
               COUNT(*) FILTER (WHERE srp.status = 'completed')   AS completed,
               COUNT(*) FILTER (WHERE srp.status = 'in_progress') AS in_progress
        FROM student_resource_progress srp
        JOIN recommendations_library rl ON rl.resource_id = srp.resource_id
        LEFT JOIN skills_library sl     ON sl.skill_id    = rl.skill_id
        JOIN student_profiles sp        ON sp.profile_id  = srp.profile_id
        JOIN users u                    ON u.user_id      = sp.user_id
        WHERE u.role = 'student' AND u.is_active AND {COURSE_FILTER}
        GROUP BY rl.resource_id, rl.resource_title, rl.resource_type, rl.provider, sl.skill_name
        ORDER BY completed DESC, in_progress DESC, rl.resource_title
        LIMIT 10
    """), params).fetchall()
    students = db.execute(text(f"""
        SELECT u.user_id, u.full_name, u.student_number, u.course, sp.target_role,
               COUNT(*) FILTER (WHERE srp.status = 'completed')   AS completed,
               COUNT(*) FILTER (WHERE srp.status = 'in_progress') AS in_progress,
               COUNT(*) FILTER (WHERE srp.status = 'saved')       AS saved,
               MAX(srp.completed_at)                              AS last_completed
        {scope}
        GROUP BY u.user_id, u.full_name, u.student_number, u.course, sp.target_role
        ORDER BY completed DESC, in_progress DESC, u.full_name
    """), params).fetchall()
    return {"totals": dict(totals._mapping), "top_resources": [dict(t._mapping) for t in top],
            "students": [dict(r._mapping) for r in students]}


# ── Advisor notes (human review of the AI results) ────────────
# Notes are seen by the advisors and admins who can see the student, never by the
# student. An "ai_review" note records whether the advisor agrees with the AI result
# of an assessment (human oversight of the automated scores).
class NoteIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    note_type: Literal["general", "ai_review"] = "general"
    ai_verdict: Optional[Literal["agree", "disagree"]] = None
    assessment_id: Optional[UUID] = None


class NoteUpdate(BaseModel):
    body: Optional[str] = Field(None, min_length=1, max_length=2000)
    ai_verdict: Optional[Literal["agree", "disagree"]] = None


NOTE_COLUMNS = """n.note_id, n.student_id, n.author_id, au.full_name AS author_name, n.body, n.note_type,
                  n.ai_verdict, n.assessment_id, jr.role_name AS assessment_role, a.readiness_score AS assessment_score,
                  a.created_at AS assessment_date, n.created_at, n.updated_at"""


def visible_student(db, user_id, current_user):
    """The student's row if this advisor may see them, else 404 (same as a missing student)"""
    try:
        uid = str(UUID(str(user_id)))
    except ValueError:
        raise HTTPException(status_code=404, detail="Student not found")
    row = db.execute(text(f"""
        SELECT u.user_id, sp.profile_id FROM users u LEFT JOIN student_profiles sp ON sp.user_id = u.user_id
        WHERE u.user_id = CAST(:uid AS uuid) AND u.role = 'student' AND {COURSE_FILTER}
    """), {"uid": uid, "courses": courses_of(current_user)}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return row


def list_notes(db, student_id, current_user):
    rows = db.execute(text(f"""
        SELECT {NOTE_COLUMNS}
        FROM advisor_notes n
        LEFT JOIN users au       ON au.user_id = n.author_id
        LEFT JOIN assessments a  ON a.assessment_id = n.assessment_id
        LEFT JOIN job_roles jr   ON jr.role_id = a.role_id
        WHERE n.student_id = CAST(:sid AS uuid)
        ORDER BY n.created_at DESC
    """), {"sid": str(student_id)}).fetchall()
    me = str(current_user.user_id)
    return [{**dict(r._mapping), "can_edit": str(r.author_id) == me} for r in rows]


def note_row(db, note_id):
    try:
        nid = str(UUID(str(note_id)))
    except ValueError:
        raise HTTPException(status_code=404, detail="Note not found")
    row = db.execute(text("SELECT note_id, student_id, author_id, note_type FROM advisor_notes WHERE note_id = :n"),
                     {"n": nid}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    return row


@router.get("/students/{user_id}/notes")
def get_notes(user_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_advisor(current_user)
    visible_student(db, user_id, current_user)
    return list_notes(db, user_id, current_user)


@router.post("/students/{user_id}/notes", status_code=201)
def add_note(user_id: str, req: NoteIn, request: Request,
             current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_advisor(current_user)
    student = visible_student(db, user_id, current_user)
    if req.note_type == "ai_review":
        if not req.ai_verdict or not req.assessment_id:
            raise HTTPException(status_code=400, detail="A review of the AI result needs the assessment and agree / disagree.")
        owns = db.execute(text("SELECT 1 FROM assessments WHERE assessment_id = :a AND profile_id = :p"),
                          {"a": str(req.assessment_id), "p": str(student.profile_id)}).fetchone()
        if not owns:
            raise HTTPException(status_code=400, detail="That assessment does not belong to this student.")
    elif req.ai_verdict or req.assessment_id:
        raise HTTPException(status_code=400, detail="Only a review of the AI result has a verdict and an assessment.")
    note_id = db.execute(text("""
        INSERT INTO advisor_notes (student_id, author_id, body, note_type, ai_verdict, assessment_id)
        VALUES (:sid, :aid, :body, :type, :verdict, :assessment) RETURNING note_id
    """), {"sid": str(student.user_id), "aid": str(current_user.user_id), "body": req.body.strip(),
           "type": req.note_type, "verdict": req.ai_verdict,
           "assessment": str(req.assessment_id) if req.assessment_id else None}).scalar()
    audit.record(db, "advisor.note_create", user=current_user, request=request, target_type="user",
                 target_id=student.user_id, details={"note_type": req.note_type, "ai_verdict": req.ai_verdict})
    db.commit()
    return next(n for n in list_notes(db, student.user_id, current_user) if str(n["note_id"]) == str(note_id))


@router.patch("/notes/{note_id}")
def update_note(note_id: str, req: NoteUpdate, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Only the author changes a note"""
    require_advisor(current_user)
    note = note_row(db, note_id)
    visible_student(db, note.student_id, current_user)
    if str(note.author_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Only the author can change this note.")
    if req.body is None and req.ai_verdict is None:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    if req.ai_verdict and note.note_type != "ai_review":
        raise HTTPException(status_code=400, detail="Only a review of the AI result has a verdict.")
    db.execute(text("""
        UPDATE advisor_notes SET body = COALESCE(:body, body), ai_verdict = COALESCE(:verdict, ai_verdict),
                                 updated_at = NOW()
        WHERE note_id = :n
    """), {"body": req.body.strip() if req.body else None, "verdict": req.ai_verdict, "n": str(note.note_id)})
    audit.record(db, "advisor.note_update", user=current_user, request=request, target_type="user",
                 target_id=note.student_id)
    db.commit()
    return next(n for n in list_notes(db, note.student_id, current_user) if str(n["note_id"]) == str(note.note_id))


@router.delete("/notes/{note_id}")
def delete_note(note_id: str, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Only the author deletes a note"""
    require_advisor(current_user)
    note = note_row(db, note_id)
    visible_student(db, note.student_id, current_user)
    if str(note.author_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Only the author can delete this note.")
    db.execute(text("DELETE FROM advisor_notes WHERE note_id = :n"), {"n": str(note.note_id)})
    audit.record(db, "advisor.note_delete", user=current_user, request=request, target_type="user",
                 target_id=note.student_id)
    db.commit()
    return {"message": "Note deleted"}


# ── Student CV ────────────────────────────────────────────────
@router.get("/students/{user_id}/cv")
def download_student_cv(user_id: str, request: Request,
                        current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """The CV the student uploaded (audited, like evidence files)"""
    require_advisor(current_user)
    student = visible_student(db, user_id, current_user)
    row = db.execute(text("SELECT file_name, content_type, data FROM student_cvs WHERE profile_id = :p"),
                     {"p": str(student.profile_id) if student.profile_id else None}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="This student has not uploaded a CV.")
    audit.record(db, "advisor.view_cv", user=current_user, request=request, target_type="user",
                 target_id=student.user_id, commit=True)
    return Response(content=bytes(row.data), media_type=row.content_type, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(row.file_name)}",
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


# ── Reports ───────────────────────────────────────────────────
@router.get("/reports/skill-gap-summary")
def get_skill_gap_report(
    role_id: str = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Skill gap breakdown by job role — for export"""
    require_advisor(current_user)

    if not role_id:
        return get_cohort_skill_gaps(None, None, current_user, db)
    gaps = db.execute(
        text(f"""
            SELECT sl.skill_name, sl.category,
                   COUNT(*) FILTER (WHERE smr.match_status = 'gap') AS gap_count,
                   COUNT(*) FILTER (WHERE smr.match_status = 'developing') AS developing_count,
                   COUNT(*) FILTER (WHERE smr.match_status = 'strong') AS strong_count,
                   COUNT(*) AS total
            FROM skill_match_results smr
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            JOIN assessments a ON a.assessment_id = smr.assessment_id
            JOIN student_profiles sp ON sp.profile_id = a.profile_id
            JOIN users u ON u.user_id = sp.user_id
            WHERE a.role_id = :rid AND {COURSE_FILTER}
            GROUP BY sl.skill_name, sl.category
            ORDER BY gap_count DESC
        """),
        {"rid": role_id, "courses": courses_of(current_user)}
    ).fetchall()

    return [dict(g._mapping) for g in gaps]