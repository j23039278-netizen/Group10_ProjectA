"""
SEAGAS — Notification emails

Every email is written to the email_outbox table. It is also sent when a mail
server is configured in backend/.env:

    SMTP_HOST=smtp.example.com
    SMTP_PORT=587               (default 587; 465 for SSL)
    SMTP_SECURITY=starttls      (starttls | ssl | none; default starttls)
    SMTP_USER=...               (optional)
    SMTP_PASSWORD=...           (optional; for Gmail an App Password, not the account password)
    SMTP_FROM=seagas@newinti.edu.my

Example for a Gmail account with 2-step verification and an App Password:
    SMTP_HOST=smtp.gmail.com  SMTP_PORT=587  SMTP_SECURITY=starttls
    SMTP_USER=you@gmail.com   SMTP_PASSWORD=<16-letter app password>  SMTP_FROM=you@gmail.com
(SMTP_STARTTLS=false from older setups still means "none".)

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


def _security():
    security = (os.getenv("SMTP_SECURITY") or "").strip().lower()
    if security in ("starttls", "ssl", "none"):
        return security
    return "none" if os.getenv("SMTP_STARTTLS", "true").lower() == "false" else "starttls"


def _from_address():
    return os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "seagas@localhost"


def mail_status():
    """What the admin page shows about the mail server (never the password)"""
    security = _security()
    return {"configured": smtp_configured(), "host": os.getenv("SMTP_HOST") or None,
            "port": int(os.getenv("SMTP_PORT") or (465 if security == "ssl" else 587)),
            "security": security, "from_address": _from_address() if smtp_configured() else None,
            "login": bool(os.getenv("SMTP_USER"))}


def _send_smtp(to_address, subject, body):
    msg = EmailMessage()
    msg["From"] = _from_address()
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)
    status = mail_status()
    smtp_class = smtplib.SMTP_SSL if status["security"] == "ssl" else smtplib.SMTP
    with smtp_class(status["host"], status["port"], timeout=15) as s:
        if status["security"] == "starttls":
            s.starttls()
        if os.getenv("SMTP_USER"):
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
        s.send_message(msg)


def _try_send(to_address, subject, body):
    """('sent' | 'not_sent' | 'failed', error or None); never raises"""
    if not smtp_configured():
        return "not_sent", None
    try:
        _send_smtp(to_address, subject, body)
        return "sent", None
    except Exception as e:   # network, auth, refused address ...
        error = f"{type(e).__name__}: {e}"[:500]
        log.warning("Email to %s failed: %s", to_address, error)
        return "failed", error


def send_email(db, to_address, subject, body, related_user_id=None):
    """Store the email in email_outbox and send it if SMTP is configured.

    Returns 'sent', 'not_sent' (no mail server) or 'failed'. Never raises: a mail
    problem must not undo the work that triggered the email. The caller commits.
    """
    status, error = _try_send(to_address, subject, body)
    db.execute(
        text("""
            INSERT INTO email_outbox (to_address, subject, body, status, error, related_user_id,
                                      last_attempt_at, sent_at)
            VALUES (:to, :subject, :body, CAST(:status AS VARCHAR), :error, :uid,
                    NOW(), CASE WHEN CAST(:status AS VARCHAR) = 'sent' THEN NOW() END)
        """),
        {"to": to_address, "subject": subject, "body": body, "status": status,
         "error": error, "uid": str(related_user_id) if related_user_id else None}
    )
    return status


def resend(db, email_id):
    """Send a stored email again (after the mail server was set up, or after a failure).
    Updates its status. Returns (status, error). The caller commits."""
    row = db.execute(text("SELECT to_address, subject, body FROM email_outbox WHERE email_id = :e"),
                     {"e": str(email_id)}).fetchone()
    status, error = _try_send(row.to_address, row.subject, row.body)
    db.execute(text("""
        UPDATE email_outbox SET status = CAST(:s AS VARCHAR), error = :err, attempts = attempts + 1,
               last_attempt_at = NOW(), sent_at = CASE WHEN CAST(:s AS VARCHAR) = 'sent' THEN NOW() ELSE sent_at END
        WHERE email_id = :e
    """), {"s": status, "err": error, "e": str(email_id)})
    return status, error


def test_email():
    subject = "SEAGAS test email"
    body = f"""This is a test email from SEAGAS.

If you can read this, the mail server settings in backend/.env work and SEAGAS can
send account emails to students and advisors.

Sign-in page: {FRONTEND_URL}/login
"""
    return subject, body


def welcome_email(full_name, student_number, school_email, temp_password, course_name=None, programme=None):
    """Subject and body of the account email a new student receives"""
    subject = "Your SEAGAS student account"
    course_line = f"  Course:              {course_name}\n" if course_name else ""
    if programme:
        course_line += f"  Programme:           {programme}\n"
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


def staff_welcome_email(full_name, staff_number, school_email, temp_password, position=None):
    """Subject and body of the account email a new advisor receives"""
    subject = "Your SEAGAS advisor account"
    position_line = f"  Position:            {position}\n" if position else ""
    body = f"""Dear {full_name},

Your SEAGAS advisor account has been created.

  Staff ID:            {staff_number}
{position_line}  School email:        {school_email}
  Temporary password:  {temp_password}

Sign in at {FRONTEND_URL}/login with your school email and the temporary
password (leave Student ID empty). You will be asked to choose your own password
straight away; the temporary password stops working after that.

If you did not expect this email, please contact the SEAGAS administrator.

SEAGAS - Student Employability Assessment and Skill Gap Analysis System
"""
    return subject, body
