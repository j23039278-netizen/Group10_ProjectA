# JD (Job Description) Dataset

**Owner:** Ng Yong Hin (AI / NLP Engineer)

This folder holds real IT job descriptions for 6 target roles. We use them to (a) check the skill lists in `job_role_skills` against the market (FR-03), (b) find skills that are missing from the library (FR-02), and (c) evaluate the L1 and L2 extractors in Sprint 4 (FR-04, FR-14).

> **Status (Sprint 2):** the pipeline and formats are ready and have been tested end-to-end on the fictional examples in `samples/`. **We are still waiting for the raw JD data**, so `jd_dataset.csv` and `gold/gold_sample.csv` have not been created yet.

## Sources

1. **Public Kaggle datasets.** Download them by hand into `data/raw/kaggle/`. Add one row per file to `data/raw/kaggle/LICENSES.csv` (`file,dataset,license,downloaded`). Check each licence before you use a dataset and record it there. The licence is copied into every JD's `source_license`.
2. **Manual copies** from JobStreet Malaysia, LinkedIn or company career pages. Save each one as `data/raw/manual/<ROLE_CODE>/<n>.txt`:
   ```
   https://… 2026-10-01          <- line 1: source URL and date collected
   Title: Junior Data Analyst    <- optional header lines (Title / Location / Company / Seniority)
   Location: Kuala Lumpur

   <JD body>
   ```
3. **Public job-board APIs (Phase 6, not built yet).** The collector (Greenhouse or Remotive APIs) will save raw JSON to `data/raw/api/<source>/<date>/*.json`. `ingest_jds.py` can already read that layout: a JSON list of jobs, or an object with a `jobs` list in Greenhouse or Remotive style, with `source = api:<source>` or a `source` value set in the file (for example `api:greenhouse:<board>`). Phase 6 will therefore not need to change this pipeline. There is an example in `samples/api/`.
4. **No web scraping.** Scraping LinkedIn, JobStreet or Indeed breaks their terms of service.

`data/raw/` is listed in `.gitignore`. Never commit raw files. Only the cleaned, anonymised `jd_dataset.csv` is committed.

**Target:** at least 30 JDs per role (180 in total). The ideal is 50–100 per role.

## Pipeline

```powershell
python data/jd_dataset/ingest_jds.py          # data/raw -> jd_dataset.csv
python data/jd_dataset/analyse_jd_skills.py   # -> jd_skill_frequency.csv, unmatched_terms.csv, role_skill_diff.csv
python data/jd_dataset/make_gold_sample.py    # -> gold/gold_sample.csv (60), gold_labels.csv (empty), gold_labels_draft.csv
python data/jd_dataset/load_jds.py            # -> job_descriptions (source='scraped'); add --dry-run to test
```

To test with the examples, pass `--raw-dir data/jd_dataset/samples`, `--dataset data/jd_dataset/samples/jd_dataset_sample.csv` and `--out-dir data/jd_dataset/samples`.

### Cleaning rules (`ingest_jds.py`)

- **Role:** the title is matched against keyword rules (`jd_common.ROLE_TITLE_RULES`). For manual files, the folder name decides the role. Titles that match none of the 6 roles are skipped.
- **Seniority:** `entry` (intern, graduate, trainee, fresh), `junior` (junior, associate) or `mid`. Titles with senior, lead, principal, manager, architect and similar words are **skipped**, because SEAGAS targets graduates.
- **Text:** HTML is removed. Emails become `[EMAIL]`, URLs become `[URL]`, phone numbers become `[PHONE]`, and company names (every name seen in the batch, plus any "… Sdn Bhd / Berhad / Pte Ltd / Inc") become `[COMPANY]`. Runs of whitespace are collapsed.
- **Filters:** texts shorter than 300 characters are dropped. Duplicates are dropped by an MD5 hash of the normalised text.
- `company` is always `Anonymised`.
- `jd_ref` values (`JD-DA-0001`, and so on) are stable. They are assigned by sorting on role, source and text hash.

### Fields (`jd_dataset.csv`)

`jd_ref, role_code, title, company, location, seniority, source, source_url, source_license, collected_date, raw_text`

- `source` is one of `kaggle:<dataset>`, `manual`, `api:<source>[:<board>]`, or `sample` (fictional test data only).
- `source_url` is the original posting URL (from the first line of a manual file, the URL column in Kaggle data, or `absolute_url` / `url` in API data).

Role codes: `DATA_ANALYST` (DA), `DATA_SCIENTIST` (DS), `SOFTWARE_DEV` (SD), `CYBER_ANALYST` (CY), `CLOUD_ENGINEER` (CE), `WEB_DEV` (WD).

### Frequency analysis (`analyse_jd_skills.py`)

This is a keyword baseline. It matches skill names and aliases with word boundaries, ignores case, keeps the longest match when matches overlap, and **never uses ambiguous aliases**. For each role it suggests an importance: `required` if at least 50% of the role's JDs mention the skill, `preferred` for 20–50%, and `bonus` for 10–20%. `role_skill_diff.csv` compares these suggestions with `seed_job_role_skills.sql`. The script **never changes the seed**. Yong Hin decides what to update. Frequent terms that the library does not cover go to `unmatched_terms.csv`. The script uses spaCy noun chunks if spaCy and `en_core_web_sm` are installed, and plain n-grams otherwise.

### Loading into the DB (`load_jds.py`)

Each JD becomes a `job_descriptions` row with `source='scraped'`, `profile_id=NULL`, `role_id` taken from the `role_code`, and `nlp_status='pending'`. Loading is idempotent: a JD is skipped if a `scraped` row with the same `md5(raw_text)` already exists. The table has no `jd_ref` column, and schema.sql is not changed. The connection string comes from `backend/.env` and is never printed.

## Gold set (Sprint 4 evaluation)

`make_gold_sample.py` draws 10 JDs per role with seed 42, 60 in total. **Gold labels must be made by a person.** The system being evaluated must not generate them, or the evaluation means nothing. `gold_labels_draft.csv` is a keyword pre-fill that only saves typing. Every row must be checked and corrected by hand before it goes into `gold_labels.csv`. See [gold/ANNOTATION_GUIDE.md](gold/ANNOTATION_GUIDE.md).

## `samples/`

These are **fictional** example JDs written to test the pipeline. They are not real postings. The folder has 8 usable JDs (manual, Kaggle-format and Greenhouse-API-format, one or more per role) plus one duplicate, one text that is too short, one senior title and one non-IT row, which test each filter. Do not load `samples/` into the DB and do not report numbers from it.
