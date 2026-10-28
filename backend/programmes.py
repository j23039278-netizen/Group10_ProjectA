"""
SEAGAS — Programmes (majors) of each course

The list is the programmes table (database/schema.sql). A student's programme is
set with the course when the account is created from a new-student list
(routers/intake.py); students cannot change it, admins can (routers/admin.py).
"""

from fastapi import HTTPException
from sqlalchemy import text


def list_programmes(db, course=None):
    """Active programmes, of one course or all, in display order"""
    rows = db.execute(text("""
        SELECT programme_name, course FROM programmes
        WHERE is_active AND (CAST(:course AS VARCHAR) IS NULL OR course = CAST(:course AS VARCHAR))
        ORDER BY course, sort_order, programme_name
    """), {"course": course}).fetchall()
    return [dict(r._mapping) for r in rows]


def by_course(db):
    """{course: {lower-case name: name}} for matching uploaded text"""
    out = {}
    for p in list_programmes(db):
        out.setdefault(p["course"], {})[" ".join(p["programme_name"].lower().split())] = p["programme_name"]
    return out


def check_programme(db, name, course):
    """The programme's exact name, or 400 when it is not a programme of the course"""
    match = by_course(db).get(course, {}).get(" ".join((name or "").lower().split()))
    if not match:
        raise HTTPException(status_code=400, detail="Choose one of the programmes of the student's course.")
    return match


def set_programme(db, user_id, name):
    """Store the programme on the student's profile (created if missing)"""
    db.execute(text("""
        INSERT INTO student_profiles (user_id, programme) VALUES (CAST(:uid AS uuid), :p)
        ON CONFLICT (user_id) DO UPDATE SET programme = EXCLUDED.programme, updated_at = NOW()
    """), {"uid": str(user_id), "p": name})
