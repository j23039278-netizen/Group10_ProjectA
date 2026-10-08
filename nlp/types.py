"""
Data types shared by the SEAGAS NLP module and the backend.

Field names follow the database columns they are stored in
(jd_extracted_skills, student_skills, job_role_skills, skill_match_results),
so the backend can map them one to one. See docs/NLP_INTERFACE.md.

Import as `from nlp.types import ...`. Never put the nlp/ folder itself on
sys.path: this module would then shadow Python's standard `types` module.
"""

from typing import Literal, TypedDict

# ── Allowed values ────────────────────────────────────────────
# Mirrors the CHECK constraints in database/schema.sql.
MatchingMethod = Literal["keyword", "semantic", "hybrid"]   # assessments / skill_match_results
ExtractionMethod = Literal["keyword", "semantic"]           # jd_extracted_skills (per skill)
ProficiencyLevel = Literal["beginner", "intermediate", "advanced"]
Importance = Literal["required", "preferred", "bonus"]
MatchStatus = Literal["strong", "developing", "gap"]

VALID_METHODS = ("keyword", "semantic", "hybrid")


# ── Skill catalogue ───────────────────────────────────────────
class SkillEntry(TypedDict):
    """One skill in the catalogue (skills_library row + taxonomy metadata)."""
    skill_id: str | None            # skills_library.skill_id (UUID); None for the JSON taxonomy
    skill_name: str                 # canonical name, e.g. "Power BI"
    category: str                   # Technical | AI_Digital | Analytical | Soft
    subcategory: str                # e.g. "Programming Language"; "" when unknown
    aliases: list[str]              # safe aliases, e.g. ["PowerBI", "Microsoft Power BI"]
    ambiguous_aliases: list[str]    # aliases that need context, e.g. ["Go"]
    description: str


# ── extract_skills() output ───────────────────────────────────
class ExtractedSkill(TypedDict):
    """A skill found in a job description (one row of jd_extracted_skills)."""
    skill_id: str | None            # skills_library UUID when the catalogue has one, else None
    skill_name: str                 # canonical name from the catalogue
    raw_skill_text: str             # exact span of the JD text, == text[start_char:end_char]
    method: ExtractionMethod        # which extractor found it -> extraction_method
    confidence_score: float         # 0.0 – 1.0
    start_char: int                 # offset of the span in the input text (inclusive)
    end_char: int                   # offset of the span in the input text (exclusive)


# ── match_skills() input ──────────────────────────────────────
class StudentSkill(TypedDict):
    """A skill the student claims (student_skills JOIN skills_library)."""
    skill_id: str | None
    skill_name: str
    proficiency_level: ProficiencyLevel
    evidence_type: list[str]        # e.g. ["project", "certification", "coursework", "internship"]


class RequiredSkill(TypedDict):
    """A skill the job asks for (from jd_extracted_skills or job_role_skills)."""
    skill_id: str | None
    skill_name: str                 # canonical name (not the raw JD text)
    importance: Importance


# ── match_skills() output ─────────────────────────────────────
class MatchResult(TypedDict):
    """Match decision for one required skill (one row of skill_match_results)."""
    skill_id: str | None
    skill_name: str
    importance: Importance
    match_status: MatchStatus
    similarity_score: float         # 0.0 – 1.0 (1.0 exact/alias match, 0.0 nothing found)
    matching_method: MatchingMethod # method that decided this row (see docs)
    matched_student_skill: str | None  # student skill_name that triggered the match, None for a gap
    reason: str                     # one short English sentence shown to the student
