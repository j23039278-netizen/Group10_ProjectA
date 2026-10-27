"""
SEAGAS — Advisor Router
Handles cohort overview, skill gap reports, student list
Author: Soh Way Miin (Carl)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

import audit
import evidence
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


# ── Course filter (CS | BUSINESS | ICT; none = every student) ─
def course_param(course):
    if course is None or course == "":
        return None
    c = course.upper()
    if c not in ("CS", "BUSINESS", "ICT"):
        raise HTTPException(status_code=400, detail="course must be CS, BUSINESS or ICT")
    return c


# Each student's latest assessment, limited to one course when :course is set
LATEST_ASSESSMENTS = """
    SELECT DISTINCT ON (a.profile_id) a.assessment_id, a.profile_id, a.readiness_score
    FROM assessments a
    JOIN student_profiles sp ON sp.profile_id = a.profile_id
    JOIN users u             ON u.user_id     = sp.user_id
    WHERE u.role = 'student' AND u.is_active
      AND (CAST(:course AS VARCHAR) IS NULL OR u.course = CAST(:course AS VARCHAR))
    ORDER BY a.profile_id, a.created_at DESC
"""


# ── Cohort Overview ───────────────────────────────────────────
@router.get("/cohort/overview")
def get_cohort_overview(
    course: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cohort-level summary for the advisor dashboard (one course, or everyone)"""
    require_advisor(current_user)
    params = {"course": course_param(course)}

    counts = db.execute(
        text("""
            SELECT COUNT(*)                                   AS total,
                   COUNT(*) FILTER (WHERE sp.is_complete)     AS complete
            FROM users u
            LEFT JOIN student_profiles sp ON sp.user_id = u.user_id
            WHERE u.role = 'student' AND u.is_active = TRUE
              AND (CAST(:course AS VARCHAR) IS NULL OR u.course = CAST(:course AS VARCHAR))
        """),
        params
    ).fetchone()

    scores = db.execute(
        text(f"""
            SELECT ROUND(AVG(readiness_score), 1)               AS avg_score,
                   COUNT(*) FILTER (WHERE readiness_score < 40) AS at_risk,
                   COUNT(*)                                     AS assessed
            FROM ({LATEST_ASSESSMENTS}) latest
        """),
        params
    ).fetchone()

    return {
        "course":              params["course"],
        "total_students":      counts.total,
        "profiles_complete":   counts.complete,
        "students_assessed":   scores.assessed,
        "avg_readiness_score": float(scores.avg_score) if scores.avg_score else 0,
        "students_at_risk":    scores.at_risk
    }


# ── Skill Gap Report ──────────────────────────────────────────
@router.get("/cohort/skill-gaps")
def get_cohort_skill_gaps(
    course: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Top skill gaps across the latest assessments of one course, or of every student"""
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
        {"course": course_param(course)}
    ).fetchall()

    return [dict(g._mapping) for g in gaps]


# ── Student List ──────────────────────────────────────────────
@router.get("/students")
def get_all_students(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all students with their latest readiness score"""
    require_advisor(current_user)

    students = db.execute(
        text("""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.student_number,
                u.course,
                sp.programme,
                sp.target_role,
                sp.gpa,
                a.readiness_score   AS latest_score,
                a.created_at        AS last_assessed,
                jr.role_name        AS assessed_role
            FROM users u
            LEFT JOIN student_profiles sp ON sp.user_id = u.user_id
            LEFT JOIN LATERAL (
                SELECT * FROM assessments
                WHERE profile_id = sp.profile_id
                ORDER BY created_at DESC
                LIMIT 1
            ) a ON TRUE
            LEFT JOIN job_roles jr ON jr.role_id = a.role_id
            WHERE u.role = 'student' AND u.is_active = TRUE
            ORDER BY u.full_name
        """)
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
        text("""
            SELECT u.full_name, u.email, u.student_number, u.course, sp.*
            FROM users u
            JOIN student_profiles sp ON sp.user_id = u.user_id
            WHERE u.user_id = CAST(:uid AS uuid) AND u.role = 'student'
        """),
        {"uid": str(user_id)}
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

    return {
        "student":        dict(student._mapping),
        "assessment":     latest,
        "skills":         [dict(s._mapping) for s in skills],
        "skill_gaps":     [dict(g._mapping) for g in gaps],
        "history":        [dict(h._mapping) for h in history],
        "projects":       evidence.attach_files(db, [dict(p._mapping) for p in projects], "project_id"),
        "certifications": evidence.attach_files(db, [dict(c._mapping) for c in certifications], "cert_id"),
        "progress":       evidence.attach_files(db, [dict(p._mapping) for p in progress], "progress_id"),
    }


# ── Development Tracking ──────────────────────────────────────
@router.get("/cohort/progress")
def get_cohort_progress(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Overall recommendation completion across cohort"""
    require_advisor(current_user)

    progress = db.execute(
        text("""
            SELECT * FROM v_student_progress
            ORDER BY completed_tasks DESC
        """)
    ).fetchall()

    return [dict(p._mapping) for p in progress]


# ── Reports ───────────────────────────────────────────────────
@router.get("/reports/skill-gap-summary")
def get_skill_gap_report(
    role_id: str = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Skill gap breakdown by job role — for export"""
    require_advisor(current_user)

    if role_id:
        gaps = db.execute(
            text("""
                SELECT sl.skill_name, sl.category,
                       COUNT(*) FILTER (WHERE smr.match_status = 'gap') AS gap_count,
                       COUNT(*) FILTER (WHERE smr.match_status = 'developing') AS developing_count,
                       COUNT(*) FILTER (WHERE smr.match_status = 'strong') AS strong_count,
                       COUNT(*) AS total
                FROM skill_match_results smr
                JOIN skills_library sl ON sl.skill_id = smr.skill_id
                JOIN assessments a ON a.assessment_id = smr.assessment_id
                WHERE a.role_id = :rid
                GROUP BY sl.skill_name, sl.category
                ORDER BY gap_count DESC
            """),
            {"rid": role_id}
        ).fetchall()
    else:
        gaps = db.execute(
            text("""
                SELECT skill_name, category,
                       gap_count, developing_count, strong_count,
                       total_assessments AS total, gap_percentage
                FROM v_cohort_skill_gaps
                ORDER BY gap_percentage DESC
            """)
        ).fetchall()

    return [dict(g._mapping) for g in gaps]