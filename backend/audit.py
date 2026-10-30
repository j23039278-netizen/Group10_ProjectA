"""
SEAGAS — Audit log (NFR: security and accountability)

Records who did what and when: sign-ins (including failed ones), registrations,
assessments, JD analyses, advisors opening a student's record, and every admin
change to an account. Admins read the log from the Admin portal.

Never put passwords, tokens or other secrets into `details`.
"""

import json
import logging

from sqlalchemy import text

log = logging.getLogger("uvicorn.error")

ACTIONS = (
    "auth.login", "auth.login_failed", "auth.register", "auth.password_change",
    "intake.upload", "intake.accounts_create", "intake.reject",
    "assessment.run", "jd.analyse",
    "advisor.view_student", "advisor.view_file", "advisor.view_cv",
    "advisor.note_create", "advisor.note_update", "advisor.note_delete",
    "admin.user_create", "admin.user_update", "admin.password_reset",
    "admin.skill_create", "admin.skill_update", "admin.role_create", "admin.role_update",
    "admin.resource_create", "admin.resource_update",
)


def client_ip(request):
    if request is None or request.client is None:
        return None
    return request.client.host


def record(db, action, *, user=None, email=None, target_type=None, target_id=None,
           details=None, request=None, commit=False):
    """Add one audit row. A failure here is logged, never raised to the user.

    user: the signed-in users row (None for anonymous events such as a failed login).
    email: the email involved when there is no user row (e.g. a failed login attempt).
    commit=True for read-only requests (login, advisor view) that commit nothing else.
    """
    assert action in ACTIONS, action
    try:
        # A savepoint, so a failed audit write does not roll back the request's own work
        with db.begin_nested():
            db.execute(
                text("""
                    INSERT INTO audit_log
                        (user_id, actor_email, actor_role, action, target_type, target_id,
                         details, ip_address)
                    VALUES (:uid, :email, :role, :action, :ttype, :tid, CAST(:details AS JSONB), :ip)
                """),
                {"uid": str(user.user_id) if user is not None else None,
                 "email": user.email if user is not None else email,
                 "role": user.role if user is not None else None,
                 "action": action, "ttype": target_type,
                 "tid": str(target_id) if target_id is not None else None,
                 "details": json.dumps(details, default=str) if details else None,
                 "ip": client_ip(request)}
            )
        if commit:
            db.commit()
    except Exception as e:  # auditing must not break the request itself
        log.warning("audit log write failed for %s: %s", action, e)
