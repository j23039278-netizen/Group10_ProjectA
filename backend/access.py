"""
SEAGAS — Record-level access checks

A signed-in student may only read their own assessments and job descriptions.
Advisors and admins may read any student's records (advisor dashboard, admin
support). Records the student may not see return 404, the same as a record
that does not exist, so IDs of other students' records reveal nothing.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text

STAFF_ROLES = ("advisor", "admin")


def _not_found(what):
    return HTTPException(status_code=404, detail=f"{what} not found")


def _valid_uuid(value):
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False


def own_profile_id(db, current_user):
    """The signed-in user's student profile_id as a string, or None"""
    row = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()
    return str(row.profile_id) if row else None


def get_assessment_or_404(db, current_user, assessment_id):
    """The assessment row, if the user may read it"""
    if not _valid_uuid(assessment_id):
        raise _not_found("Assessment")
    row = db.execute(
        text("SELECT * FROM assessments WHERE assessment_id = :aid"),
        {"aid": str(assessment_id)}
    ).fetchone()
    if not row:
        raise _not_found("Assessment")
    if current_user.role not in STAFF_ROLES and str(row.profile_id) != own_profile_id(db, current_user):
        raise _not_found("Assessment")
    return row


def get_jd_or_404(db, current_user, jd_id, for_update=False):
    """The job description row, if the user may use it.

    Students: their own JDs. JDs with no owner (the shared JD dataset and admin
    templates) can be read by anyone but only re-analysed by staff.
    """
    if not _valid_uuid(jd_id):
        raise _not_found("Job description")
    row = db.execute(
        text("SELECT * FROM job_descriptions WHERE jd_id = :jid"),
        {"jid": str(jd_id)}
    ).fetchone()
    if not row:
        raise _not_found("Job description")
    if current_user.role in STAFF_ROLES:
        return row
    if row.profile_id is None and not for_update:
        return row
    if row.profile_id is not None and str(row.profile_id) == own_profile_id(db, current_user):
        return row
    raise _not_found("Job description")
