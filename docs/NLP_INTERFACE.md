# SEAGAS NLP Interface (contract for backend integration)

**Owner:** Ng Yong Hin (AI / NLP Engineer) | **Consumer:** Soh Way Miin (Carl), backend
**Status (2026-10-15):** everything below works: `extract_skills()` with
`method="keyword"`, `"semantic"` and `"hybrid"` (`nlp/extractor.py`), and
`match_skills()` with all three methods (`nlp/matcher.py`). The signatures and fields
below will not change without a note in this file.

**Changes on 2026-10-15**

- `method="hybrid"` extraction and `match_skills()` are implemented; neither raises
  `NotImplementedError` any more.
- `MatchResult.matching_method` is now the method passed to `match_skills()`, the same
  on every row (before: "the method that decided this row"). It still fits the
  `skill_match_results` CHECK.
- The Strong / Developing / Gap rules, thresholds and reason templates are in
  [`docs/NLP_CLASSIFICATION_RULES.md`](NLP_CLASSIFICATION_RULES.md).

---

## 1. Import

```python
from nlp import extract_skills, match_skills, load_catalogue
from nlp.types import ExtractedSkill, StudentSkill, RequiredSkill, MatchResult
```

- `import nlp`, keyword extraction, `match_skills(method="keyword")` and the catalogue
  use only the Python standard library.
- Semantic and hybrid extraction, and `match_skills()` with `"semantic"` or `"hybrid"`,
  need the packages in `nlp/requirements.txt` (spaCy + `en_core_web_sm`,
  sentence-transformers, numpy). They are imported only when a similarity is needed.
  See section 8.
- The **repo root** must be on `sys.path` (not `nlp/` itself: `nlp/types.py` would then
  shadow Python's built-in `types` module).
- Everything is plain `dict` / `list` / `str` / `float`, so results can be passed to
  SQLAlchemy parameters or returned from FastAPI as they are.

## 2. Functions

### `extract_skills(text, method="hybrid", skills=None) -> list[ExtractedSkill]`

| Parameter | Type | Meaning |
|-----------|------|---------|
| `text` | `str` | Raw JD text (`job_descriptions.raw_text`). |
| `method` | `str` | `"keyword"`, `"semantic"` or `"hybrid"` (default). |
| `skills` | `list[dict] \| None` | Rows from `skills_library` (`skill_id`, `skill_name`, `category`, `aliases`, `description`, optional `is_active`). Pass them so results carry real UUIDs. `None` uses `nlp/resources/skills_taxonomy.json`, and then `skill_id` is `None`. SQLAlchemy `Row` objects are accepted too. |

Returns one `ExtractedSkill` per **distinct** skill found, ordered by
`start_char`. `raw_skill_text` and the offsets come from the skill's first
occurrence; `confidence_score` is the best over all occurrences. Blank text
returns `[]`.

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
| `keyword` | Exact / alias / normalised matching against the catalogue ("Power-BI" = "PowerBI" = "Power BI"). Ambiguous aliases (R, Go, Excel, CV, REST, ...) only count with supporting context. | Same skill only: same `skill_id` when both sides have one, else the same canonical name (aliases resolved). No similarity. |
| `semantic` | spaCy noun chunks, short verb phrases and short sentences of the JD, embedded with `all-MiniLM-L6-v2`; a phrase counts as its most similar catalogue skill when cosine similarity ≥ `MATCH_THRESHOLD` (`nlp/config.py`). | Cosine similarity between the required skill and every student skill; the most similar student skill decides. |
| `hybrid` | (1) every keyword hit; (2) items of coordinated skill lists that keyword could not resolve, read with the shared head noun ("good **analytical**, communication and problem-solving skills" → "analytical skills" → Critical Thinking); (3) semantic hits for skills not found yet whose span does not overlap a keyword span. Keyword results are exactly those of `method="keyword"`. | Keyword first; semantic only for required skills keyword could not match. |

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
| `confidence_score` | `float` 0–1 | Keyword hit = 1.0 (0.8 for an ambiguous alias with context); semantic = cosine similarity | `confidence_score` (round to 3 dp) |
| `start_char` | `int` | Start offset of the span in `text` (inclusive) | not stored (UI highlighting) |
| `end_char` | `int` | End offset of the span in `text` (exclusive) | not stored |

`jd_extracted_skills.importance` is not produced in this version; leave the
column default (`'required'`).

### `StudentSkill` (input)

| Field | Type | Meaning | DB source |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | UUID | `student_skills.skill_id` |
| `skill_name` | `str` | Canonical name | `skills_library.skill_name` |
| `proficiency_level` | `"beginner" \| "intermediate" \| "advanced"` | Self-rated level (case-insensitive) | `student_skills.proficiency_level` |
| `evidence_type` | `list[str]` | `project`, `certification`, `coursework`, `internship`; `[]` or `None` if there is none. A PostgreSQL array literal (`"{project,coursework}"`) is accepted too | `student_skills.evidence_type` |

### `RequiredSkill` (input)

| Field | Type | Meaning | DB source |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | UUID | `jd_extracted_skills.skill_id` / `job_role_skills.skill_id` |
| `skill_name` | `str` | **Canonical** name (not the raw JD text) | `skills_library.skill_name` |
| `importance` | `"required" \| "preferred" \| "bonus"` | Weight in the readiness score; `None` counts as `"required"` (the column default) | `jd_extracted_skills.importance` / `job_role_skills.importance` |

### `MatchResult` → `skill_match_results`

| Field | Type | Meaning | DB column |
|-------|------|---------|-----------|
| `skill_id` | `str \| None` | Copied from the `RequiredSkill` | `skill_id` |
| `skill_name` | `str` | Copied from the `RequiredSkill` | (via `skill_id`) |
| `importance` | `str` | Copied from the `RequiredSkill` | (scoring only) |
| `match_status` | `"strong" \| "developing" \| "gap"` | Decision for this skill | `match_status` |
| `similarity_score` | `float` 0–1 | 1.0 for the same skill / alias, cosine similarity for a semantic match (cut to 3 decimals), 0.0 for a gap | `similarity_score` |
| `matching_method` | `"keyword" \| "semantic" \| "hybrid"` | The method passed to `match_skills()`, the same on every row | `matching_method` |
| `matched_student_skill` | `str \| None` | `skill_name` of the student skill that decided the row; `None` for a gap | `matched_student_skill` |
| `reason` | `str` | One plain-English sentence for the student, from a fixed template | no column (API response only; see 6d) |

Rules, in short (full table and templates in `docs/NLP_CLASSIFICATION_RULES.md`):

- **strong**: the same skill, or similarity ≥ `MATCH_THRESHOLD` (0.60), and the student
  skill is intermediate / advanced or has evidence.
- **developing**: the same, but beginner with no evidence; or
  `RELATED_THRESHOLD` (0.50) ≤ similarity < 0.60.
- **gap**: anything else.

## 4. Examples

Real output of the code on 2026-10-15 (`skills=None`, so `skill_id` is `None`; pass
`skills_library` rows to get UUIDs).

### `extract_skills`

```python
extract_skills(
    "Junior Data Analyst. Must know SQL and PowerBI; experience with data "
    "visualization tools is a plus. Good analytical and communication skills.",
    method="hybrid",
)
```

```json
[
  {"skill_id": null, "skill_name": "SQL", "raw_skill_text": "SQL",
   "method": "keyword", "confidence_score": 1.0, "start_char": 31, "end_char": 34},
  {"skill_id": null, "skill_name": "Power BI", "raw_skill_text": "PowerBI",
   "method": "keyword", "confidence_score": 1.0, "start_char": 39, "end_char": 46},
  {"skill_id": null, "skill_name": "Data Visualisation", "raw_skill_text": "data visualization",
   "method": "keyword", "confidence_score": 1.0, "start_char": 64, "end_char": 82},
  {"skill_id": null, "skill_name": "Critical Thinking", "raw_skill_text": "analytical",
   "method": "semantic", "confidence_score": 0.7698968648910522, "start_char": 105, "end_char": 115},
  {"skill_id": null, "skill_name": "Communication", "raw_skill_text": "communication skills",
   "method": "keyword", "confidence_score": 1.0, "start_char": 120, "end_char": 140}
]
```

`method="keyword"` returns the same rows without Critical Thinking.

### `match_skills`

```python
match_skills(
    student_skills=[
        {"skill_id": None, "skill_name": "SQL", "proficiency_level": "advanced",
         "evidence_type": ["project", "coursework"]},
        {"skill_id": None, "skill_name": "Python", "proficiency_level": "beginner",
         "evidence_type": []},
        {"skill_id": None, "skill_name": "Tableau", "proficiency_level": "intermediate",
         "evidence_type": ["coursework"]},
        {"skill_id": None, "skill_name": "AWS", "proficiency_level": "intermediate",
         "evidence_type": ["certification"]},
    ],
    required_skills=[
        {"skill_id": None, "skill_name": "SQL", "importance": "required"},
        {"skill_id": None, "skill_name": "Python", "importance": "required"},
        {"skill_id": None, "skill_name": "Power BI", "importance": "required"},
        {"skill_id": None, "skill_name": "Azure", "importance": "preferred"},
        {"skill_id": None, "skill_name": "Docker", "importance": "bonus"},
    ],
    method="hybrid",
)
```

```json
[
  {"skill_id": null, "skill_name": "SQL", "importance": "required",
   "match_status": "strong", "similarity_score": 1.0, "matching_method": "hybrid",
   "matched_student_skill": "SQL",
   "reason": "You list SQL (advanced, with project and coursework evidence), which matches this skill, so this is marked Strong."},
  {"skill_id": null, "skill_name": "Python", "importance": "required",
   "match_status": "developing", "similarity_score": 1.0, "matching_method": "hybrid",
   "matched_student_skill": "Python",
   "reason": "You list Python (beginner). A beginner skill needs project, certification or internship evidence to count as Strong, so this is marked Developing."},
  {"skill_id": null, "skill_name": "Power BI", "importance": "required",
   "match_status": "gap", "similarity_score": 0.0, "matching_method": "hybrid",
   "matched_student_skill": null,
   "reason": "No skill in your profile is Power BI or close enough to it, so this is marked as a Gap."},
  {"skill_id": null, "skill_name": "Azure", "importance": "preferred",
   "match_status": "developing", "similarity_score": 0.524, "matching_method": "hybrid",
   "matched_student_skill": "AWS",
   "reason": "You list AWS (intermediate, with certification evidence). It is closely related to Azure but not the same skill, so this is marked Developing."},
  {"skill_id": null, "skill_name": "Docker", "importance": "bonus",
   "match_status": "gap", "similarity_score": 0.0, "matching_method": "hybrid",
   "matched_student_skill": null,
   "reason": "No skill in your profile is Docker or close enough to it, so this is marked as a Gap."}
]
```

Tableau scores only 0.251 against Power BI, so Power BI is a gap (see the
classification rules, section 7). With the backend's weights this student's readiness
is 5.5 / 12 = **45.83**.

## 5. Error behaviour

| Situation | Result |
|-----------|--------|
| `method` not in `keyword` / `semantic` / `hybrid` | `ValueError` → return HTTP 400 |
| `text` is not a `str` | `ValueError` |
| `skills` row without `skill_name`, or two rows with the same name (case-insensitive) | `ValueError` |
| A student / required skill that is not a dict (or SQLAlchemy `Row`), has no `skill_name`, or has an unknown `proficiency_level` / `importance` | `ValueError` → HTTP 400 |
| Blank `text` / empty `required_skills` | `[]` (no error) |
| Empty `student_skills` | One gap per required skill (no error, no model load) |
| Skill rows with `is_active = FALSE` | Skipped |
| An alias claimed by two different skills | Ignored for lookup (no guessing) |
| `"semantic"` / `"hybrid"` without `nlp/requirements.txt` installed | `ImportError` / `OSError` (spaCy model missing) → treat like any other failure |
| Anything else unexpected | Propagates; set `job_descriptions.nlp_status = 'failed'` |

## 6. Backend changes needed (Carl)

These are suggestions; `nlp/` does not edit `backend/` or `database/schema.sql`.

**(a) `jd_extracted_skills.extraction_method` and "hybrid".** The CHECK allows
`'spacy_ner', 'keyword', 'semantic'`, not `'hybrid'`. Store the per-skill
`ExtractedSkill.method` (always `keyword` or `semantic`), which already fits, so **no
schema change is needed**.

**(b) `skill_match_results`.** Fill `matched_student_skill` and `similarity_score` from
`MatchResult` (the INSERT in `assessments.py` currently omits `matched_student_skill`).

**(c) Where the calls go.**

`backend/routers/jobs.py`, `trigger_nlp_analysis()`, replacing the `TODO Sprint 2`
comment (around line 227):

```python
    # ── NLP: extract skills from the JD (docs/NLP_INTERFACE.md) ──
    from nlp import extract_skills

    rows = db.execute(text("""
        SELECT skill_id, skill_name, category, aliases, description, is_active
        FROM skills_library
    """)).fetchall()
    try:
        extracted = extract_skills(jd.raw_text, method="hybrid",
                                   skills=[dict(r._mapping) for r in rows])
    except Exception:
        db.execute(text("UPDATE job_descriptions SET nlp_status = 'failed' WHERE jd_id = :jid"),
                   {"jid": jd_id})
        db.commit()
        raise HTTPException(status_code=500, detail="Skill extraction failed")

    db.execute(text("DELETE FROM jd_extracted_skills WHERE jd_id = :jid"), {"jid": jd_id})
    for s in extracted:
        db.execute(text("""
            INSERT INTO jd_extracted_skills
                (jd_id, skill_id, raw_skill_text, extraction_method, confidence_score)
            VALUES (:jid, :sid, :raw, :method, :conf)
        """), {"jid": jd_id, "sid": s["skill_id"], "raw": s["raw_skill_text"][:255],
               "method": s["method"], "conf": round(s["confidence_score"], 3)})
```

The existing lines after it (set `nlp_status = 'complete'`, commit) stay.

`backend/routers/assessments.py`, `run_assessment()`, replacing the matching block
(around lines 114–162, from `# ── Matching Logic` to the end of the `for req_skill`
loop):

```python
    # ── Matching Logic (nlp/, rules in docs/NLP_CLASSIFICATION_RULES.md) ──
    from nlp import match_skills

    students = [{"skill_id": str(s.skill_id), "skill_name": s.skill_name,
                 "proficiency_level": s.proficiency_level,
                 "evidence_type": list(s.evidence_type or [])} for s in student_skills]
    required = [{"skill_id": str(r.skill_id) if r.skill_id else None,
                 "skill_name": r.skill_name,
                 "importance": r.importance or "required"} for r in required_skills]
    try:
        match_results = match_skills(students, required, method=req.matching_method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Weighted scoring: required=3, preferred=2, bonus=1; strong=1, developing=0.5, gap=0
    IMPORTANCE_WEIGHTS = {"required": 3, "preferred": 2, "bonus": 1}
    STATUS_CREDIT      = {"strong": 1.0, "developing": 0.5, "gap": 0.0}

    earned_points = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) * STATUS_CREDIT[m["match_status"]]
                        for m in match_results)
    max_points    = sum(IMPORTANCE_WEIGHTS.get(m["importance"], 1) for m in match_results)
    strong_count     = sum(m["match_status"] == "strong" for m in match_results)
    developing_count = sum(m["match_status"] == "developing" for m in match_results)
    gap_count        = sum(m["match_status"] == "gap" for m in match_results)
```

`readiness_score`, the response and `match_results` keep their names; each result now
also has `matched_student_skill` and `reason`. In the INSERT into `skill_match_results`,
add the matched skill:

```python
                INSERT INTO skill_match_results
                    (assessment_id, skill_id, match_status, similarity_score,
                     matching_method, matched_student_skill)
                VALUES (:aid, :sid, :status, :score, :method, :matched)
                ON CONFLICT (assessment_id, skill_id) DO NOTHING
            ...
                    "score":   mr["similarity_score"],      # already 3 decimals
                    "method":  mr["matching_method"],
                    "matched": mr["matched_student_skill"],
```

**Also worth fixing while there:**

- **(d)** `reason` has no column. Either return it only in the `/run` response (it is
  in `match_results` already), or add `reason TEXT` to `skill_match_results` so
  `GET /assessments/{id}` can show it later.
- **(e)** In the JD path of `run_assessment()`, `jes.raw_skill_text AS skill_name`
  passes raw JD text (e.g. "PowerBI" or "analytical"). Use
  `COALESCE(sl.skill_name, jes.raw_skill_text) AS skill_name` so `RequiredSkill`
  gets the canonical name.
- **(f)** `import nlp` needs the repo root on `sys.path`. Today it only works because
  `routers/auth.py` appends `".."` and uvicorn runs from `backend/`;
  `assessments.py` appends `backend/`, not the root. A robust line at the top of
  `assessments.py` and `jobs.py`:
  `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))`.
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

## 8. Semantic and hybrid (Level 2)

- **Install:** `pip install -r nlp/requirements.txt` (spaCy 3.8.16, `en_core_web_sm`
  3.8.0, sentence-transformers 6.1.0, transformers 5.19.0, torch 2.14.1 CPU, numpy
  2.4.4, scikit-learn 1.8.0; matplotlib is only for the experiments). Most of the
  download is torch. If the `en_core_web_sm` wheel URL is blocked:
  `python -m spacy download en_core_web_sm`.
- **Model:** `config.MODEL_NAME` (`all-MiniLM-L6-v2`) is loaded once per process on
  first use (`nlp/model.py`, thread-safe). The very first run downloads ~90 MB into the
  Hugging Face cache (`HF_HOME`). After that, setting `HF_HUB_OFFLINE=1` skips the
  network check on start-up.
- **First-load time (this laptop, CPU):** model 17–28 s, spaCy 1.4 s. Catalogue skill
  embeddings are cached in `nlp/resources/skill_embeddings.npy` (+ `.json` with the
  catalogue hash; both git-ignored) and rebuilt automatically when `skills_library`
  changes. The per-alias embeddings for coordinated lists are built in memory on the
  first hybrid extraction that needs them (about 0.3 s).
- **Speed after warm-up:** hybrid extraction 0.12 s per JD (65 JDs, mean 1,840 chars;
  keyword under 1 ms, semantic 0.12 s); `match_skills` about 1 ms per assessment.
  Matching catalogue skills only needs numpy and the cached embeddings, so it does not
  load the model; a skill name outside the catalogue does.
- **Thresholds:** `MATCH_THRESHOLD = 0.60`, `RELATED_THRESHOLD = 0.50`,
  `SKILL_TEXT_MODE = "name_aliases"`, plus `LIST_ITEM_TEXT_MODE = "name_aliases_max"`
  and `LIST_ITEM_THRESHOLD = 0.70` for coordinated lists in hybrid extraction. They
  live only in `nlp/config.py`; how they were chosen is in
  `nlp/experiments/THRESHOLDS.md`.
- **Results:** hybrid finds 11.2 skills per JD on the 65 JDs (keyword 9.2, semantic
  7.3) and 7 of 7 skills on the POC004 brief example (keyword 6 of 7).
- **Warm-up:** at FastAPI start-up, run
  `extract_skills("Good analytical and communication skills in SQL.", method="hybrid")`
  once (in a background thread if start-up should not wait), so the first real request
  does not pay the model load.
