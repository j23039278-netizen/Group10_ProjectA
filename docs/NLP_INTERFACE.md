# SEAGAS NLP Interface (contract for backend integration)

**Owner:** Ng Yong Hin (AI / NLP Engineer) | **Consumer:** Soh Way Miin (Carl), backend
**Status:** interface only. Types, validation and the skill catalogue work now;
`extract_skills()` and `match_skills()` raise `NotImplementedError` until the
extraction / matching branches are merged. The signatures and fields below will
not change without a note in this file.

---

## 1. Import

```python
from nlp import extract_skills, match_skills, load_catalogue
from nlp.types import ExtractedSkill, StudentSkill, RequiredSkill, MatchResult
```

- `nlp/` uses only the Python standard library in this version.
- The **repo root** must be on `sys.path` (not `nlp/` itself: `nlp/types.py`
  would then shadow Python's built-in `types` module).
- Everything is plain `dict` / `list` / `str` / `float`, so results can be
  passed to SQLAlchemy parameters or returned from FastAPI as they are.

## 2. Functions

### `extract_skills(text, method="hybrid", skills=None) -> list[ExtractedSkill]`

| Parameter | Type | Meaning |
|-----------|------|---------|
| `text` | `str` | Raw JD text (`job_descriptions.raw_text`). |
| `method` | `str` | `"keyword"`, `"semantic"` or `"hybrid"` (default). |
| `skills` | `list[dict] \| None` | Rows from `skills_library` (`skill_id`, `skill_name`, `category`, `aliases`, `description`, optional `is_active`). Pass them so results carry real UUIDs. `None` uses `nlp/resources/skills_taxonomy.json`, and then `skill_id` is `None`. SQLAlchemy `Row` objects are accepted too. |

Returns one `ExtractedSkill` per **distinct** skill found (its best occurrence),
ordered by `start_char`. Blank text returns `[]`.

### `match_skills(student_skills, required_skills, method="hybrid") -> list[MatchResult]`

| Parameter | Type | Meaning |
|-----------|------|---------|
| `student_skills` | `list[StudentSkill]` | The student's skills (`student_skills` JOIN `skills_library`). May be empty: every required skill is then a gap. |
| `required_skills` | `list[RequiredSkill]` | From `jd_extracted_skills` (JD path) or `job_role_skills` (role template path). |
| `method` | `str` | `"keyword"`, `"semantic"` or `"hybrid"` (default). |

Returns exactly **one `MatchResult` per item of `required_skills`, in the same
order**. An empty `required_skills` returns `[]`. Readiness scoring
(required = 3, preferred = 2, bonus = 1; strong = full, developing = half)
stays in the backend.

### Method values

| Value | Extraction | Matching |
|-------|------------|----------|
| `keyword` | Exact / alias / normalised matching against the catalogue ("Power-BI" = "PowerBI" = "Power BI"). Ambiguous aliases (R, Go, Excel, CV, REST, ...) only count with supporting context. | Same skill by `skill_id`, name, alias or normalised name. |
| `semantic` | Sentence-embedding similarity between JD phrases and skill names / descriptions. | Embedding similarity between required and student skills (e.g. MySQL vs PostgreSQL). |
| `hybrid` | Both, merged; keyword wins when both find the same skill. | Keyword first; semantic only for required skills keyword could not match. |

Any other value (including `"spacy_ner"`, `None`, wrong case) raises `ValueError`.

## 3. Types and database mapping

All types are `TypedDict`s in `nlp/types.py`. Every field is always present.

### `ExtractedSkill` → `jd_extracted_skills`

| Field | Type | Meaning | DB column |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | `skills_library` UUID; `None` only if no `skills` rows were passed | `skill_id` |
| `skill_name` | `str` | Canonical name from the catalogue, e.g. `"Power BI"` | (via `skill_id` → `skills_library.skill_name`) |
| `raw_skill_text` | `str` | Exact span of the JD, `text[start_char:end_char]`, e.g. `"PowerBI"`; at most 255 chars | `raw_skill_text` |
| `method` | `"keyword" \| "semantic"` | Extractor that found this skill. Never `"hybrid"`, even when `method="hybrid"` was requested | `extraction_method` |
| `confidence_score` | `float` 0–1 | Keyword hit = 1.0 (lower for ambiguous aliases); semantic = similarity | `confidence_score` (round to 3 dp) |
| `start_char` | `int` | Start offset of the span in `text` (inclusive) | not stored (UI highlighting) |
| `end_char` | `int` | End offset of the span in `text` (exclusive) | not stored |

`jd_extracted_skills.importance` is not produced in this version; leave the
column default (`'required'`).

### `StudentSkill` (input)

| Field | Type | Meaning | DB source |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | UUID | `student_skills.skill_id` |
| `skill_name` | `str` | Canonical name | `skills_library.skill_name` |
| `proficiency_level` | `"beginner" \| "intermediate" \| "advanced"` | Self-rated level | `student_skills.proficiency_level` |
| `evidence_type` | `list[str]` | `project`, `certification`, `coursework`, `internship`; `[]` if NULL | `student_skills.evidence_type` |

### `RequiredSkill` (input)

| Field | Type | Meaning | DB source |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | UUID | `jd_extracted_skills.skill_id` / `job_role_skills.skill_id` |
| `skill_name` | `str` | **Canonical** name (not the raw JD text) | `skills_library.skill_name` |
| `importance` | `"required" \| "preferred" \| "bonus"` | Weight in the readiness score | `jd_extracted_skills.importance` / `job_role_skills.importance` |

### `MatchResult` → `skill_match_results`

| Field | Type | Meaning | DB column |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | Copied from the `RequiredSkill` | `skill_id` |
| `skill_name` | `str` | Copied from the `RequiredSkill` | (via `skill_id`) |
| `importance` | `str` | Copied from the `RequiredSkill` | (scoring only) |
| `match_status` | `"strong" \| "developing" \| "gap"` | Decision for this skill | `match_status` |
| `similarity_score` | `float` 0–1 | 1.0 for same skill / alias, cosine similarity for semantic, 0.0 when nothing was found | `similarity_score` (round to 3 dp) |
| `matching_method` | `"keyword" \| "semantic" \| "hybrid"` | Method that decided this row: `keyword` or `semantic` when one of them found the match; for a gap it is the requested method (`hybrid` if both were tried) | `matching_method` |
| `matched_student_skill` | `str \| None` | `skill_name` of the student skill that triggered the match; `None` for a gap | `matched_student_skill` |
| `reason` | `str` | One short English sentence shown to the student | no column (API response only; see 6d) |

Planned `match_status` rules (thresholds will be tuned on the gold set and
written here when the matcher is merged):

- **strong**: the student has the skill (same skill / alias, or very high
  semantic similarity) at intermediate or advanced level.
- **developing**: the student has it at beginner level, or only a closely
  related skill.
- **gap**: nothing in the profile matches.

## 4. Examples

### `extract_skills`

```python
extract_skills(
    "Junior Data Analyst. Must know SQL and PowerBI; experience with "
    "data visualization tools is a plus.",
    method="hybrid",
    skills=skill_rows,  # from skills_library
)
```

```json
[
  {"skill_id": "5b1c...-sql", "skill_name": "SQL", "raw_skill_text": "SQL",
   "method": "keyword", "confidence_score": 1.0, "start_char": 31, "end_char": 34},
  {"skill_id": "9e0a...-pbi", "skill_name": "Power BI", "raw_skill_text": "PowerBI",
   "method": "keyword", "confidence_score": 1.0, "start_char": 39, "end_char": 46},
  {"skill_id": "77d2...-viz", "skill_name": "Data Visualisation", "raw_skill_text": "data visualization",
   "method": "keyword", "confidence_score": 1.0, "start_char": 64, "end_char": 82}
]
```

### `match_skills`

```python
match_skills(
    student_skills=[
        {"skill_id": "5b1c...-sql", "skill_name": "SQL",
         "proficiency_level": "advanced", "evidence_type": ["project", "coursework"]},
        {"skill_id": "a3f4...-tab", "skill_name": "Tableau",
         "proficiency_level": "intermediate", "evidence_type": ["coursework"]},
    ],
    required_skills=[
        {"skill_id": "5b1c...-sql", "skill_name": "SQL", "importance": "required"},
        {"skill_id": "9e0a...-pbi", "skill_name": "Power BI", "importance": "required"},
        {"skill_id": "c81e...-dkr", "skill_name": "Docker", "importance": "bonus"},
    ],
    method="hybrid",
)
```

```json
[
  {"skill_id": "5b1c...-sql", "skill_name": "SQL", "importance": "required",
   "match_status": "strong", "similarity_score": 1.0, "matching_method": "keyword",
   "matched_student_skill": "SQL",
   "reason": "You listed SQL at advanced level, which matches this skill."},
  {"skill_id": "9e0a...-pbi", "skill_name": "Power BI", "importance": "required",
   "match_status": "developing", "similarity_score": 0.78, "matching_method": "semantic",
   "matched_student_skill": "Tableau",
   "reason": "You know Tableau, a closely related tool; practise Power BI to make this a strong match."},
  {"skill_id": "c81e...-dkr", "skill_name": "Docker", "importance": "bonus",
   "match_status": "gap", "similarity_score": 0.0, "matching_method": "hybrid",
   "matched_student_skill": null,
   "reason": "No skill in your profile matches Docker."}
]
```

(UUIDs shortened; numbers are illustrative.)

## 5. Error behaviour

| Situation | Result |
|-----------|--------|
| `method` not in `keyword` / `semantic` / `hybrid` | `ValueError` → return HTTP 400 |
| `text` is not a `str` | `ValueError` |
| `skills` row without `skill_name`, or two rows with the same name (case-insensitive) | `ValueError` |
| Blank `text` / empty `required_skills` | `[]` (no error) |
| Skill rows with `is_active = FALSE` | Skipped |
| An alias claimed by two different skills | Ignored for lookup (no guessing) |
| Extraction / matching not merged yet | `NotImplementedError` → keep the current placeholder / Level 1 logic |
| Anything else unexpected | Propagates; set `job_descriptions.nlp_status = 'failed'` |

## 6. Backend changes needed (Carl)

These are suggestions; `nlp/` does not edit `backend/` or `database/schema.sql`.

**(a) `jd_extracted_skills.extraction_method` and "hybrid".** The CHECK allows
`'spacy_ner', 'keyword', 'semantic'`, not `'hybrid'`. Recommended: store the
per-skill `ExtractedSkill.method` (always `keyword` or `semantic`), which already
fits, so **no schema change is needed**. The requested method (`hybrid`) does not
need to be stored per row. (Alternative: add `'hybrid'` to the CHECK.)

**(b) `skill_match_results`.** Fill `matched_student_skill` and
`similarity_score` from `MatchResult` (the INSERT in `assessments.py` currently
omits `matched_student_skill`), and store `MatchResult.matching_method` per row.

**(c) Where the calls go.**

`backend/routers/jobs.py`, `trigger_nlp_analysis()`, at the `TODO Sprint 2`
comment (around line 227):

```python
from nlp import extract_skills

rows = db.execute(text("""
    SELECT skill_id, skill_name, category, aliases, description, is_active
    FROM skills_library
""")).fetchall()
try:
    extracted = extract_skills(jd.raw_text, method="hybrid",
                               skills=[dict(r._mapping) for r in rows])
except NotImplementedError:
    extracted = []  # NLP not merged yet: keep the placeholder behaviour

db.execute(text("DELETE FROM jd_extracted_skills WHERE jd_id = :jid"), {"jid": jd_id})
for s in extracted:
    db.execute(text("""
        INSERT INTO jd_extracted_skills
            (jd_id, skill_id, raw_skill_text, extraction_method, confidence_score)
        VALUES (:jid, :sid, :raw, :method, :conf)
    """), {"jid": jd_id, "sid": s["skill_id"], "raw": s["raw_skill_text"],
           "method": s["method"], "conf": round(s["confidence_score"], 3)})
```

Wrap it so any other exception sets `nlp_status = 'failed'` instead of `'complete'`.

`backend/routers/assessments.py`, `run_assessment()`, replacing the Level 1
matching loop (around lines 115–160):

```python
from nlp import match_skills

students = [{"skill_id": str(s.skill_id), "skill_name": s.skill_name,
             "proficiency_level": s.proficiency_level,
             "evidence_type": list(s.evidence_type or [])} for s in student_skills]
required = [{"skill_id": str(r.skill_id) if r.skill_id else None,
             "skill_name": r.skill_name,
             "importance": r.importance or "required"} for r in required_skills]
try:
    results = match_skills(students, required, method=req.matching_method)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except NotImplementedError:
    results = None  # NLP not merged yet: keep the Level 1 logic
```

Then use `match_status` / `similarity_score` / `matching_method` /
`matched_student_skill` from each result in the existing weighted scoring and
INSERT, and add `reason` to `match_results` in the API response.

**Also worth fixing while there:**

- **(d)** `reason` has no column. Either return it only in the `/run` response,
  or add `reason TEXT` to `skill_match_results` so `GET /assessments/{id}` can
  show it later.
- **(e)** In the JD path of `run_assessment()`, `jes.raw_skill_text AS skill_name`
  passes raw JD text (e.g. "PowerBI"). Use
  `COALESCE(sl.skill_name, jes.raw_skill_text) AS skill_name` so `RequiredSkill`
  gets the canonical name.
- **(f)** `assessments.py` appends `dirname(dirname(__file__))`, which is
  `backend/`, not the repo root. Uvicorn runs from `backend/`, so
  `import nlp` (and `import recommendation`) need the repo root on `sys.path`:
  `Path(__file__).resolve().parents[2]`.
- **(g)** `category_score()` only checks `skill_id` equality, so developing
  matches score 0 in the 7-dimension breakdown. It could reuse `match_status`
  from the results.
- **(h)** `AssessmentRequest.matching_method` defaults to `"semantic"`;
  the NLP default is `"hybrid"`. Either is valid; pick one for the UI.

## 7. Skill catalogue helpers

```python
cat = load_catalogue()            # default taxonomy, cached (138 skills)
cat = load_catalogue(rows)        # DB rows -> real UUIDs, not cached

cat.get("power bi")               # entry for a canonical name, or None
cat.canonical_name("ReactJS")     # "React"   (name or alias, case-insensitive)
cat.lookup("Power-BI")            # "Power BI" (also tries the normalised key)
cat.is_ambiguous("Go")            # True       (R, Go, Excel, CV, REST, ...)
cat.skill_id("T-SQL")             # UUID of SQL, or None
```

Text helpers in `nlp/normalise.py`: `normalise_text()`, `uk_spelling()`
(US → UK, the library uses UK spelling), `singularise()`, `skill_key()`.
