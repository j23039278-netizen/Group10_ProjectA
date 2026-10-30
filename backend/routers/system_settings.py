"""
SEAGAS — System settings API (FR-16)

GET /api/settings              current values, for any signed-in page (no secrets)
GET /api/admin/settings        values with labels, limits and who changed them (admins)
PUT /api/admin/settings        change some values (admins, audited)

The list of settings, defaults and limits is backend/settings.py.
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

import audit
import notifications
import settings
from database import get_db
from routers.auth import get_current_user

public_router = APIRouter()
admin_router = APIRouter()


class SettingsUpdate(BaseModel):
    values: Dict[str, Any]


class TestEmail(BaseModel):
    to: EmailStr


def require_admin(user):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")


def admin_view(db):
    stored = {r.key: r for r in db.execute(text("""
        SELECT s.key, s.updated_at, u.full_name AS updated_by FROM system_settings s
        LEFT JOIN users u ON u.user_id = s.updated_by
    """)).fetchall()}
    values = settings.get_all(db)
    items = []
    for key, d in settings.DEFINITIONS.items():
        row = stored.get(key)
        items.append({"key": key, "label": d["label"], "help": d["help"], "value": values[key], "default": d["default"],
                      "min": d.get("min"), "max": d.get("max"),
                      "updated_by": row.updated_by if row else None, "updated_at": row.updated_at if row else None})
    return {"settings": items, "email": notifications.mail_status()}


@public_router.get("")
def get_settings(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return settings.get_all(db)


@admin_router.get("")
def get_admin_settings(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(current_user)
    return admin_view(db)


@admin_router.put("")
def update_settings(req: SettingsUpdate, request: Request,
                    current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(current_user)
    current = settings.get_all(db)
    changes = settings.validate(req.values, current)
    changed = {k: v for k, v in changes.items() if v != current[k]}
    for key, value in changed.items():
        db.execute(text("""
            INSERT INTO system_settings (key, value, updated_by, updated_at)
            VALUES (:k, CAST(:v AS JSONB), :u, NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_by = EXCLUDED.updated_by, updated_at = NOW()
        """), {"k": key, "v": json.dumps(value), "u": str(current_user.user_id)})
    if changed:
        audit.record(db, "admin.settings_update", user=current_user, request=request, target_type="settings",
                     details={k: {"from": current[k], "to": v} for k, v in changed.items()})
    db.commit()
    return admin_view(db)


@admin_router.post("/test-email")
def send_test_email(req: TestEmail, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a test email with the mail server settings in backend/.env (also kept in the outbox)"""
    require_admin(current_user)
    if not notifications.smtp_configured():
        raise HTTPException(status_code=400, detail="No mail server is set up yet: add the SMTP settings to backend/.env and restart the backend.")
    subject, body = notifications.test_email()
    status = notifications.send_email(db, str(req.to), subject, body)
    error = db.execute(text("SELECT error FROM email_outbox WHERE to_address = :t ORDER BY created_at DESC LIMIT 1"),
                       {"t": str(req.to)}).scalar()
    db.commit()
    return {"status": status, "error": error}
