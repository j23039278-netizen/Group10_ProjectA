"""
SEAGAS NLP module — public interface.
Author: Ng Yong Hin (AI / NLP Engineer)

The backend should only use the names exported here:

    from nlp import extract_skills, match_skills

The contract (fields, DB mapping, errors, examples) is in docs/NLP_INTERFACE.md;
the Strong / Developing / Gap rules are in docs/NLP_CLASSIFICATION_RULES.md.

  extract_skills(method="keyword")   Level 1, nlp/extractor.py (standard library only)
  extract_skills(method="semantic")  Level 2, nlp/extractor.py (nlp/requirements.txt)
  extract_skills(method="hybrid")    both, merged, nlp/extractor.py (nlp/requirements.txt)
  extract_skills(method="tfidf")     TF-IDF + cosine on the semantic candidates, for the
                                     method comparison only (spaCy + scikit-learn, no model)
  match_skills(...)                  nlp/matcher.py; method="keyword" needs only the
                                     standard library, "semantic" / "hybrid" load the
                                     model when a similarity is needed
  derive_evidence(...)               nlp/evidence.py; adds project / certification /
                                     internship evidence from the student's records
                                     to the student skills before match_skills()
                                     (keyword extraction, standard library only)
"""

from nlp.evidence import derive_evidence
from nlp.extractor import extract_hybrid, extract_keyword, extract_semantic, extract_tfidf
from nlp.matcher import match
from nlp.skills import SkillCatalogue, load_catalogue
from nlp.types import (
    EXTRACTION_METHODS,
    VALID_METHODS,
    ExtractedSkill,
    MatchResult,
    RequiredSkill,
    SkillEntry,
    StudentSkill,
)

__all__ = [
    "extract_skills", "match_skills", "derive_evidence", "load_catalogue", "SkillCatalogue",
    "ExtractedSkill", "StudentSkill", "RequiredSkill", "MatchResult", "SkillEntry",
    "VALID_METHODS", "EXTRACTION_METHODS",
]


def _check_method(method, allowed=VALID_METHODS):
    if method not in allowed:
        raise ValueError(
            f"method must be one of {', '.join(allowed)}; got {method!r}"
        )


def extract_skills(
    text: str,
    method: str = "hybrid",
    skills: list[dict] | None = None,
) -> list[ExtractedSkill]:
    """Extract skills from a job description.

    text:   raw JD text (job_descriptions.raw_text).
    method: "keyword", "semantic", "hybrid" (both, merged) or "tfidf"
            (TF-IDF + cosine; for the method comparison, not for the DB).
    skills: skills_library rows (skill_id, skill_name, aliases, ...) so results
            carry real UUIDs; None uses nlp/resources/skills_taxonomy.json
            (skill_id is then None).

    Returns one ExtractedSkill per distinct skill, ordered by start_char.
    Blank text returns []. Raises ValueError for an unknown method or bad input.
    """
    _check_method(method, EXTRACTION_METHODS)
    if not isinstance(text, str):
        raise ValueError(f"text must be a str; got {type(text).__name__}")
    catalogue = load_catalogue(skills)  # validates the rows early
    if not text.strip():
        return []
    if method == "keyword":
        return extract_keyword(text, catalogue)
    if method == "semantic":
        return extract_semantic(text, catalogue)
    if method == "tfidf":
        return extract_tfidf(text, catalogue)
    return extract_hybrid(text, catalogue)


def match_skills(
    student_skills: list[StudentSkill],
    required_skills: list[RequiredSkill],
    method: str = "hybrid",
) -> list[MatchResult]:
    """Match a student's skills against the skills a job requires.

    method: "keyword", "semantic" or "hybrid" (keyword first, semantic for the rest).

    Returns one MatchResult per item of required_skills, in the same order.
    No required skills returns []; no student skills makes every required
    skill a gap. Raises ValueError for an unknown method or a malformed skill
    (missing skill_name, unknown proficiency_level or importance).
    "tfidf" is an extraction method only and raises ValueError here.
    """
    if method == "tfidf":
        raise ValueError(
            "method 'tfidf' is only for extract_skills(); match_skills() takes "
            f"{', '.join(VALID_METHODS)}"
        )
    _check_method(method)
    if not required_skills:
        return []
    return match(student_skills or [], required_skills, method, load_catalogue())
