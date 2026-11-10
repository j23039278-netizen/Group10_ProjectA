"""
SEAGAS — Run one assessment (skill matching + readiness score) and store it

Used by POST /api/assessments/run and by data/run_assessments.py (batch
assessments for the synthetic students), so both compute scores the same way.

Readiness is tiered coverage, required 70 / preferred 25 / bonus 5 (readiness.py).
The skill dimensions use points instead: required=3, preferred=2, bonus=1, with
Strong = full points, Developing = half, Gap = 0.
Strong / Developing / Gap comes from the NLP matcher (Ng Yong Hin, nlp/);
rules in docs/NLP_CLASSIFICATION_RULES.md.
"""

from sqlalchemy import text

import nlp_service
from nlp import derive_evidence  # importable once nlp_service has put the repo root on the path
from readiness import STATUS_CREDIT, tier_coverage, tiered_readiness

IMPORTANCE_WEIGHTS = {"required": 3, "preferred": 2, "bonus": 1}   # dimension scores only


class AssessmentError(Exception):
    """A request that cannot be assessed; status is the HTTP status to return"""

    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def load_student_skills(db, profile_id):
    """The student's current skills as dicts, with evidence from their projects and
    certifications added (nlp/evidence.py): the website does not ask for evidence_type
    when a skill is added. Stored evidence_type is kept and never overwritten."""
    student_skills = db.execute(
        text("""
            SELECT sl.skill_id, sl.skill_name, sl.category,
                   ss.proficiency_level, ss.evidence_type
            FROM student_skills ss
            JOIN skills_library sl ON sl.skill_id = ss.skill_id
            WHERE ss.profile_id = :pid
        """),
        {"pid": str(profile_id)}
    ).fetchall()
    students = [{"skill_id": str(sk.skill_id), "skill_name": sk.skill_name,
                 "proficiency_level": sk.proficiency_level,
                 "evidence_type": list(sk.evidence_type or [])} for sk in student_skills]
    records = db.execute(
        text("""
            SELECT 'project' AS kind, p.project_title, p.description, p.technologies,
                   p.project_type, NULL::varchar AS cert_name, NULL::varchar AS issuer,
                   (SELECT COUNT(*) FROM student_evidence_files f
                     WHERE f.project_id = p.project_id) AS proof_count
            FROM student_projects p WHERE p.profile_id = :pid
            UNION ALL
            SELECT 'certification', NULL, NULL, NULL, NULL, c.cert_name, c.issuer,
                   (SELECT COUNT(*) FROM student_evidence_files f WHERE f.cert_id = c.cert_id)
            FROM student_certifications c WHERE c.profile_id = :pid
        """),
        {"pid": str(profile_id)}
    ).fetchall()
    return derive_evidence(students,
                           [r for r in records if r.kind == "project"],
                           [r for r in records if r.kind == "certification"])


def load_match_rows(db, assessment_id):
    """The stored match rows of an assessment as dicts, strong first, then by skill name.
    The one place that reads importance: rows stored before the column existed fall back to
    the role template, then to required (a pasted JD counts every skill as required)."""
    rows = db.execute(
        text("""
            SELECT smr.skill_id, sl.skill_name, sl.category,
                   smr.match_status, smr.similarity_score, smr.matching_method,
                   smr.matched_student_skill, smr.reason,
                   COALESCE(smr.importance, jrs.importance, 'required') AS importance
            FROM skill_match_results smr
            JOIN assessments a     ON a.assessment_id = smr.assessment_id
            JOIN skills_library sl ON sl.skill_id = smr.skill_id
            LEFT JOIN job_role_skills jrs ON jrs.role_id = a.role_id AND jrs.skill_id = smr.skill_id
            WHERE smr.assessment_id = :aid
            ORDER BY
                CASE smr.match_status
                    WHEN 'strong'     THEN 1
                    WHEN 'developing' THEN 2
                    WHEN 'gap'        THEN 3
                END,
                sl.skill_name
        """),
        {"aid": str(assessment_id)}
    ).fetchall()
    return [{**r._mapping, "skill_id": str(r.skill_id)} for r in rows]


def run_for_profile(db, profile, *, role_id=None, jd_id=None,
                    method=nlp_service.DEFAULT_METHOD, commit=True):
    """Assess one student profile against a role template or an analysed JD.

    profile: a student_profiles row. Access checks are the caller's job.
    commit=False leaves the transaction open (the batch script commits in groups).
    Returns the same dict as POST /api/assessments/run.
    """
    try:
        nlp_service.check_method(method)
    except ValueError as e:
        raise AssessmentError(400, str(e))
    if not jd_id and not role_id:
        raise AssessmentError(400, "Provide either a jd_id or a role_id")

    students = load_student_skills(db, profile.profile_id)
    if not students:
        raise AssessmentError(400, "Add at least one skill to your profile before running assessment")

    # Required skills — from an analysed JD or a role template
    if jd_id:
        required_skills = db.execute(
            text("""
                SELECT jes.skill_id,
                       COALESCE(sl.skill_name, jes.raw_skill_text) AS skill_name,
                       sl.category, jes.importance
                FROM jd_extracted_skills jes
                LEFT JOIN skills_library sl ON sl.skill_id = jes.skill_id
                WHERE jes.jd_id = :jid
            """),
            {"jid": str(jd_id)}
        ).fetchall()
    else:
        required_skills = db.execute(
            text("""
                SELECT sl.skill_id, sl.skill_name, sl.category, jrs.importance
                FROM job_role_skills jrs
                JOIN skills_library sl ON sl.skill_id = jrs.skill_id
                WHERE jrs.role_id = :rid
                ORDER BY
                    CASE jrs.importance
                        WHEN 'required'  THEN 1
                        WHEN 'preferred' THEN 2
                        WHEN 'bonus'     THEN 3
                    END
            """),
            {"rid": str(role_id)}
        ).fetchall()
    if not required_skills:
        raise AssessmentError(
            400,
            "No skills were found in this job description. Run the analysis first, "
            "or paste a longer description." if jd_id else "No required skills found for this role")

    # ── Matching (nlp/) ───────────────────────────────────────
    required = [{"skill_id": str(r.skill_id) if r.skill_id else None,
                 "skill_name": r.skill_name,
                 "importance": r.importance or "required"} for r in required_skills]
    try:
        match_results, method_used, matching_note = nlp_service.match_skills(students, required, method)
    except ValueError as e:
        raise AssessmentError(400, str(e))

    def weighted(rows):
        top = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) for m in rows)
        got = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) * STATUS_CREDIT[m["match_status"]] for m in rows)
        return got, top

    readiness_score = tiered_readiness(match_results)

    # 7 dimensions. match_results are in the same order as required_skills.
    def category_score(category):
        rows = [m for r, m in zip(required_skills, match_results) if r.category == category]
        if not rows:
            return None
        got, top = weighted(rows)
        return round(got / top * 100, 2) if top > 0 else 0

    # Experience dimensions from the student's records. Industry experience counts
    # internship projects and work experience other than volunteering; internship_count
    # is also a profile field (synthetic data sets it directly), so the larger value is used.
    exp = db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM student_projects WHERE profile_id = :pid)       AS projects,
                (SELECT COUNT(*) FROM student_projects
                  WHERE profile_id = :pid AND project_type = 'internship')            AS internship_projects,
                (SELECT COUNT(*) FROM student_experiences
                  WHERE profile_id = :pid AND experience_type <> 'volunteer')         AS work_experiences,
                (SELECT COUNT(*) FROM student_certifications WHERE profile_id = :pid) AS certifications
        """),
        {"pid": str(profile.profile_id)}
    ).fetchone()
    internships = max(profile.internship_count or 0, exp.internship_projects + exp.work_experiences)
    dims = {
        "technical_skills":    category_score("Technical"),
        "ai_digital_skills":   category_score("AI_Digital"),
        "analytical_skills":   category_score("Analytical"),
        "communication":       category_score("Soft"),
        "industry_experience": min(internships * 50, 100),
        "project_experience":  min(exp.projects * 25, 100),
        "certification":       min(exp.certifications * 33, 100),
    }

    # ── Store ─────────────────────────────────────────────────
    assessment_id = str(db.execute(
        text("""
            INSERT INTO assessments (
                profile_id, jd_id, role_id, matching_method, readiness_score,
                score_technical, score_ai_digital, score_analytical, score_communication,
                score_industry_exp, score_project_exp, score_certification
            ) VALUES (
                :pid, :jid, :rid, :method, :score,
                :tech, :ai, :analytical, :comm, :ind, :proj, :cert
            ) RETURNING assessment_id
        """),
        {"pid": str(profile.profile_id), "jid": str(jd_id) if jd_id else None,
         "rid": str(role_id) if role_id else None, "method": method_used,
         "score": readiness_score,
         "tech": dims["technical_skills"], "ai": dims["ai_digital_skills"],
         "analytical": dims["analytical_skills"], "comm": dims["communication"],
         "ind": dims["industry_experience"], "proj": dims["project_experience"],
         "cert": dims["certification"]}
    ).fetchone().assessment_id)

    rows = [{"aid": assessment_id, "sid": m["skill_id"], "status": m["match_status"],
             "score": m["similarity_score"], "method": m["matching_method"],
             "matched": m["matched_student_skill"], "reason": m["reason"],
             "importance": m["importance"]}
            for m in match_results if m["skill_id"]]
    if rows:
        db.execute(
            text("""
                INSERT INTO skill_match_results
                    (assessment_id, skill_id, match_status, similarity_score,
                     matching_method, matched_student_skill, reason, importance)
                VALUES (:aid, :sid, :status, :score, :method, :matched, :reason, :importance)
                ON CONFLICT (assessment_id, skill_id) DO NOTHING
            """),
            rows
        )
    if commit:
        db.commit()

    return {
        "assessment_id":   assessment_id,
        "readiness_score": readiness_score,
        "scoring_method":  "tiered coverage (required=70, preferred=25, bonus=5)",
        "matching_method": method_used,
        "matching_note":   matching_note,
        "dimension_scores": dims,
        "skill_summary": {
            "strong":     sum(m["match_status"] == "strong" for m in match_results),
            "developing": sum(m["match_status"] == "developing" for m in match_results),
            "gaps":       sum(m["match_status"] == "gap" for m in match_results),
            "total":      len(required_skills),
            "tier_coverage": tier_coverage(match_results),
        },
        "match_results": match_results,
    }
