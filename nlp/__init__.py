"""
SEAGAS NLP module — public interface.
Author: Ng Yong Hin (AI / NLP Engineer)

The backend should only use the names exported here:

    from nlp import extract_skills, match_skills

The contract (fields, DB mapping, errors, examples) is in docs/NLP_INTERFACE.md.
This version defines the interface only: input validation works, the
extraction / matching logic raises NotImplementedError until the
implementation branches are merged.
"""

from nlp.skills import SkillCatalogue, load_catalogue
from nlp.types import (
    VALID_METHODS,
    ExtractedSkill,
    MatchResult,
    RequiredSkill,
    SkillEntry,
    StudentSkill,
)

__all__ = [
    "extract_skills", "match_skills", "load_catalogue", "SkillCatalogue",
    "ExtractedSkill", "StudentSkill", "RequiredSkill", "MatchResult", "SkillEntry",
    "VALID_METHODS",
]


def _check_method(method):
    if method not in VALID_METHODS:
        raise ValueError(
            f"method must be one of {', '.join(VALID_METHODS)}; got {method!r}"
        )


def extract_skills(
    text: str,
    method: str = "hybrid",
    skills: list[dict] | None = None,
) -> list[ExtractedSkill]:
    """Extract skills from a job description.

    text:   raw JD text (job_descriptions.raw_text).
    method: "keyword", "semantic" or "hybrid" (both, merged).
    skills: skills_library rows (skill_id, skill_name, aliases, ...) so results
            carry real UUIDs; None uses nlp/resources/skills_taxonomy.json
            (skill_id is then None).

    Returns one ExtractedSkill per distinct skill, ordered by start_char.
    Blank text returns []. Raises ValueError for an unknown method or bad input.
    """
    _check_method(method)
    if not isinstance(text, str):
        raise ValueError(f"text must be a str; got {type(text).__name__}")
    load_catalogue(skills)  # validates the rows early
    if not text.strip():
        return []
    raise NotImplementedError(
        "nlp.extract_skills() is not implemented yet (interface only). "
        "Keyword/semantic extraction lands in a later nlp branch."
    )


def match_skills(
    student_skills: list[StudentSkill],
    required_skills: list[RequiredSkill],
    method: str = "hybrid",
) -> list[MatchResult]:
    """Match a student's skills against the skills a job requires.

    method: "keyword", "semantic" or "hybrid" (keyword first, semantic for the rest).

    Returns one MatchResult per item of required_skills, in the same order.
    No required skills returns []. Raises ValueError for an unknown method.
    """
    _check_method(method)
    if not required_skills:
        return []
    raise NotImplementedError(
        "nlp.match_skills() is not implemented yet (interface only). "
        "Keyword/semantic matching lands in a later nlp branch."
    )
