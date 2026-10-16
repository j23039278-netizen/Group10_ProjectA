"""
SEAGAS — Admin Router
- Users: create advisor/admin accounts, rename, activate/deactivate, reset passwords.
- Skills library and job roles: list all; add new ones; edit the ones admins
  added; activate/deactivate any.
- Audit log: read and filter.

Students register themselves through /api/auth/register; advisor and admin
accounts can only be created here, by a signed-in admin.

Who owns the library data: the 138 skills and 6 roles that come from
data/skills/skills_library.csv and the seed files are maintained there
(start_backend.bat re-applies the seeds), so admins can only switch them on or
off. Skills and roles that admins add (source = 'admin') are never touched by
the seeds and can be edited here.
"""

import re
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import audit
from database import get_db
from routers.auth import check_email_domain, check_password, get_current_user, hash_password

router = APIRouter()

STAFF_ROLES = ("advisor", "admin")
CATEGORIES = Literal["Technical", "AI_Digital", "Analytical", "Soft"]
LEVELS = Literal["entry", "junior", "mid", "senior"]
IMPORTANCE = Literal["required", "preferred", "bonus"]
SEED_MANAGED = "This entry comes from the seed files (data/skills/skills_library.csv); " \
               "edit it there. Admins can only activate or deactivate it."


# ── Permission Check ──────────────────────────────────────────
def require_admin(current_user):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")


# ── Pydantic Schemas ──────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(max_length=255)
    password: str
    role: str = "advisor"   # advisor | admin


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    password: str


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    category: CATEGORIES
    subcategory: Optional[str] = Field(None, max_length=50)
    aliases: List[str] = Field([], max_length=30)
    description: Optional[str] = Field(None, max_length=1000)


class SkillUpdate(BaseModel):
    category: Optional[CATEGORIES] = None
    subcategory: Optional[str] = Field(None, max_length=50)
    aliases: Optional[List[str]] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class RoleCreate(BaseModel):
    role_name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    industry_level: LEVELS = "junior"


class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    industry_level: Optional[LEVELS] = None
    is_active: Optional[bool] = None


class RoleSkill(BaseModel):
    skill_id: UUID
    importance: IMPORTANCE = "required"


USER_COLUMNS = "user_id, email, full_name, role, is_active, created_at"


def clean_list(items):
    """Trimmed, non-empty, de-duplicated (case-insensitive) strings"""
    seen, out = set(), []
    for i in items or []:
        i = i.strip()
        if i and i.lower() not in seen:
            seen.add(i.lower())
            out.append(i[:100])
    return out


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
def create_user(req: UserCreate, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
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
    audit.record(db, "admin.user_create", user=current_user, request=request,
                 target_type="user", target_id=user.user_id,
                 details={"email": email, "role": req.role})
    db.commit()
    return dict(user._mapping)


@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID,
    req: UserUpdate,
    request: Request,
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
    audit.record(db, "admin.user_update", user=current_user, request=request,
                 target_type="user", target_id=user_id,
                 details=req.model_dump(exclude_none=True))
    db.commit()
    return dict(user._mapping)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: UUID,
    req: PasswordReset,
    request: Request,
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
    audit.record(db, "admin.password_reset", user=current_user, request=request,
                 target_type="user", target_id=user_id)
    db.commit()
    return {"message": "Password updated"}


# ── Skills library ────────────────────────────────────────────
SKILL_COLUMNS = """sl.skill_id, sl.skill_name, sl.category, sl.subcategory, sl.aliases,
                   sl.description, sl.source, sl.is_active"""


def get_skill_row(db, skill_id):
    row = db.execute(text(f"SELECT {SKILL_COLUMNS} FROM skills_library sl WHERE skill_id = :sid"),
                     {"sid": str(skill_id)}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Skill not found")
    return row


@router.get("/skills")
def list_skills(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Every skill, active or not, with how many role templates use it"""
    require_admin(current_user)
    skills = db.execute(text(f"""
        SELECT {SKILL_COLUMNS}, COUNT(jrs.role_skill_id) AS role_count
        FROM skills_library sl
        LEFT JOIN job_role_skills jrs ON jrs.skill_id = sl.skill_id
        GROUP BY sl.skill_id
        ORDER BY sl.category, sl.skill_name
    """)).fetchall()
    return [dict(s._mapping) for s in skills]


@router.post("/skills", status_code=201)
def create_skill(req: SkillCreate, request: Request,
                 current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a skill to the library (source = 'admin'; the seed files never change it)"""
    require_admin(current_user)
    name = req.skill_name.strip()
    if db.execute(text("SELECT 1 FROM skills_library WHERE lower(skill_name) = lower(:n)"),
                  {"n": name}).fetchone():
        raise HTTPException(status_code=400, detail=f"A skill called {name} already exists")
    row = db.execute(
        text("""
            INSERT INTO skills_library (skill_name, category, subcategory, aliases, description, source)
            VALUES (:name, :cat, :sub, :aliases, :desc, 'admin')
            RETURNING skill_id
        """),
        {"name": name, "cat": req.category, "sub": (req.subcategory or "").strip() or None,
         "aliases": clean_list(req.aliases), "desc": req.description}
    ).fetchone()
    audit.record(db, "admin.skill_create", user=current_user, request=request,
                 target_type="skill", target_id=row.skill_id,
                 details={"skill_name": name, "category": req.category})
    db.commit()
    return dict(get_skill_row(db, row.skill_id)._mapping)


@router.patch("/skills/{skill_id}")
def update_skill(skill_id: UUID, req: SkillUpdate, request: Request,
                 current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Activate / deactivate any skill; edit the details of admin-added skills"""
    require_admin(current_user)
    skill = get_skill_row(db, skill_id)
    changes = req.model_dump(exclude_unset=True)
    content = {k: v for k, v in changes.items() if k != "is_active"}
    if content and skill.source != "admin":
        raise HTTPException(status_code=400, detail=SEED_MANAGED)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    sets, params = [], {"sid": str(skill_id)}
    for field in ("category", "subcategory", "description", "is_active"):
        if field in changes:
            sets.append(f"{field} = :{field}")
            params[field] = changes[field]
    if "aliases" in changes:
        sets.append("aliases = :aliases")
        params["aliases"] = clean_list(changes["aliases"])
    db.execute(text(f"UPDATE skills_library SET {', '.join(sets)} WHERE skill_id = :sid"), params)
    audit.record(db, "admin.skill_update", user=current_user, request=request,
                 target_type="skill", target_id=skill_id, details=changes)
    db.commit()
    return dict(get_skill_row(db, skill_id)._mapping)


# ── Job roles ─────────────────────────────────────────────────
ROLE_COLUMNS = """jr.role_id, jr.role_name, jr.role_code, jr.description, jr.industry_level,
                  jr.is_active, jr.source"""


def get_role_row(db, role_id):
    row = db.execute(text(f"SELECT {ROLE_COLUMNS} FROM job_roles jr WHERE role_id = :rid"),
                     {"rid": str(role_id)}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job role not found")
    return row


@router.get("/roles")
def list_roles(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Every role template, active or not, with skill counts"""
    require_admin(current_user)
    roles = db.execute(text(f"""
        SELECT {ROLE_COLUMNS},
               COUNT(jrs.role_skill_id)                                            AS skill_count,
               COUNT(jrs.role_skill_id) FILTER (WHERE jrs.importance = 'required') AS required_count
        FROM job_roles jr
        LEFT JOIN job_role_skills jrs ON jrs.role_id = jr.role_id
        GROUP BY jr.role_id
        ORDER BY jr.role_name
    """)).fetchall()
    return [dict(r._mapping) for r in roles]


@router.get("/roles/{role_id}/skills")
def get_role_skills(role_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(current_user)
    role = get_role_row(db, role_id)
    skills = db.execute(text("""
        SELECT sl.skill_id, sl.skill_name, sl.category, jrs.importance
        FROM job_role_skills jrs
        JOIN skills_library sl ON sl.skill_id = jrs.skill_id
        WHERE jrs.role_id = :rid
        ORDER BY CASE jrs.importance WHEN 'required' THEN 1 WHEN 'preferred' THEN 2 ELSE 3 END,
                 sl.skill_name
    """), {"rid": str(role_id)}).fetchall()
    return {"role": dict(role._mapping), "skills": [dict(s._mapping) for s in skills]}


@router.post("/roles", status_code=201)
def create_role(req: RoleCreate, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a job role template (source = 'admin'); set its skills with PUT /roles/{id}/skills"""
    require_admin(current_user)
    name = req.role_name.strip()
    code = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")[:30] or "ROLE"
    if db.execute(text("SELECT 1 FROM job_roles WHERE lower(role_name) = lower(:n) OR role_code = :c"),
                  {"n": name, "c": code}).fetchone():
        raise HTTPException(status_code=400, detail=f"A role called {name} already exists")
    row = db.execute(
        text("""
            INSERT INTO job_roles (role_name, role_code, description, industry_level, source)
            VALUES (:name, :code, :desc, :level, 'admin')
            RETURNING role_id
        """),
        {"name": name, "code": code, "desc": req.description, "level": req.industry_level}
    ).fetchone()
    audit.record(db, "admin.role_create", user=current_user, request=request,
                 target_type="job_role", target_id=row.role_id, details={"role_name": name})
    db.commit()
    return dict(get_role_row(db, row.role_id)._mapping)


@router.patch("/roles/{role_id}")
def update_role(role_id: UUID, req: RoleUpdate, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Activate / deactivate any role; edit the details of admin-added roles"""
    require_admin(current_user)
    role = get_role_row(db, role_id)
    changes = req.model_dump(exclude_unset=True)
    content = {k: v for k, v in changes.items() if k != "is_active"}
    if content and role.source != "admin":
        raise HTTPException(status_code=400, detail=SEED_MANAGED)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    if "role_name" in changes:
        changes["role_name"] = changes["role_name"].strip()
        if db.execute(text("SELECT 1 FROM job_roles WHERE lower(role_name) = lower(:n) AND role_id <> :rid"),
                      {"n": changes["role_name"], "rid": str(role_id)}).fetchone():
            raise HTTPException(status_code=400, detail="Another role already has that name")

    sets = [f"{k} = :{k}" for k in changes]
    db.execute(text(f"UPDATE job_roles SET {', '.join(sets)} WHERE role_id = :rid"),
               {**changes, "rid": str(role_id)})
    audit.record(db, "admin.role_update", user=current_user, request=request,
                 target_type="job_role", target_id=role_id, details=changes)
    db.commit()
    return dict(get_role_row(db, role_id)._mapping)


@router.put("/roles/{role_id}/skills")
def set_role_skills(role_id: UUID, skills: List[RoleSkill], request: Request,
                    current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Replace the required skills of an admin-added role"""
    require_admin(current_user)
    role = get_role_row(db, role_id)
    if role.source != "admin":
        raise HTTPException(status_code=400, detail=SEED_MANAGED)
    ids = [str(s.skill_id) for s in skills]
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=400, detail="A skill is listed twice")
    if ids:
        found = db.execute(text("SELECT COUNT(*) FROM skills_library WHERE skill_id = ANY(CAST(:ids AS uuid[]))"),
                           {"ids": ids}).scalar()
        if found != len(ids):
            raise HTTPException(status_code=400, detail="Unknown skill in the list")

    db.execute(text("DELETE FROM job_role_skills WHERE role_id = :rid"), {"rid": str(role_id)})
    if skills:
        db.execute(
            text("INSERT INTO job_role_skills (role_id, skill_id, importance) VALUES (:rid, :sid, :imp)"),
            [{"rid": str(role_id), "sid": str(s.skill_id), "imp": s.importance} for s in skills]
        )
    audit.record(db, "admin.role_update", user=current_user, request=request,
                 target_type="job_role", target_id=role_id,
                 details={"skills": len(skills),
                          "required": sum(s.importance == "required" for s in skills)})
    db.commit()
    return get_role_skills(role_id, current_user, db)


# ── Audit log ─────────────────────────────────────────────────
@router.get("/audit-log")
def list_audit_log(
    action: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Newest first. action may be a prefix such as 'admin.' or 'auth.'"""
    require_admin(current_user)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    where, params = ["TRUE"], {}
    if action:
        where.append("action LIKE :action")
        params["action"] = action.strip() + "%"
    if search:
        where.append("(actor_email ILIKE :q OR target_id ILIKE :q)")
        params["q"] = f"%{search.strip()}%"
    where_sql = " AND ".join(where)

    total = db.execute(text(f"SELECT COUNT(*) FROM audit_log WHERE {where_sql}"), params).scalar()
    rows = db.execute(
        text(f"""
            SELECT log_id, created_at, actor_email, actor_role, action,
                   target_type, target_id, details, ip_address
            FROM audit_log
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset}
    ).fetchall()
    return {"total": total, "entries": [dict(r._mapping) for r in rows], "actions": list(audit.ACTIONS)}
