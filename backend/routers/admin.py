"""
SEAGAS — Admin Router
User management (create advisor/admin accounts, activate/deactivate,
reset passwords) and read-only views of the skills library and job roles.

Students register themselves through /api/auth/register; advisor and admin
accounts can only be created here, by a signed-in admin.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import check_email_domain, get_current_user, hash_password

router = APIRouter()

PASSWORD_MIN = 8
STAFF_ROLES = ("advisor", "admin")


# ── Permission Check ──────────────────────────────────────────
def require_admin(current_user):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")


def check_password(password: str):
    if len(password) < PASSWORD_MIN:
        raise HTTPException(status_code=400,
                            detail=f"Password must be at least {PASSWORD_MIN} characters.")


# ── Pydantic Schemas ──────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "advisor"   # advisor | admin


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    password: str


USER_COLUMNS = "user_id, email, full_name, role, is_active, created_at"


# ── Users ─────────────────────────────────────────────────────
@router.get("/stats")
def get_user_stats(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Account counts per role for the admin overview cards"""
    require_admin(current_user)

    rows = db.execute(text("""
        SELECT role,
               COUNT(*)                             AS total,
               COUNT(*) FILTER (WHERE is_active)    AS active
        FROM users
        GROUP BY role
    """)).fetchall()

    stats = {r: {"total": 0, "active": 0} for r in ("student", "advisor", "admin")}
    for r in rows:
        stats[r.role] = {"total": r.total, "active": r.active}
    return stats


@router.get("/users")
def list_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Paged account list. Advisors and admins are listed before students."""
    require_admin(current_user)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    where, params = ["TRUE"], {}
    if search:
        where.append("(full_name ILIKE :q OR email ILIKE :q)")
        params["q"] = f"%{search.strip()}%"
    if role:
        where.append("role = :role")
        params["role"] = role
    where_sql = " AND ".join(where)

    total = db.execute(text(f"SELECT COUNT(*) FROM users WHERE {where_sql}"), params).scalar()
    users = db.execute(
        text(f"""
            SELECT {USER_COLUMNS}
            FROM users
            WHERE {where_sql}
            ORDER BY CASE role WHEN 'admin' THEN 1 WHEN 'advisor' THEN 2 ELSE 3 END,
                     full_name
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset}
    ).fetchall()

    return {"total": total, "users": [dict(u._mapping) for u in users]}


@router.post("/users", status_code=201)
def create_user(req: UserCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Create an advisor or admin account"""
    require_admin(current_user)

    if req.role not in STAFF_ROLES:
        raise HTTPException(status_code=400,
                            detail="Admins can create advisor or admin accounts. Students register themselves.")
    if not req.full_name.strip():
        raise HTTPException(status_code=400, detail="Full name is required.")
    check_password(req.password)

    email = req.email.strip().lower()
    check_email_domain(email, req.role)
    if db.execute(text("SELECT 1 FROM users WHERE lower(email) = :e"), {"e": email}).fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = db.execute(
        text(f"""
            INSERT INTO users (email, password_hash, role, full_name)
            VALUES (:email, :pw, :role, :name)
            RETURNING {USER_COLUMNS}
        """),
        {"email": email, "pw": hash_password(req.password),
         "role": req.role, "name": req.full_name.strip()}
    ).fetchone()
    db.commit()
    return dict(user._mapping)


@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID,
    req: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rename an account, or activate / deactivate it"""
    require_admin(current_user)

    if req.is_active is False and str(current_user.user_id) == str(user_id):
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")

    sets, params = [], {"uid": str(user_id)}
    if req.full_name is not None:
        if not req.full_name.strip():
            raise HTTPException(status_code=400, detail="Full name cannot be empty.")
        sets.append("full_name = :name")
        params["name"] = req.full_name.strip()
    if req.is_active is not None:
        sets.append("is_active = :active")
        params["active"] = req.is_active
    if not sets:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    user = db.execute(
        text(f"""
            UPDATE users SET {", ".join(sets)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :uid
            RETURNING {USER_COLUMNS}
        """),
        params
    ).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.commit()
    return dict(user._mapping)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: UUID,
    req: PasswordReset,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a new password for any account"""
    require_admin(current_user)
    check_password(req.password)

    updated = db.execute(
        text("""
            UPDATE users SET password_hash = :pw, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :uid
            RETURNING user_id
        """),
        {"pw": hash_password(req.password), "uid": str(user_id)}
    ).fetchone()
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    db.commit()
    return {"message": "Password updated"}


# ── Skills & Role Library (read-only) ─────────────────────────
@router.get("/skills")
def list_skills(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(current_user)
    skills = db.execute(text("""
        SELECT sl.skill_id, sl.skill_name, sl.category, sl.subcategory,
               sl.aliases, sl.source,
               COUNT(jrs.role_skill_id) AS role_count
        FROM skills_library sl
        LEFT JOIN job_role_skills jrs ON jrs.skill_id = sl.skill_id
        WHERE sl.is_active = TRUE
        GROUP BY sl.skill_id
        ORDER BY sl.category, sl.skill_name
    """)).fetchall()
    return [dict(s._mapping) for s in skills]


@router.get("/roles")
def list_roles(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(current_user)
    roles = db.execute(text("""
        SELECT jr.role_id, jr.role_name, jr.industry_level,
               COUNT(jrs.role_skill_id)                                    AS skill_count,
               COUNT(jrs.role_skill_id) FILTER (WHERE jrs.importance = 'required') AS required_count
        FROM job_roles jr
        LEFT JOIN job_role_skills jrs ON jrs.role_id = jr.role_id
        WHERE jr.is_active = TRUE
        GROUP BY jr.role_id
        ORDER BY jr.role_name
    """)).fetchall()
    return [dict(r._mapping) for r in roles]
