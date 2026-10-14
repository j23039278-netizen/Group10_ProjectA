"""
SEAGAS NLP module — public interface.
Author: Ng Yong Hin (AI / NLP Engineer)

The backend should only use the names exported here:

    from nlp import extract_skills, match_skills

The contract (fields, DB mapping, errors, examples) is in docs/NLP_INTERFACE.md.
Implemented so far: extract_skills(method="keyword") (Level 1) and
extract_skills(method="semantic") (Level 2), both in nlp/extractor.py.
Semantic extraction needs nlp/requirements.txt; keyword extraction needs only
the standard library. Hybrid extraction and match_skills() raise
NotImplementedError until their branches are merged.
"""

from nlp.extractor import extract_keyword, extract_semantic
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
    catalogue = load_catalogue(skills)  # validates the rows early
    if not text.strip():
        return []
    if method == "keyword":
        return extract_keyword(text, catalogue)
    if method == "semantic":
        return extract_semantic(text, catalogue)
    raise NotImplementedError(
        f"nlp.extract_skills(method={method!r}) is not implemented yet. "
        "Use method=\"keyword\" or \"semantic\" until hybrid extraction is merged."
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
