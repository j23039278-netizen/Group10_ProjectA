"""
SEAGAS — Advisor Router
Handles cohort overview, skill gap reports, student list
Author: Soh Way Miin (Carl)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

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


# ── Cohort Overview ───────────────────────────────────────────
@router.get("/cohort/overview")
def get_cohort_overview(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cohort-level summary for advisor dashboard"""
    require_advisor(current_user)

    # Total students
    total = db.execute(
        text("SELECT COUNT(*) FROM users WHERE role = 'student' AND is_active = TRUE")
    ).scalar()

    # Profiles completed
    profiles_complete = db.execute(
        text("SELECT COUNT(*) FROM student_profiles")
    ).scalar()

    # Average readiness score
    avg_score = db.execute(
        text("""
            SELECT ROUND(AVG(a.readiness_score), 1)
            FROM assessments a
            JOIN (
                SELECT profile_id, MAX(created_at) AS latest
                FROM assessments GROUP BY profile_id
            ) latest ON latest.profile_id = a.profile_id
            AND latest.latest = a.created_at
        """)
    ).scalar()

    # Students at risk (readiness < 40%)
    at_risk = db.execute(
        text("""
            SELECT COUNT(DISTINCT a.profile_id)
            FROM assessments a
            JOIN (
                SELECT profile_id, MAX(created_at) AS latest
                FROM assessments GROUP BY profile_id
            ) latest ON latest.profile_id = a.profile_id
            AND latest.latest = a.created_at
            WHERE a.readiness_score < 40
        """)
    ).scalar()

    return {
        "total_students":     total,
        "profiles_complete":  profiles_complete,
        "avg_readiness_score": float(avg_score) if avg_score else 0,
        "students_at_risk":   at_risk
    }


# ── Skill Gap Report ──────────────────────────────────────────
@router.get("/cohort/skill-gaps")
def get_cohort_skill_gaps(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Top skill gaps across all students — uses v_cohort_skill_gaps view"""
    require_advisor(current_user)

    gaps = db.execute(
        text("""
            SELECT skill_name, category,
                   gap_count, developing_count, strong_count,
                   total_assessments, gap_percentage
            FROM v_cohort_skill_gaps
            WHERE total_assessments > 0
            ORDER BY gap_percentage DESC
            LIMIT 20
        """)
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Full employability profile for one student"""
    require_advisor(current_user)

    # Basic info
    student = db.execute(
        text("""
            SELECT u.full_name, u.email, sp.*
            FROM users u
            JOIN student_profiles sp ON sp.user_id = u.user_id
            WHERE u.user_id = :uid
        """),
        {"uid": user_id}
    ).fetchone()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

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
                SELECT sl.skill_name, sl.category, smr.match_status
                FROM skill_match_results smr
                JOIN skills_library sl ON sl.skill_id = smr.skill_id
                WHERE smr.assessment_id = :aid
                ORDER BY smr.match_status
            """),
            {"aid": str(assessment.assessment_id)}
        ).fetchall()

    return {
        "student":    dict(student._mapping),
        "assessment": dict(assessment._mapping) if assessment else None,
        "skills":     [dict(s._mapping) for s in skills],
        "skill_gaps": [dict(g._mapping) for g in gaps]
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