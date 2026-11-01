"""
SEAGAS — Library Router: skills library, job role templates and learning resources
(recommendations library). Admins manage every entry; advisors manage the entries
of their own courses (the lecturer's feedback of 22 October moved this to advisors).

- Everyone on staff sees every entry, active or not.
- Adding: an advisor's skills and roles must be for their courses only; a resource
  can be added for any skill their students see.
- Changing (edit, activate / deactivate): an advisor can change a skill or role whose
  courses are all theirs, and a resource whose skill's courses are all theirs or that
  they added. Shared entries (for example soft skills in every course) stay with admins,
  so one course cannot switch them off for another.
- Each list row has can_edit for the signed-in user.

Who owns the library data: the skills and roles that come from
data/skills/skills_library.csv and the seed files are maintained there
(start_backend.bat re-applies the seeds), so they can only be switched on or off
here. Skills and roles added on the website (source = 'admin') are never touched by
the seeds and can be edited. Learning resources follow the same rule with
database/seed_recommendations_library_final.sql.
"""

import re
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import audit
from advisor_scope import courses_of
from database import get_db
from routers.auth import get_current_user

router = APIRouter()

COURSE = Literal["CS", "BUSINESS", "ICT"]
CATEGORIES = Literal["Technical", "AI_Digital", "Analytical", "Soft"]
LEVELS = Literal["entry", "junior", "mid", "senior"]
IMPORTANCE = Literal["required", "preferred", "bonus"]
RESOURCE_TYPES = Literal["course", "certification", "project", "workshop", "competition", "internship"]
DIFFICULTIES = Literal["beginner", "intermediate", "advanced"]
SEED_MANAGED = "This entry comes from the seed files (data/skills/skills_library.csv); " \
               "edit it there. Admins can only activate or deactivate it."
RESOURCE_SEED_MANAGED = "This resource comes from database/seed_recommendations_library_final.sql; " \
                        "edit it there. Admins can only activate or deactivate it."
NOT_YOURS = "This entry is also used by courses you do not manage, so only an admin can change it."


# ── Permission Check ──────────────────────────────────────────
def library_scope(current_user):
    """None for admins (every course); an advisor's courses"""
    if current_user.role == "admin":
        return None
    if current_user.role == "advisor":
        return courses_of(current_user)
    raise HTTPException(status_code=403, detail="Access denied. Admin or advisor role required.")


def within(scope, courses):
    """All of these courses are managed by the user"""
    return scope is None or set(courses or []) <= set(scope)


def check_within(scope, courses, detail=NOT_YOURS):
    if not within(scope, courses):
        raise HTTPException(status_code=403, detail=detail)


# ── Pydantic Schemas ──────────────────────────────────────────
class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    category: CATEGORIES
    subcategory: Optional[str] = Field(None, max_length=50)
    aliases: List[str] = Field([], max_length=30)
    description: Optional[str] = Field(None, max_length=1000)
    # Courses whose students see the skill when adding their skills
    courses: List[COURSE] = Field(["CS", "BUSINESS", "ICT"], min_length=1, max_length=3)


class SkillUpdate(BaseModel):
    category: Optional[CATEGORIES] = None
    subcategory: Optional[str] = Field(None, max_length=50)
    aliases: Optional[List[str]] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=1000)
    courses: Optional[List[COURSE]] = Field(None, min_length=1, max_length=3)
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


def clean_list(items):
    """Trimmed, non-empty, de-duplicated (case-insensitive) strings"""
    seen, out = set(), []
    for i in items or []:
        i = i.strip()
        if i and i.lower() not in seen:
            seen.add(i.lower())
            out.append(i[:100])
    return out


# ── Skills library ────────────────────────────────────────────
SKILL_COLUMNS = """sl.skill_id, sl.skill_name, sl.category, sl.subcategory, sl.aliases,
                   sl.description, sl.courses, sl.source, sl.is_active"""


def get_skill_row(db, skill_id):
    row = db.execute(text(f"SELECT {SKILL_COLUMNS} FROM skills_library sl WHERE skill_id = :sid"),
                     {"sid": str(skill_id)}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Skill not found")
    return row


@router.get("/skills")
def list_skills(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Every skill, active or not, with how many role templates use it"""
    scope = library_scope(current_user)
    skills = db.execute(text(f"""
        SELECT {SKILL_COLUMNS}, COUNT(jrs.role_skill_id) AS role_count
        FROM skills_library sl
        LEFT JOIN job_role_skills jrs ON jrs.skill_id = sl.skill_id
        GROUP BY sl.skill_id
        ORDER BY sl.category, sl.skill_name
    """)).fetchall()
    return [{**s._mapping, "can_edit": within(scope, s.courses)} for s in skills]


@router.post("/skills", status_code=201)
def create_skill(req: SkillCreate, request: Request,
                 current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a skill to the library (source = 'admin'; the seed files never change it)"""
    scope = library_scope(current_user)
    check_within(scope, req.courses, "Choose only the courses you manage.")
    name = req.skill_name.strip()
    if db.execute(text("SELECT 1 FROM skills_library WHERE lower(skill_name) = lower(:n)"),
                  {"n": name}).fetchone():
        raise HTTPException(status_code=400, detail=f"A skill called {name} already exists")
    row = db.execute(
        text("""
            INSERT INTO skills_library (skill_name, category, subcategory, aliases, description, courses, source)
            VALUES (:name, :cat, :sub, :aliases, :desc, CAST(:courses AS VARCHAR(10)[]), 'admin')
            RETURNING skill_id
        """),
        {"name": name, "cat": req.category, "sub": (req.subcategory or "").strip() or None,
         "aliases": clean_list(req.aliases), "desc": req.description,
         "courses": sorted(set(req.courses))}
    ).fetchone()
    audit.record(db, "admin.skill_create", user=current_user, request=request,
                 target_type="skill", target_id=row.skill_id,
                 details={"skill_name": name, "category": req.category})
    db.commit()
    return dict(get_skill_row(db, row.skill_id)._mapping)


@router.patch("/skills/{skill_id}")
def update_skill(skill_id: UUID, req: SkillUpdate, request: Request,
                 current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Activate / deactivate any skill; edit the details of skills added on the website"""
    scope = library_scope(current_user)
    skill = get_skill_row(db, skill_id)
    check_within(scope, skill.courses)
    changes = req.model_dump(exclude_unset=True)
    if changes.get("courses"):
        check_within(scope, changes["courses"], "Choose only the courses you manage.")
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
    if changes.get("courses"):
        sets.append("courses = CAST(:courses AS VARCHAR(10)[])")
        params["courses"] = sorted(set(changes["courses"]))
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
    scope = library_scope(current_user)
    roles = db.execute(text(f"""
        SELECT {ROLE_COLUMNS},
               COUNT(jrs.role_skill_id)                                            AS skill_count,
               COUNT(jrs.role_skill_id) FILTER (WHERE jrs.importance = 'required') AS required_count
        FROM job_roles jr
        LEFT JOIN job_role_skills jrs ON jrs.role_id = jr.role_id
        GROUP BY jr.role_id
        ORDER BY jr.role_name
    """)).fetchall()
    return [{**r._mapping, "can_edit": within(scope, r.courses)} for r in roles]


@router.get("/roles/{role_id}/skills")
def get_role_skills(role_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    scope = library_scope(current_user)
    role = get_role_row(db, role_id)
    role = {**role._mapping, "can_edit": within(scope, role.courses)}
    skills = db.execute(text("""
        SELECT sl.skill_id, sl.skill_name, sl.category, jrs.importance
        FROM job_role_skills jrs
        JOIN skills_library sl ON sl.skill_id = jrs.skill_id
        WHERE jrs.role_id = :rid
        ORDER BY CASE jrs.importance WHEN 'required' THEN 1 WHEN 'preferred' THEN 2 ELSE 3 END,
                 sl.skill_name
    """), {"rid": str(role_id)}).fetchall()
    return {"role": role, "skills": [dict(s._mapping) for s in skills]}


@router.post("/roles", status_code=201)
def create_role(req: RoleCreate, request: Request,
                current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a job role template (source = 'admin'); set its skills with PUT /roles/{id}/skills"""
    scope = library_scope(current_user)
    check_within(scope, req.courses, "Choose only the courses you manage.")
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
    """Activate / deactivate any role; edit the details of roles added on the website"""
    scope = library_scope(current_user)
    role = get_role_row(db, role_id)
    check_within(scope, role.courses)
    changes = req.model_dump(exclude_unset=True)
    if changes.get("courses"):
        check_within(scope, changes["courses"], "Choose only the courses you manage.")
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
    """Replace the required skills of a role added on the website"""
    scope = library_scope(current_user)
    role = get_role_row(db, role_id)
    check_within(scope, role.courses)
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
                      rl.difficulty, rl.description, rl.is_active, rl.source,
                      sl.courses AS skill_courses, rl.created_by"""


def can_change_resource(scope, current_user, res):
    """The skill's courses are all the user's, or the user added the resource"""
    return within(scope, res.skill_courses) or str(res.created_by) == str(current_user.user_id)


def check_skill_visible(db, scope, skill_id):
    """Advisors add resources only for skills their students see"""
    courses = db.execute(text("SELECT courses FROM skills_library WHERE skill_id = :sid"),
                         {"sid": str(skill_id)}).scalar()
    if scope is not None and not set(courses or []) & set(scope):
        raise HTTPException(status_code=403, detail="This skill is not in the skills list of your courses.")


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
    scope = library_scope(current_user)
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
    return [{**r._mapping, "can_edit": can_change_resource(scope, current_user, r)} for r in rows]


@router.post("/resources", status_code=201)
def create_resource(req: ResourceCreate, request: Request,
                    current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a learning resource for a skill (source = 'admin'; the seed file never changes it)"""
    scope = library_scope(current_user)
    title = req.resource_title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required.")
    check_skill_exists(db, req.skill_id)
    check_skill_visible(db, scope, req.skill_id)
    check_resource_unique(db, req.skill_id, title)
    data = req.model_dump()
    data.update(resource_title=title, skill_id=str(req.skill_id),
                provider=(req.provider or "").strip() or None,
                url=(req.url or "").strip() or None,
                cost=(req.cost or "").strip() or "Free",
                created_by=str(current_user.user_id))
    row = db.execute(
        text("""
            INSERT INTO recommendations_library
                (skill_id, resource_title, resource_type, provider, url, duration_hours,
                 cost, difficulty, description, source, created_by)
            VALUES (:skill_id, :resource_title, :resource_type, :provider, :url, :duration_hours,
                    :cost, :difficulty, :description, 'admin', :created_by)
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
    """Activate / deactivate any resource; edit the details of resources added on the website.
    Inactive resources are no longer recommended (recommendation/engine.py filters on is_active)."""
    scope = library_scope(current_user)
    res = get_resource_row(db, resource_id)
    if not can_change_resource(scope, current_user, res):
        raise HTTPException(status_code=403, detail=NOT_YOURS)
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
        check_skill_visible(db, scope, changes["skill_id"])
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
