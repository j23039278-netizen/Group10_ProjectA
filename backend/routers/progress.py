"""
SEAGAS -- Development Progress Router
Handles student resource tracking (FR-11)
Start, complete, and track recommended learning activities
Author: Soh Way Miin (Carl) -- Backend Developer
"""
 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
 
from database import get_db
from routers.auth import get_current_user
 
router = APIRouter()
 
 
# ── Pydantic Schemas ──────────────────────────────────────────
class ProgressUpdate(BaseModel):
    status: str                        # 'in_progress' | 'completed'
    skill_added: Optional[bool] = False
 
 
# ── Helper: get student profile_id ───────────────────────────
def get_profile(current_user, db):
    profile = db.execute(
        text("SELECT profile_id FROM student_profiles WHERE user_id = :uid"),
        {"uid": str(current_user.user_id)}
    ).fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail="Create your student profile first")
    return str(profile.profile_id)
 
 
# ══════════════════════════════════════════════════════════════
# POST /api/progress/{resource_id}/start
# Student clicks "Start" on a recommendation resource
# ══════════════════════════════════════════════════════════════
@router.post("/{resource_id}/start", status_code=201)
def start_resource(
    resource_id: str,
    assessment_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a recommended resource as 'in_progress'.
    Creates a new progress record or updates existing one.
    """
    profile_id = get_profile(current_user, db)
 
    # Get skill_id from this resource
    resource = db.execute(
        text("SELECT resource_id, skill_id FROM recommendations_library WHERE resource_id = :rid"),
        {"rid": resource_id}
    ).fetchone()
 
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
 
    # Upsert: create or update to in_progress
    db.execute(
        text("""
            INSERT INTO student_resource_progress
                (profile_id, resource_id, assessment_id, skill_id, status, started_at)
            VALUES
                (:pid, :rid, :aid, :sid, 'in_progress', NOW())
            ON CONFLICT (profile_id, resource_id)
            DO UPDATE SET
                status     = 'in_progress',
                started_at = COALESCE(student_resource_progress.started_at, NOW()),
                updated_at = NOW()
        """),
        {
            "pid": profile_id,
            "rid": resource_id,
            "aid": assessment_id,
            "sid": str(resource.skill_id) if resource.skill_id else None
        }
    )
    db.commit()
 
    return {
        "message": "Resource marked as in progress",
        "resource_id": resource_id,
        "status": "in_progress"
    }
 
 
# ══════════════════════════════════════════════════════════════
# POST /api/progress/{resource_id}/complete
# Student clicks "Mark Complete" on a resource
# ══════════════════════════════════════════════════════════════
@router.post("/{resource_id}/complete")
def complete_resource(
    resource_id: str,
    req: ProgressUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a resource as completed and optionally record that
    the student has added the skill to their profile.
    Returns prompt for the frontend to ask about skill/cert update.
    """
    profile_id = get_profile(current_user, db)
 
    # Get resource + skill info
    resource = db.execute(
        text("""
            SELECT rl.resource_id, rl.skill_id, rl.resource_title,
                   rl.resource_type, sl.skill_name
            FROM recommendations_library rl
            LEFT JOIN skills_library sl ON sl.skill_id = rl.skill_id
            WHERE rl.resource_id = :rid
        """),
        {"rid": resource_id}
    ).fetchone()
 
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
 
    # Update to completed
    result = db.execute(
        text("""
            UPDATE student_resource_progress
            SET status       = 'completed',
                completed_at = NOW(),
                skill_added  = :skill_added,
                updated_at   = NOW()
            WHERE profile_id = :pid
            AND   resource_id = :rid
            RETURNING progress_id
        """),
        {
            "pid": profile_id,
            "rid": resource_id,
            "skill_added": req.skill_added
        }
    ).fetchone()
 
    # If no record exists yet (student skipped Start), create one
    if not result:
        db.execute(
            text("""
                INSERT INTO student_resource_progress
                    (profile_id, resource_id, skill_id, status,
                     started_at, completed_at, skill_added)
                VALUES
                    (:pid, :rid, :sid, 'completed',
                     NOW(), NOW(), :skill_added)
            """),
            {
                "pid": profile_id,
                "rid": resource_id,
                "sid": str(resource.skill_id) if resource.skill_id else None,
                "skill_added": req.skill_added
            }
        )
    db.commit()
 
    # Build prompt for frontend dialog
    resource_type = resource.resource_type or "activity"
    skill_name    = resource.skill_name or "this skill"
 
    if resource_type == "certification":
        prompt_type = "certification"
        prompt_msg  = f"Would you like to add the '{skill_name}' certification to your profile?"
    elif resource_type == "project":
        prompt_type = "project"
        prompt_msg  = f"Would you like to add this project and '{skill_name}' to your profile?"
    else:
        prompt_type = "skill"
        prompt_msg  = f"Would you like to add '{skill_name}' to your skill profile?"
 
    return {
        "message": "Resource marked as completed",
        "resource_id": resource_id,
        "resource_title": resource.resource_title,
        "status": "completed",
        "prompt": {
            "type": prompt_type,
            "message": prompt_msg,
            "skill_name": skill_name,
            "skill_id": str(resource.skill_id) if resource.skill_id else None
        }
    }
 
 
# ══════════════════════════════════════════════════════════════
# PATCH /api/progress/{resource_id}/skill-added
# Called after student confirms they added skill to profile
# ══════════════════════════════════════════════════════════════
@router.patch("/{resource_id}/skill-added")
def mark_skill_added(
    resource_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update skill_added = TRUE after student confirms
    they have added the skill/cert to their profile.
    """
    profile_id = get_profile(current_user, db)
 
    db.execute(
        text("""
            UPDATE student_resource_progress
            SET skill_added = TRUE,
                updated_at  = NOW()
            WHERE profile_id  = :pid
            AND   resource_id = :rid
        """),
        {"pid": profile_id, "rid": resource_id}
    )
    db.commit()
 
    return {
        "message": "Skill added status updated",
        "resource_id": resource_id,
        "skill_added": True
    }
 
 
# ══════════════════════════════════════════════════════════════
# GET /api/progress/my
# Get all progress records for this student
# ══════════════════════════════════════════════════════════════
@router.get("/my")
def get_my_progress(
    status: Optional[str] = None,   # filter by status
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all resource progress for the current student.
    Optional filter: ?status=in_progress | completed
    """
    profile_id = get_profile(current_user, db)
 
    query = """
        SELECT
            srp.progress_id,
            srp.resource_id,
            srp.status,
            srp.started_at,
            srp.completed_at,
            srp.skill_added,
            rl.resource_title,
            rl.resource_type,
            rl.provider,
            rl.url,
            rl.difficulty,
            sl.skill_name,
            sl.category
        FROM student_resource_progress srp
        JOIN recommendations_library rl ON rl.resource_id = srp.resource_id
        LEFT JOIN skills_library sl ON sl.skill_id = srp.skill_id
        WHERE srp.profile_id = :pid
    """
    params = {"pid": profile_id}
 
    if status:
        query += " AND srp.status = :status"
        params["status"] = status
 
    query += " ORDER BY srp.updated_at DESC"
 
    records = db.execute(text(query), params).fetchall()
 
    return {
        "total": len(records),
        "progress": [dict(r._mapping) for r in records]
    }
 
 
# ══════════════════════════════════════════════════════════════
# GET /api/progress/my/summary
# Summary counts for student dashboard
# ══════════════════════════════════════════════════════════════
@router.get("/my/summary")
def get_progress_summary(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return summary counts for the student dashboard:
    - in_progress count
    - completed count
    - skill_added count (completed + confirmed skill added)
    """
    profile_id = get_profile(current_user, db)
 
    summary = db.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'in_progress')  AS in_progress,
                COUNT(*) FILTER (WHERE status = 'completed')    AS completed,
                COUNT(*) FILTER (WHERE skill_added = TRUE)      AS skills_added
            FROM student_resource_progress
            WHERE profile_id = :pid
        """),
        {"pid": profile_id}
    ).fetchone()
 
    return {
        "in_progress":  summary.in_progress,
        "completed":    summary.completed,
        "skills_added": summary.skills_added
    }
 
 
# ══════════════════════════════════════════════════════════════
# GET /api/progress/assessment/{assessment_id}
# Get progress for all resources in a specific assessment
# Used by Recommendations page to show current status
# ══════════════════════════════════════════════════════════════
@router.get("/assessment/{assessment_id}")
def get_assessment_progress(
    assessment_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get progress status for all resources linked to a specific assessment.
    Frontend uses this to show Start/In Progress/Completed buttons.
    """
    profile_id = get_profile(current_user, db)
 
    records = db.execute(
        text("""
            SELECT
                srp.resource_id,
                srp.status,
                srp.started_at,
                srp.completed_at,
                srp.skill_added
            FROM student_resource_progress srp
            WHERE srp.profile_id    = :pid
            AND   srp.assessment_id = :aid
        """),
        {"pid": profile_id, "aid": assessment_id}
    ).fetchall()
 
    # Return as dict keyed by resource_id for easy frontend lookup
    progress_map = {
        str(r.resource_id): {
            "status":       r.status,
            "started_at":   str(r.started_at) if r.started_at else None,
            "completed_at": str(r.completed_at) if r.completed_at else None,
            "skill_added":  r.skill_added
        }
        for r in records
    }
 
    return {
        "assessment_id": assessment_id,
        "progress":      progress_map
    }