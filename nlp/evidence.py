"""
Skill evidence derived from a student's projects and certifications.
Author: Ng Yong Hin (AI / NLP Engineer)

Use it through `nlp.derive_evidence(student_skills, projects, certifications)`
before `nlp.match_skills()`. Rules and the trade-offs: docs/NLP_CLASSIFICATION_RULES.md,
section 4a.

The website has no evidence input when a student adds a skill, so for real
users student_skills.evidence_type is empty and a beginner skill can never be
Strong (rule C). Students do list projects and certifications; this module
reads them at assessment time and adds what they show:

  project        the project's technologies contain the skill (catalogue lookup,
                 so "Postgres" counts for PostgreSQL), or keyword extraction
                 finds it in project_title / description. A project of type
                 "internship" gives "internship" instead of "project".
  certification  keyword extraction finds the skill in cert_name. The issuer is
                 read only when the name gives no skill, because issuers are
                 organisations: "CNCF / Linux Foundation" is not Linux evidence
                 for a Kubernetes certification, but "Amazon Web Services" is
                 AWS evidence for a certification named "Cloud Practitioner".

  * Only skills the student lists get evidence; no skill is added.
  * Stored evidence_type is kept, first and in its order; derived types are
    appended. Nothing is written back to the database.
  * Free text (title, description, certification name / issuer) never gives a
    soft skill or a trait such as Problem Solving: "good communication and
    teamwork" in a description is a claim, not a demonstration. Such a skill
    listed in technologies counts.
  * IMPLIED_SKILLS: a cloud platform is also Cloud Computing evidence.
  * Keyword extraction only (no model), so it is fast and every piece of
    evidence can be traced to a word in the record.
  * require_proof (config.DERIVED_EVIDENCE_NEEDS_PROOF, default off): count only
    projects / certifications with at least one evidence file or link
    (proof_count > 0).

Each returned skill is a copy of the input with evidence_type extended and
evidence_sources = {"project": ["Sales Dashboard"], ...}: the title of every
project / certification behind each evidence type. match_skills() names them
in the reason.
"""

from functools import lru_cache

from nlp import config
from nlp.extractor import extract_keyword
from nlp.matcher import _evidence, _row
from nlp.normalise import skill_key
from nlp.skills import load_catalogue

# Derived types in the order they are appended to evidence_type.
DERIVED_TYPES = ("project", "certification", "internship")
# Skills that free text never evidences (see the module docstring): every soft
# skill, and the analytical skills that are personal traits ("Excel at problem
# solving" in a description says nothing a project showed).
FREE_TEXT_EXCLUDED_CATEGORIES = frozenset({"Soft"})
FREE_TEXT_EXCLUDED_SKILLS = frozenset({"Problem Solving", "Critical Thinking", "Decision Making",
                                       "Systems Thinking"})
# Evidence for a skill is also evidence for these (catalogue names).
IMPLIED_SKILLS = {
    "AWS": ("Cloud Computing",),
    "Azure": ("Cloud Computing",),
    "GCP": ("Cloud Computing",),
}


@lru_cache(maxsize=4096)
def _text_skills(text, catalogue):
    """Canonical names keyword extraction finds in `text`, soft skills and traits
    left out. Cached: the same project descriptions come back on every assessment."""
    if not text or not text.strip():
        return ()
    return tuple(s["skill_name"] for s in extract_keyword(text, catalogue)
                 if s["skill_name"] not in FREE_TEXT_EXCLUDED_SKILLS
                 and catalogue.get(s["skill_name"])["category"] not in FREE_TEXT_EXCLUDED_CATEGORIES)


def _listed_skills(items, catalogue):
    """Canonical names for a technologies list: each item by catalogue lookup
    (aliases resolved), else by keyword extraction ("Python 3.11 / Django"),
    else the item itself, so a skill outside the catalogue can still match."""
    names = []
    for item in _evidence(items):
        name = catalogue.lookup(item)
        if name:
            names.append(name)
        else:
            names.extend(s["skill_name"] for s in extract_keyword(item, catalogue) or [{"skill_name": item}])
    return names


def _with_implied(names):
    return {skill_key(n) for name in names for n in (name, *IMPLIED_SKILLS.get(name, ()))}


def _project(row, catalogue):
    """(evidence type, title, skill keys) for one student_projects row."""
    names = _listed_skills(row.get("technologies"), catalogue)
    names += _text_skills(row.get("project_title") or "", catalogue)
    names += _text_skills(row.get("description") or "", catalogue)
    kind = "internship" if row.get("project_type") == "internship" else "project"
    return kind, (row.get("project_title") or "").strip(), _with_implied(names)


def _certification(row, catalogue):
    """(evidence type, name, skill keys) for one student_certifications row."""
    name = (row.get("cert_name") or "").strip()
    names = _text_skills(name, catalogue) or _text_skills(row.get("issuer") or "", catalogue)
    return "certification", name, _with_implied(names)


def _has_proof(row):
    return int(row.get("proof_count") or 0) > 0


def derive_evidence(student_skills, projects=(), certifications=(), *,
                    require_proof=None, catalogue=None):
    """student_skills with evidence from the student's projects and certifications.

    student_skills: StudentSkill dicts (or SQLAlchemy rows), as for match_skills().
    projects:       student_projects rows: project_title, description,
                    technologies (list or PostgreSQL array literal), project_type.
    certifications: student_certifications rows: cert_name, issuer.
    Either may carry proof_count, the number of student_evidence_files rows
    (files or links) attached to it.
    require_proof:  only count items with proof_count > 0; None uses
                    config.DERIVED_EVIDENCE_NEEDS_PROOF.
    catalogue:      a SkillCatalogue; None uses the default taxonomy.

    Returns new dicts in the same order: evidence_type is a list with the
    stored types first, then any new derived type; evidence_sources maps each
    derived type to the titles that produced it (empty when none did).
    """
    catalogue = catalogue or load_catalogue()
    if require_proof is None:
        require_proof = config.DERIVED_EVIDENCE_NEEDS_PROOF
    records = []   # (evidence type, title, skill keys) per project / certification
    for rows, read, what in ((projects, _project, "project"),
                             (certifications, _certification, "certification")):
        for item in rows or ():
            row = _row(item, what)
            if not require_proof or _has_proof(row):
                records.append(read(row, catalogue))

    out = []
    for item in student_skills or ():
        skill = dict(_row(item, "student skill"))
        name = str(skill.get("skill_name") or "").strip()
        key = skill_key(catalogue.lookup(name) or name)
        sources = {}
        for kind, title, keys in records:
            if key and key in keys:
                titles = sources.setdefault(kind, [])
                if title and title not in titles:
                    titles.append(title)
        evidence = list(_evidence(skill.get("evidence_type")))
        evidence += [t for t in DERIVED_TYPES if t in sources and t not in evidence]
        skill["evidence_type"] = evidence
        skill["evidence_sources"] = {t: sources[t] for t in DERIVED_TYPES if t in sources}
        out.append(skill)
    return out
