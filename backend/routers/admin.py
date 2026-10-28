"""
SEAGAS — Admin Router
- Users: create advisor/admin accounts, rename, activate/deactivate, reset passwords
  (created and reset passwords are temporary: the owner must change them).
  Student accounts come from the intake lists (routers/intake.py).
- Skills library, job roles and learning resources (recommendations library):
  list all; add new ones; edit the ones admins added; activate/deactivate any.
- Audit log: read and filter.

Students do not register themselves (routers/intake.py); advisor and admin
accounts can only be created here, by a signed-in admin.

Who owns the library data: the 166 skills and 10 roles that come from
data/skills/skills_library.csv and the seed files are maintained there
(start_backend.bat re-applies the seeds), so admins can only switch them on or
off. Skills and roles that admins add (source = 'admin') are never touched by
the seeds and can be edited here. Learning resources follow the same rule with
database/seed_recommendations_library_final.sql.
"""

import re
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import audit
import notifications
import programmes
from advisor_scope import position_label, staff_prefix
from database import get_db
from routers.auth import ROLE_EMAIL_DOMAINS, check_email_domain, check_password, get_current_user, hash_password
from routers.intake import temporary_password
from routers.students import refresh_profile_complete

router = APIRouter()

STAFF_ROLES = ("advisor", "admin")
CATEGORIES = Literal["Technical", "AI_Digital", "Analytical", "Soft"]
LEVELS = Literal["entry", "junior", "mid", "senior"]
IMPORTANCE = Literal["required", "preferred", "bonus"]
RESOURCE_TYPES = Literal["course", "certification", "project", "workshop", "competition", "internship"]
DIFFICULTIES = Literal["beginner", "intermediate", "advanced"]
SEED_MANAGED = "This entry comes from the seed files (data/skills/skills_library.csv); " \
               "edit it there. Admins can only activate or deactivate it."
RESOURCE_SEED_MANAGED = "This resource comes from database/seed_recommendations_library_final.sql; " \
                        "edit it there. Admins can only activate or deactivate it."


# ── Permission Check ──────────────────────────────────────────
def require_admin(current_user):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")


# ── Pydantic Schemas ──────────────────────────────────────────
COURSE = Literal["CS", "BUSINESS", "ICT"]
POSITION = Literal["dean", "hop"]


class UserCreate(BaseModel):
    full_name: str = Field(max_length=255)
    role: str = "advisor"   # advisor | admin
    # Admins: school email and a temporary password typed by the admin.
    # Advisors: like students, the system makes a temporary password and emails the
    # staff ID, school email (default <staff ID>@advisor.newinti.edu.my) and password
    # to their personal email.
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    # Advisors only: Dean (Computing = CS + ICT, or Business) or Head of Programme of
    # one course, and a 5-digit staff ID (suggested when left out). See advisor_scope.py.
    advisor_position: Optional[POSITION] = None
    advisor_courses: Optional[List[COURSE]] = Field(None, min_length=1, max_length=2)
    staff_number: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    # School email (sign-in name); it must keep the domain of the account's role
    email: Optional[EmailStr] = None
    # Students only: one of the programmes of their course
    programme: Optional[str] = Field(None, max_length=150)
    is_active: Optional[bool] = None
    advisor_position: Optional[POSITION] = None
    advisor_courses: Optional[List[COURSE]] = Field(None, min_length=1, max_length=2)
    staff_number: Optional[str] = None


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
    # Courses whose students may choose this role as their target role
    courses: List[COURSE] = Field(["CS"], min_length=1, max_length=3)


class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    industry_level: Optional[LEVELS] = None
    courses: Optional[List[COURSE]] = Field(None, min_length=1, max_length=3)
    is_active: Optional[bool] = None


class RoleSkill(BaseModel):
    skill_id: UUID
    importance: IMPORTANCE = "required"


class ResourceCreate(BaseModel):
    skill_id: UUID
    resource_title: str = Field(min_length=1, max_length=255)
    resource_type: RESOURCE_TYPES = "course"
    provider: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = Field(None, max_length=2000)
    duration_hours: Optional[int] = Field(None, ge=0, le=10000)
    cost: Optional[str] = Field("Free", max_length=50)
    difficulty: DIFFICULTIES = "beginner"
    description: Optional[str] = Field(None, max_length=2000)


class ResourceUpdate(BaseModel):
    skill_id: Optional[UUID] = None
    resource_title: Optional[str] = Field(None, min_length=1, max_length=255)
    resource_type: Optional[RESOURCE_TYPES] = None
    provider: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = Field(None, max_length=2000)
    duration_hours: Optional[int] = Field(None, ge=0, le=10000)
    cost: Optional[str] = Field(None, max_length=50)
    difficulty: Optional[DIFFICULTIES] = None
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None


USER_COLUMNS = """user_id, email, full_name, role, student_number, course, staff_number,
                  advisor_position, advisor_courses, is_active, must_change_password, created_at,
                  (SELECT sp.programme FROM student_profiles sp WHERE sp.user_id = users.user_id) AS programme"""


def user_out(row):
    u = dict(row._mapping)
    u["position_label"] = position_label(u["advisor_position"], u["advisor_courses"])
    return u


NO_USER = "00000000-0000-0000-0000-000000000000"


def current_dean(db, courses, user_id=None):
    """The other active Dean of this office (CS + ICT, or Business), or None"""
    return db.execute(text("""
        SELECT user_id, full_name FROM users
        WHERE role = 'advisor' AND is_active AND advisor_position = 'dean'
          AND advisor_courses = CAST(:courses AS VARCHAR(10)[]) AND user_id <> CAST(:uid AS uuid)
    """), {"courses": sorted(set(courses)), "uid": str(user_id or NO_USER)}).fetchone()


def check_one_dean(db, position, courses, user_id=None):
    """Each office has only one active Dean"""
    if position != "dean":
        return
    other = current_dean(db, courses, user_id)
    if other:
        raise HTTPException(status_code=400, detail=(
            f"{other.full_name} is already the {position_label(position, courses)}. Change their "
            "position or deactivate their account first."))


def advisor_fields(db, position, courses, staff_number, user_id=None):
    """Checked (position, sorted courses, staff ID) for an advisor; the ID is suggested when None"""
    prefix = staff_prefix(position, courses)
    courses = sorted(set(courses))
    check_one_dean(db, position, courses, user_id)
    if staff_number is None:
        staff_number = db.execute(text("SELECT next_staff_number(:p)"), {"p": prefix}).scalar()
    else:
        staff_number = staff_number.strip()
        if not re.fullmatch(r"[0-9]{5}", staff_number):
            raise HTTPException(status_code=400, detail="The staff ID must be 5 digits.")
        if not staff_number.startswith(prefix):
            raise HTTPException(status_code=400, detail=(
                f"Staff IDs of the {position_label(position, courses)} start with {prefix}."))
        taken = db.execute(text("SELECT 1 FROM users WHERE staff_number = :n AND user_id <> CAST(:uid AS uuid)"),
                           {"n": staff_number, "uid": str(user_id or NO_USER)}).fetchone()
        if taken:
            raise HTTPException(status_code=400, detail=f"Staff ID {staff_number} is already used.")
    return position, courses, staff_number


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
    # Students per course (Computer Science / Business / ICT)
    courses = {c: 0 for c in ("CS", "BUSINESS", "ICT")}
    for c in db.execute(text("SELECT course, COUNT(*) AS n FROM users WHERE role = 'student' GROUP BY course")).fetchall():
        courses[c.course] = c.n
    stats["courses"] = courses
    return stats


@router.get("/users")
def list_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    course: Optional[str] = None,     # CS | BUSINESS | ICT (students only)
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
        where.append("(full_name ILIKE :q OR email ILIKE :q OR student_number LIKE :q OR staff_number LIKE :q)")
        params["q"] = f"%{search.strip()}%"
    if role:
        where.append("role = :role")
        params["role"] = role
    if course:
        where.append("course = :course")
        params["course"] = course.upper()
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

    return {"total": total, "users": [user_out(u) for u in users]}


@router.get("/staff-number")
def suggest_staff_number(position: POSITION, courses: List[COURSE] = Query(...),
                         current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """The next free staff ID for an advisor position (the admin may change it)"""
    require_admin(current_user)
    prefix = staff_prefix(position, courses)
    number = db.execute(text("SELECT next_staff_number(:p)"), {"p": prefix}).scalar()
    dean = current_dean(db, courses) if position == "dean" else None
    return {"staff_number": number, "position_label": position_label(position, courses),
            # Each office has one Dean: who holds the post now (the form warns the admin)
            "current_dean": {"user_id": str(dean.user_id), "full_name": dean.full_name} if dean else None}


@router.post("/users", status_code=201)
def create_user(req: UserCreate, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Create an advisor or admin account. Advisors get their login details by email."""
    require_admin(current_user)

    if req.role not in STAFF_ROLES:
        raise HTTPException(status_code=400,
                            detail="Admins create advisor or admin accounts here. Student accounts are created from the new-student lists (Student Intake).")
    if not req.full_name.strip():
        raise HTTPException(status_code=400, detail="Full name is required.")

    position = courses = number = None
    if req.role == "advisor":
        if not req.advisor_position or not req.advisor_courses:
            raise HTTPException(status_code=400, detail="Choose the advisor's position and course.")
        if not req.personal_email:
            raise HTTPException(status_code=400, detail="Enter the advisor's personal email: the login details are sent there.")
        position, courses, number = advisor_fields(db, req.advisor_position, req.advisor_courses, req.staff_number)
        email = (req.email or f"{number}@{ROLE_EMAIL_DOMAINS['advisor']}").strip().lower()
        if req.personal_email.lower() == email:
            raise HTTPException(status_code=400, detail="The personal email must not be the school email.")
        password = temporary_password()
    else:
        if req.advisor_position or req.advisor_courses or req.staff_number:
            raise HTTPException(status_code=400, detail="Only advisors have a position, courses and a staff ID.")
        if not req.email or not req.password:
            raise HTTPException(status_code=400, detail="Enter the email and a temporary password.")
        check_password(req.password)
        email, password = req.email.strip().lower(), req.password

    check_email_domain(email, req.role)
    if db.execute(text("SELECT 1 FROM users WHERE lower(email) = :e"), {"e": email}).fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = db.execute(
        text(f"""
            INSERT INTO users (email, password_hash, role, full_name, must_change_password,
                               advisor_position, advisor_courses, staff_number)
            VALUES (:email, :pw, :role, :name, TRUE,
                    :position, CAST(:courses AS VARCHAR(10)[]), :number)
            RETURNING {USER_COLUMNS}
        """),
        {"email": email, "pw": hash_password(password),
         "role": req.role, "name": req.full_name.strip(),
         "position": position, "courses": courses, "number": number}
    ).fetchone()
    audit.record(db, "admin.user_create", user=current_user, request=request,
                 target_type="user", target_id=user.user_id,
                 details={"email": email, "role": req.role, "advisor_position": position,
                          "advisor_courses": courses, "staff_number": number})
    out = user_out(user)
    if req.role == "advisor":
        subject, body = notifications.staff_welcome_email(user.full_name, number, email, password,
                                                          out["position_label"])
        out["email_status"] = notifications.send_email(db, str(req.personal_email), subject, body,
                                                       related_user_id=user.user_id)
        out["personal_email"] = str(req.personal_email)
    db.commit()
    return out


@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID,
    req: UserUpdate,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rename an account, change its school email, activate / deactivate it, or change an
    advisor's position, courses or staff ID"""
    require_admin(current_user)

    if req.is_active is False and str(current_user.user_id) == str(user_id):
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")

    sets, params = [], {"uid": str(user_id)}
    if req.full_name is not None:
        if not req.full_name.strip():
            raise HTTPException(status_code=400, detail="Full name cannot be empty.")
        sets.append("full_name = :name")
        params["name"] = req.full_name.strip()
    if req.email is not None:
        email = req.email.strip().lower()
        target = db.execute(text("SELECT role FROM users WHERE user_id = :uid"), {"uid": str(user_id)}).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        check_email_domain(email, target.role)
        if db.execute(text("SELECT 1 FROM users WHERE lower(email) = :e AND user_id <> CAST(:uid AS uuid)"),
                      {"e": email, "uid": str(user_id)}).fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        sets.append("email = :email")
        params["email"] = email
    if req.is_active is not None:
        sets.append("is_active = :active")
        params["active"] = req.is_active
    if req.programme is not None:
        target = db.execute(text("SELECT role, course FROM users WHERE user_id = :uid"),
                            {"uid": str(user_id)}).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if target.role != "student":
            raise HTTPException(status_code=400, detail="Only students have a programme.")
        programmes.set_programme(db, user_id, programmes.check_programme(db, req.programme, target.course))
        refresh_profile_complete(db, user_id)
        if not sets:
            sets.append("full_name = full_name")   # nothing else changed: still return the user
    if req.is_active and not (req.advisor_position or req.advisor_courses):
        # Activating a former Dean while the office has another one
        row = db.execute(text("SELECT advisor_position, advisor_courses FROM users WHERE user_id = :uid"),
                         {"uid": str(user_id)}).fetchone()
        if row and row.advisor_position:
            check_one_dean(db, row.advisor_position, row.advisor_courses, user_id)
    if req.advisor_position or req.advisor_courses or req.staff_number:
        old = db.execute(text("SELECT role, advisor_position, advisor_courses, staff_number FROM users "
                              "WHERE user_id = :uid"), {"uid": str(user_id)}).fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="User not found")
        if old.role != "advisor":
            raise HTTPException(status_code=400, detail="Only advisors have a position, courses and a staff ID.")
        position = req.advisor_position or old.advisor_position
        courses = req.advisor_courses or old.advisor_courses
        number = req.staff_number
        # A new position keeps the staff ID only if it still has the right prefix
        if number is None and old.staff_number.startswith(staff_prefix(position, courses)):
            number = old.staff_number
        position, courses, number = advisor_fields(db, position, courses, number, user_id)
        sets += ["advisor_position = :position", "advisor_courses = CAST(:courses AS VARCHAR(10)[])",
                 "staff_number = :number"]
        params.update(position=position, courses=courses, number=number)
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
    return user_out(user)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: UUID,
    req: PasswordReset,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a temporary password for any account; the owner must change it at next sign-in"""
    require_admin(current_user)
    check_password(req.password)

    updated = db.execute(
        text("""
            UPDATE users SET password_hash = :pw, must_change_password = TRUE,
                             updated_at = CURRENT_TIMESTAMP
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
                  jr.courses, jr.is_active, jr.source"""


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
            INSERT INTO job_roles (role_name, role_code, description, industry_level, courses, source)
            VALUES (:name, :code, :desc, :level, CAST(:courses AS VARCHAR(10)[]), 'admin')
            RETURNING role_id
        """),
        {"name": name, "code": code, "desc": req.description, "level": req.industry_level,
         "courses": sorted(set(req.courses))}
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

    if changes.get("courses") is not None:
        changes["courses"] = sorted(set(changes["courses"]))
    sets = [f"{k} = CAST(:{k} AS VARCHAR(10)[])" if k == "courses" else f"{k} = :{k}" for k in changes]
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


# ── Learning resources (recommendations library) ──────────────
RESOURCE_COLUMNS = """rl.resource_id, rl.skill_id, sl.skill_name, sl.category, rl.resource_title,
                      rl.resource_type, rl.provider, rl.url, rl.duration_hours, rl.cost,
                      rl.difficulty, rl.description, rl.is_active, rl.source"""


def get_resource_row(db, resource_id):
    row = db.execute(text(f"""
        SELECT {RESOURCE_COLUMNS}
        FROM recommendations_library rl
        JOIN skills_library sl ON sl.skill_id = rl.skill_id
        WHERE rl.resource_id = :rid
    """), {"rid": str(resource_id)}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Resource not found")
    return row


def check_resource_unique(db, skill_id, title, resource_id=None):
    """uq_resource_skill: one title per skill"""
    clash = db.execute(text("""
        SELECT 1 FROM recommendations_library
        WHERE skill_id = :sid AND lower(resource_title) = lower(:t)
          AND resource_id <> COALESCE(CAST(:rid AS uuid), '00000000-0000-0000-0000-000000000000')
    """), {"sid": str(skill_id), "t": title, "rid": str(resource_id) if resource_id else None}).fetchone()
    if clash:
        raise HTTPException(status_code=400, detail="This skill already has a resource with that title")


def check_skill_exists(db, skill_id):
    if not db.execute(text("SELECT 1 FROM skills_library WHERE skill_id = :sid"),
                      {"sid": str(skill_id)}).fetchone():
        raise HTTPException(status_code=400, detail="Unknown skill")


@router.get("/resources")
def list_resources(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Every learning resource, active or not, with how many students started / finished it"""
    require_admin(current_user)
    rows = db.execute(text(f"""
        SELECT {RESOURCE_COLUMNS},
               COUNT(srp.progress_id)                                         AS student_count,
               COUNT(srp.progress_id) FILTER (WHERE srp.status = 'completed') AS completed_count
        FROM recommendations_library rl
        JOIN skills_library sl ON sl.skill_id = rl.skill_id
        LEFT JOIN student_resource_progress srp ON srp.resource_id = rl.resource_id
        GROUP BY rl.resource_id, sl.skill_id
        ORDER BY sl.skill_name, rl.resource_title
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/resources", status_code=201)
def create_resource(req: ResourceCreate, request: Request,
                    current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a learning resource for a skill (source = 'admin'; the seed file never changes it)"""
    require_admin(current_user)
    title = req.resource_title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required.")
    check_skill_exists(db, req.skill_id)
    check_resource_unique(db, req.skill_id, title)
    data = req.model_dump()
    data.update(resource_title=title, skill_id=str(req.skill_id),
                provider=(req.provider or "").strip() or None,
                url=(req.url or "").strip() or None,
                cost=(req.cost or "").strip() or "Free")
    row = db.execute(
        text("""
            INSERT INTO recommendations_library
                (skill_id, resource_title, resource_type, provider, url, duration_hours,
                 cost, difficulty, description, source)
            VALUES (:skill_id, :resource_title, :resource_type, :provider, :url, :duration_hours,
                    :cost, :difficulty, :description, 'admin')
            RETURNING resource_id
        """),
        data
    ).fetchone()
    audit.record(db, "admin.resource_create", user=current_user, request=request,
                 target_type="resource", target_id=row.resource_id,
                 details={"resource_title": title, "resource_type": req.resource_type})
    db.commit()
    return dict(get_resource_row(db, row.resource_id)._mapping)


@router.patch("/resources/{resource_id}")
def update_resource(resource_id: UUID, req: ResourceUpdate, request: Request,
                    current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Activate / deactivate any resource; edit the details of admin-added resources.
    Inactive resources are no longer recommended (recommendation/engine.py filters on is_active)."""
    require_admin(current_user)
    res = get_resource_row(db, resource_id)
    changes = req.model_dump(exclude_unset=True)
    content = {k: v for k, v in changes.items() if k != "is_active"}
    if content and res.source != "admin":
        raise HTTPException(status_code=400, detail=RESOURCE_SEED_MANAGED)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    for field in ("resource_title", "resource_type", "difficulty", "is_active"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ')} cannot be empty.")
    if "resource_title" in changes:
        changes["resource_title"] = changes["resource_title"].strip()
    if "skill_id" in changes:
        if changes["skill_id"] is None:
            raise HTTPException(status_code=400, detail="A resource must belong to a skill.")
        check_skill_exists(db, changes["skill_id"])
        changes["skill_id"] = str(changes["skill_id"])
    if "skill_id" in changes or "resource_title" in changes:
        check_resource_unique(db, changes.get("skill_id", res.skill_id),
                              changes.get("resource_title", res.resource_title), resource_id)

    sets = [f"{k} = :{k}" for k in changes]
    db.execute(text(f"UPDATE recommendations_library SET {', '.join(sets)} WHERE resource_id = :rid"),
               {**changes, "rid": str(resource_id)})
    audit.record(db, "admin.resource_update", user=current_user, request=request,
                 target_type="resource", target_id=resource_id, details=changes)
    db.commit()
    return dict(get_resource_row(db, resource_id)._mapping)


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
