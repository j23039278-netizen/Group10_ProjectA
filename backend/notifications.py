"""
SEAGAS — Notification emails

Every email is written to the email_outbox table. It is also sent when a mail
server is configured in backend/.env:

    SMTP_HOST=smtp.example.com
    SMTP_PORT=587               (default 587)
    SMTP_USER=...               (optional)
    SMTP_PASSWORD=...           (optional)
    SMTP_FROM=seagas@newinti.edu.my
    SMTP_STARTTLS=true          (default true)

Without SMTP_HOST (the normal case for the POC) the email is stored with status
'not_sent' and admins read it on the Student Intake page, so nothing leaves
the computer. Never put SMTP passwords in the code or in git.
"""

import logging
import os
import smtplib
from email.message import EmailMessage

from sqlalchemy import text

log = logging.getLogger("uvicorn.error")

# Shown in emails so students know where to sign in
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST"))


def _send_smtp(to_address, subject, body):
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "seagas@localhost"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587")), timeout=15) as s:
        if os.getenv("SMTP_STARTTLS", "true").lower() != "false":
            s.starttls()
        if os.getenv("SMTP_USER"):
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
        s.send_message(msg)


def send_email(db, to_address, subject, body, related_user_id=None):
    """Store the email in email_outbox and send it if SMTP is configured.

    Returns 'sent', 'not_sent' (no mail server) or 'failed'. Never raises: a mail
    problem must not undo the work that triggered the email. The caller commits.
    """
    status, error = "not_sent", None
    if smtp_configured():
        try:
            _send_smtp(to_address, subject, body)
            status = "sent"
        except Exception as e:   # network, auth, refused address ...
            status, error = "failed", f"{type(e).__name__}: {e}"[:500]
            log.warning("Email to %s failed: %s", to_address, error)
    db.execute(
        text("""
            INSERT INTO email_outbox (to_address, subject, body, status, error, related_user_id)
            VALUES (:to, :subject, :body, :status, :error, :uid)
        """),
        {"to": to_address, "subject": subject, "body": body, "status": status,
         "error": error, "uid": str(related_user_id) if related_user_id else None}
    )
    return status


def welcome_email(full_name, student_number, school_email, temp_password, course_name=None):
    """Subject and body of the account email a new student receives"""
    subject = "Your SEAGAS student account"
    course_line = f"  Course:              {course_name}\n" if course_name else ""
    body = f"""Dear {full_name},

Your SEAGAS account has been created.

  Student ID:          {student_number}
{course_line}  School email:        {school_email}
  Temporary password:  {temp_password}

Sign in at {FRONTEND_URL}/login with your school email, student ID and the
temporary password. You will be asked to choose your own password straight away;
the temporary password stops working after that.

If you did not expect this email, please contact your academic advisor.

SEAGAS - Student Employability Assessment and Skill Gap Analysis System
"""
    return subject, body
