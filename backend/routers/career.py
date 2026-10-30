"""
SEAGAS — Career paths (FR-15): which job roles fit the student's current skills

GET /api/students/career-paths

Every active job role offered to the student's course is compared with the skills
on the student's profile. The match uses the weights of the recommendation
engine's career-path function (recommendation/engine.py
get_career_path_recommendations): required 1.0, preferred 0.6, bonus 0.3, on
skill presence. For each role the student sees what they already have, what is
missing, and a free learning resource for the most important missing skills.
This is a quick guide; a full assessment (Job Analysis) also uses the NLP matcher,
proficiency levels, projects and experience.
"""

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_user

router = APIRouter()

WEIGHTS = {"required": 1.0, "preferred": 0.6, "bonus": 0.3}   # recommendation/engine.py
NEXT_STEPS = 3                                                  # missing skills with a suggested resource


@router.get("")
def get_career_paths(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Career paths are for students.")
    # repo root is on sys.path once nlp_service is loaded (same as routers/assessments.py)
    from recommendation.engine import COST_TIER_ORDER, cost_tier
    profile = db.execute(text("SELECT profile_id, target_role FROM student_profiles WHERE user_id = :uid"),
                         {"uid": str(current_user.user_id)}).fetchone()
    have = set()
    if profile:
        have = {str(r[0]) for r in db.execute(text("SELECT skill_id FROM student_skills WHERE profile_id = :p"),
                                              {"p": str(profile.profile_id)}).fetchall()}

    rows = db.execute(text("""
        SELECT jr.role_id, jr.role_name, jr.description, jr.industry_level,
               sl.skill_id, sl.skill_name, sl.category, jrs.importance
        FROM job_roles jr
        JOIN job_role_skills jrs ON jrs.role_id = jr.role_id
        JOIN skills_library sl   ON sl.skill_id = jrs.skill_id
        WHERE jr.is_active AND CAST(:course AS VARCHAR) = ANY(jr.courses)
        ORDER BY jr.role_name, CASE jrs.importance WHEN 'required' THEN 1 WHEN 'preferred' THEN 2 ELSE 3 END, sl.skill_name
    """), {"course": current_user.course}).fetchall()

    # Latest readiness score per assessed role
    latest = {}
    if profile:
        for r in db.execute(text("""
            SELECT DISTINCT ON (role_id) role_id, readiness_score, created_at FROM assessments
            WHERE profile_id = :p AND role_id IS NOT NULL ORDER BY role_id, created_at DESC
        """), {"p": str(profile.profile_id)}).fetchall():
            latest[str(r.role_id)] = {"score": float(r.readiness_score), "date": r.created_at}

    roles = defaultdict(lambda: {"skills": []})
    for r in rows:
        role = roles[str(r.role_id)]
        role.update(role_id=str(r.role_id), role_name=r.role_name, description=r.description, industry_level=r.industry_level)
        role["skills"].append({"skill_id": str(r.skill_id), "skill_name": r.skill_name, "category": r.category,
                               "importance": r.importance, "have": str(r.skill_id) in have})

    # One resource per missing skill, free ones first, then easier ones
    missing_ids = {s["skill_id"] for role in roles.values() for s in role["skills"] if not s["have"]}
    resources = {}
    if missing_ids:
        for r in db.execute(text("""
            SELECT skill_id, resource_title, provider, url, cost, difficulty, duration_hours
            FROM recommendations_library WHERE is_active AND skill_id = ANY(CAST(:ids AS uuid[]))
        """), {"ids": list(missing_ids)}).fetchall():
            key = (COST_TIER_ORDER[cost_tier(r.cost)], {"beginner": 1, "intermediate": 2, "advanced": 3}.get(r.difficulty, 2))
            best = resources.get(str(r.skill_id))
            if best is None or key < best[0]:
                resources[str(r.skill_id)] = (key, {"title": r.resource_title, "provider": r.provider, "url": r.url,
                                                    "cost": r.cost, "duration_hours": r.duration_hours})

    paths = []
    for role in roles.values():
        skills = role.pop("skills")
        total = sum(WEIGHTS.get(s["importance"], 0.5) for s in skills)
        got = sum(WEIGHTS.get(s["importance"], 0.5) for s in skills if s["have"])
        count = lambda imp, owned=None: sum(1 for s in skills if s["importance"] == imp and (owned is None or s["have"] == owned))
        missing = [s for s in skills if not s["have"]]
        paths.append({
            **role,
            "match_pct": round(got / total * 100, 1) if total else 0,
            "required": {"have": count("required", True), "total": count("required")},
            "preferred": {"have": count("preferred", True), "total": count("preferred")},
            "bonus": {"have": count("bonus", True), "total": count("bonus")},
            "matched_skills": [s["skill_name"] for s in skills if s["have"]],
            "missing_skills": [{"skill_name": s["skill_name"], "importance": s["importance"]} for s in missing],
            "next_steps": [{"skill_name": s["skill_name"], "importance": s["importance"],
                            "resource": resources.get(s["skill_id"], (None, None))[1]}
                           for s in missing if s["importance"] == "required"][:NEXT_STEPS],
            "is_target_role": bool(profile and profile.target_role == role["role_name"]),
            "latest_assessment": latest.get(role["role_id"]),
        })
    paths.sort(key=lambda p: (-p["match_pct"], p["role_name"]))
    return {"skill_count": len(have), "paths": paths}
