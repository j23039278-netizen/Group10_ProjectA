"""
SEAGAS - Detail for each recommended skill (lecturer feedback F05, Sprint 3 review)

Adds two things to every skill of GET /api/assessments/{id}/recommendations:

why    Why the skill matters for this role: in how many of the role's real job
       descriptions it appears (data/jd_dataset/jd_skill_evidence.csv, the same
       file as JD fit), with one short quote from such a job description. For an
       assessment against a pasted job description: that this description asks for it.
level  Where the student is now and what counts as Strong, with the next step.
       Strong follows rule C (docs/NLP_CLASSIFICATION_RULES.md): Intermediate or
       Advanced, or Beginner backed by a project, certification or internship.
       "Now" is the student's current profile, so it can be ahead of the stored
       assessment (met_now: run the assessment again).

Read only: it never changes a score or the order of the recommendations.
"""

import csv
import re
from functools import lru_cache

from sqlalchemy import text

import assessment_service
import jd_fit

TARGET_TEXT = "Intermediate, or Beginner backed by a project, certification or internship"
_MARK = re.compile(r"<<(.+?)>>")


@lru_cache(maxsize=None)
def load_examples(path=jd_fit.EVIDENCE_CSV):
    """{(role_code, skill_name): (jd_ref, quote)}: the first quote of each skill per role.
    The skill's words in the quote are wrapped in << >> (as in the CSV)."""
    out = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["role_code"], row["skill_name"])
            if row["skill_name"] and key not in out and _MARK.search(row.get("context") or ""):
                out[key] = (row["jd_ref"], " ".join(row["context"].split()))
    return out


def jd_share(role_code, skill_name):
    """(jds that ask for the skill, jds of the role) from the JD dataset; (0, 0) if none."""
    jds = [s for s in jd_fit.load_jd_skill_sets().get(role_code, ()) if s]
    return sum(skill_name in s for s in jds), len(jds)


def why_for_role(role_code, role_name, skill_name, importance):
    asked, total = jd_share(role_code, skill_name)
    if not total:
        return None
    pct = round(asked * 100 / total)
    if asked:
        sentence = (f"Asked for in {asked} of the {total} real {role_name} job descriptions we analysed "
                    f"({pct}%).")
    else:
        sentence = (f"Not named in the {total} {role_name} job descriptions we analysed, but part of the "
                    f"{importance} skills of the role template.")
    example = load_examples().get((role_code, skill_name))
    return {"source": "role", "role_name": role_name, "jd_count": asked, "jd_total": total,
            "jd_percent": pct, "text": sentence,
            "example": {"jd_ref": example[0], "quote": example[1]} if example else None}


def why_for_jd(jd_title, importance):
    kind = {"required": "a required", "preferred": "a preferred", "bonus": "a bonus"}.get(importance, "a")
    return {"source": "jd", "jd_title": jd_title, "jd_count": None, "jd_total": None, "jd_percent": None,
            "text": f"The job description \"{jd_title}\" lists this as {kind} skill.", "example": None}


def level_detail(skill_name, gap_type, matched, mine):
    """matched: the student skill the matcher used (None for a gap); mine: the student's
    current skills by name (with evidence derived from projects and certifications)."""
    same = mine.get(skill_name)
    if same:
        level = same.get("proficiency_level") or "beginner"
        evidence = sorted(set(same.get("evidence_type") or ()))
        met = jd_fit.skill_credit(same) == 1.0
        if met:
            step = ("Your profile now meets this level. Run the assessment again to update your score.")
        else:
            step = (f"Do a project, certification or internship that uses {skill_name}, or an "
                    f"intermediate activity, and raise the skill to Intermediate when you finish.")
        return {"current": level, "current_evidence": evidence, "current_text": _level_text(level, evidence),
                "related_skill": None, "target": "intermediate", "target_text": TARGET_TEXT,
                "met_now": met, "next_step": step}
    if gap_type == "developing" and matched and matched != skill_name:
        rel = mine.get(matched) or {}
        level = rel.get("proficiency_level")
        return {"current": None, "current_evidence": [],
                "current_text": f"Not on your profile; you have the related skill {matched}"
                                + (f" ({level.capitalize()})" if level else "") + ".",
                "related_skill": matched, "target": "intermediate", "target_text": TARGET_TEXT,
                "met_now": False,
                "next_step": (f"{matched} is close, but the role asks for {skill_name} itself. Learn it, "
                              f"then add {skill_name} to My Skills with a project or certification behind it.")}
    return {"current": None, "current_evidence": [], "current_text": "Not on your profile yet.",
            "related_skill": None, "target": "intermediate", "target_text": TARGET_TEXT, "met_now": False,
            "next_step": (f"Start with a beginner activity to learn {skill_name}, then a project or "
                          f"intermediate activity to reach Strong.")}


def _level_text(level, evidence):
    strong = [e for e in evidence if e in ("project", "certification", "internship")]
    if strong:
        return f"{level.capitalize()}, with {' and '.join(strong)} evidence."
    if "coursework" in evidence:
        return f"{level.capitalize()}, with coursework only."
    return f"{level.capitalize()}, no project, certification or internship behind it."


def add_details(db, assessment, recommendations):
    """Adds why and level to each recommendation in place and returns the list."""
    if not recommendations:
        return recommendations
    matched = {r["skill_id"]: r.get("matched_student_skill")
               for r in assessment_service.load_match_rows(db, str(assessment.assessment_id))}
    mine = {}
    for s in assessment_service.load_student_skills(db, assessment.profile_id):
        mine[s["skill_name"]] = s
    if assessment.jd_id:
        title = db.execute(text("SELECT title FROM job_descriptions WHERE jd_id = :j"),
                           {"j": str(assessment.jd_id)}).scalar() or "this job"
        why = lambda rec: why_for_jd(title, rec.get("importance"))
    else:
        role = db.execute(text("SELECT role_code, role_name FROM job_roles WHERE role_id = :r"),
                          {"r": str(assessment.role_id)}).fetchone()
        why = (lambda rec: why_for_role(role.role_code, role.role_name, rec["skill_name"], rec.get("importance"))) \
            if role else (lambda rec: None)
    for rec in recommendations:
        rec["why"] = why(rec)
        rec["level"] = level_detail(rec["skill_name"], rec["gap_type"], matched.get(rec["skill_id"]), mine)
    return recommendations
