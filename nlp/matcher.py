"""
Skill matching for the SEAGAS NLP module: Strong / Developing / Gap (S2-12-01).
Author: Ng Yong Hin (AI / NLP Engineer)

Use it through `nlp.match_skills(student_skills, required_skills, method)`.
Rules, reason templates and worked examples: docs/NLP_CLASSIFICATION_RULES.md.

For each required skill (results keep the order of required_skills):
  keyword   the student has the same skill: the same skill_id when both sides
            have one, otherwise the same canonical name (aliases and spelling
            variants resolved through the catalogue). No similarity search.
  semantic  cosine similarity between the required skill and every student
            skill (nlp/model.py embeddings of the canonical names, built with
            config.SKILL_TEXT_MODE); the most similar student skill decides.
  hybrid    keyword first; semantic only for required skills keyword could
            not match.

Classification (thresholds from nlp/config.py):
  strong      the same skill, intermediate / advanced, or beginner with
              project, certification or internship evidence
  developing  the same skill at beginner level with no evidence or coursework
              only (rule C); or a different skill with similarity >=
              RELATED_THRESHOLD, whatever its level (rule A)
  gap         anything else (similarity_score 0.0, matched_student_skill None)

The keyword method needs only the standard library; semantic and hybrid load
the model (nlp/requirements.txt) the first time a similarity is needed.
"""

import math
from collections.abc import Mapping
from typing import NamedTuple

from nlp import config
from nlp.normalise import skill_key
from nlp.types import MatchResult

PROFICIENCY_LEVELS = ("beginner", "intermediate", "advanced")
IMPORTANCE_LEVELS = ("required", "preferred", "bonus")
# Evidence that lets a beginner skill count as Strong; coursework alone does not (rule C).
STRONG_EVIDENCE = frozenset({"project", "certification", "internship"})
_STATUS_RANK = {"gap": 0, "developing": 1, "strong": 2}

# ── Reasons ───────────────────────────────────────────────────
# One template per case (docs/NLP_CLASSIFICATION_RULES.md, section 4).
# {skill}: the required skill; {student}: the student skill that decided;
# {detail}: its level and evidence, e.g. "advanced, with project evidence", and
# the projects / certifications behind derived evidence (nlp/evidence.py), at most
# MAX_TITLES of them: "beginner, with project evidence from Sales Dashboard".
MAX_TITLES = 2
REASONS = {
    "same_strong": "You list {student} ({detail}), which matches this skill, so this is marked Strong.",
    "same_developing": ("You list {student} ({detail}). A beginner skill needs project, certification "
                        "or internship evidence to count as Strong, so this is marked Developing."),
    "similar": ("You list {student} ({detail}), which is very close to {skill} but not the same "
                "skill, so this is marked Developing."),
    "related": ("You list {student} ({detail}). It is closely related to {skill} but not the same "
                "skill, so this is marked Developing."),
    "gap_keyword": "No skill in your profile is {skill} or another name for it, so this is marked as a Gap.",
    "gap_similar": "No skill in your profile is {skill} or close enough to it, so this is marked as a Gap.",
    "gap_empty": "Your profile lists no skills yet, so this is marked as a Gap.",
}


# ── Input ─────────────────────────────────────────────────────
class _Skill(NamedTuple):
    """A student or required skill, resolved against the catalogue."""
    index: int                 # position in the input list
    skill_id: str | None
    name: str                  # skill_name as given
    canonical: str             # catalogue name, or the given name when unknown
    key: str                   # skill_key(canonical): spelling variants compare equal
    level: str | None = None   # student skills only
    evidence: tuple = ()       # student skills only
    importance: str | None = None   # required skills only
    sources: tuple = ()        # student skills only: titles behind derived evidence (nlp/evidence.py)


def _row(item, what):
    if isinstance(item, Mapping):
        return item
    mapping = getattr(item, "_mapping", None)   # SQLAlchemy Row
    if isinstance(mapping, Mapping):
        return mapping
    raise ValueError(f"each {what} must be a dict; got {type(item).__name__}")


def _choice(value, allowed, field, what, name):
    text = str(value or "").strip().lower()
    if text not in allowed:
        raise ValueError(f"{what} {field} must be one of {', '.join(allowed)}; "
                         f"got {value!r} for {name!r}")
    return text


def _evidence(value):
    """evidence_type as a tuple: a list, None, or a PostgreSQL array literal ("{project,coursework}")."""
    if value is None:
        return ()
    if isinstance(value, str):
        value = value.strip().strip("{}").split(",")
    words = (str(v).strip().strip('"').strip() for v in value if v is not None)
    return tuple(w for w in words if w)


def _sources(value, name):
    """evidence_sources ({"project": ["Sales Dashboard"], ...}) as one tuple of distinct titles."""
    if value is None:
        return ()
    if not isinstance(value, Mapping):
        raise ValueError(f"student skill evidence_sources must be a dict; got {type(value).__name__} for {name!r}")
    titles = (str(t).strip() for ts in value.values() for t in (ts or ()) if t is not None)
    return tuple(dict.fromkeys(t for t in titles if t))


def _skill(index, item, catalogue, what):
    row = _row(item, what)
    name = row.get("skill_name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{what} without skill_name: {dict(row)!r}")
    name = name.strip()
    canonical = catalogue.lookup(name) or name
    skill_id = row.get("skill_id")
    skill = _Skill(index, str(skill_id) if skill_id else None, name, canonical, skill_key(canonical))
    if what == "student skill":
        level = _choice(row.get("proficiency_level"), PROFICIENCY_LEVELS, "proficiency_level", what, name)
        return skill._replace(level=level, evidence=_evidence(row.get("evidence_type")),
                              sources=_sources(row.get("evidence_sources"), name))
    importance = row.get("importance") or "required"            # NULL -> the DB default
    return skill._replace(importance=_choice(importance, IMPORTANCE_LEVELS, "importance", what, name))


def _same(required, student):
    """Same skill: same skill_id when both have one, else same canonical name."""
    if required.skill_id and student.skill_id:
        return required.skill_id == student.skill_id
    return bool(required.key) and required.key == student.key


def _solid(student):
    """Intermediate / advanced, or a beginner backed by a project, certification or
    internship. Coursework alone does not count (rule C)."""
    return student.level != "beginner" or not STRONG_EVIDENCE.isdisjoint(student.evidence)


# ── Similarity ────────────────────────────────────────────────
_extra_vectors = {}   # (model, mode, text) -> vector, for names outside the catalogue


def similarity_matrix(required_names, student_names, catalogue):
    """Cosine similarity, len(required_names) x len(student_names), of skill names.

    Names are canonical names where the catalogue has them. Catalogue skills
    reuse nlp.model.skill_embeddings() (built once per catalogue); any other
    name is embedded from the name alone and cached, so nothing is encoded
    twice. Tests replace this function so they do not need the model.
    """
    import numpy as np
    from nlp.model import encode, skill_embeddings, skill_texts

    if not required_names or not student_names:
        return np.zeros((len(required_names), len(student_names)), dtype=np.float32)
    mode = config.SKILL_TEXT_MODE
    vectors = skill_embeddings(catalogue, mode)
    where = {name: k for k, name in enumerate(vectors.names)}
    ends = np.append(vectors.starts[1:], vectors.matrix.shape[0])

    def texts_of(name):   # a skill outside the catalogue: its name only
        return skill_texts({"skill_name": name, "aliases": [], "description": ""}, mode)

    missing = sorted({t for n in set(required_names) | set(student_names) if n not in where
                      for t in texts_of(n) if (config.MODEL_NAME, mode, t) not in _extra_vectors})
    if missing:   # encode() loads the model, so only call it when needed
        for text, vector in zip(missing, encode(missing)):
            _extra_vectors[(config.MODEL_NAME, mode, text)] = vector

    def rows(names):
        blocks, starts, total = [], [], 0
        for name in names:
            if name in where:
                k = where[name]
                block = vectors.matrix[vectors.starts[k]:ends[k]]
            else:
                block = np.stack([_extra_vectors[(config.MODEL_NAME, mode, t)] for t in texts_of(name)])
            blocks.append(block)
            starts.append(total)
            total += len(block)
        return np.concatenate(blocks), np.array(starts, dtype=np.intp)

    req, req_starts = rows(required_names)
    stu, stu_starts = rows(student_names)
    sims = req @ stu.T
    if len(req_starts) != len(req):          # several rows per skill: best pair counts
        sims = np.maximum.reduceat(sims, req_starts, axis=0)
    if len(stu_starts) != len(stu):
        sims = np.maximum.reduceat(sims, stu_starts, axis=1)
    return sims


def _score(value):
    """Similarity as stored in skill_match_results.similarity_score: clipped
    to 0-1 and cut (not rounded) to 3 decimals. The thresholds are applied to
    this value, so a score shown as 0.599 is never counted as >= 0.60."""
    value = min(1.0, max(0.0, float(value)))
    return math.floor(value * 1000 + 1e-9) / 1000


# ── Classification ────────────────────────────────────────────
def _status(kind, similarity, student):
    """match_status for kind "same" (same skill) or "similar" (semantic).
    Only the same skill can be Strong; a different skill, however close, is at
    most Developing (rule A)."""
    if kind == "same":
        return "strong" if _solid(student) else "developing"
    if kind == "similar" and similarity >= config.RELATED_THRESHOLD:
        return "developing"
    return "gap"


def _best_similar(required, students, sims):
    """(kind, similarity, student) of the most similar student skill; ties go to
    the better status, then to the better-backed skill, then to the one listed first."""
    best_key, best = None, None
    for s in students:
        kind, sim = ("same", 1.0) if _same(required, s) else ("similar", _score(sims[s.index]))
        key = (sim, _STATUS_RANK[_status(kind, sim, s)], _solid(s), -s.index)
        if best_key is None or key > best_key:
            best_key, best = key, (kind, sim, s)
    return best


def _joined(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _detail(student):
    if not student.evidence:
        return student.level
    detail = f"{student.level}, with {_joined(list(dict.fromkeys(student.evidence)))} evidence"
    if student.sources:
        titles = list(student.sources[:MAX_TITLES])
        if len(student.sources) > MAX_TITLES:
            titles.append(f"{len(student.sources) - MAX_TITLES} more")
        detail += " from " + _joined(titles)
    return detail


def _result(required, decision, method, has_students):
    kind, similarity, student = decision or (None, 0.0, None)
    status = _status(kind, similarity, student)
    if status == "gap":
        similarity, student = 0.0, None
        case = "gap_empty" if not has_students else "gap_keyword" if method == "keyword" else "gap_similar"
    elif kind == "same":
        case = "same_" + status
    elif similarity >= config.MATCH_THRESHOLD:
        case = "similar"
    else:
        case = "related"
    reason = REASONS[case].format(skill=required.name,
                                  student=student.name if student else "",
                                  detail=_detail(student) if student else "")
    return MatchResult(
        skill_id=required.skill_id,
        skill_name=required.name,
        importance=required.importance,
        match_status=status,
        similarity_score=similarity,
        matching_method=method,
        matched_student_skill=student.name if student else None,
        reason=reason,
    )


def match(student_skills, required_skills, method, catalogue):
    """match_skills() after the method check (see nlp/__init__.py)."""
    students = [_skill(i, s, catalogue, "student skill") for i, s in enumerate(student_skills)]
    required = [_skill(i, r, catalogue, "required skill") for i, r in enumerate(required_skills)]

    decisions = {}   # required index -> (kind, similarity, student)
    if method != "semantic":
        for r in required:
            same = [s for s in students if _same(r, s)]
            if same:
                decisions[r.index] = ("same", 1.0, max(same, key=lambda s: (_solid(s), -s.index)))
    if method != "keyword" and students:
        todo = [r for r in required if r.index not in decisions]
        if todo:
            sims = similarity_matrix([r.canonical for r in todo],
                                     [s.canonical for s in students], catalogue)
            for r, row in zip(todo, sims):
                decisions[r.index] = _best_similar(r, students, row)
    return [_result(r, decisions.get(r.index), method, bool(students)) for r in required]
