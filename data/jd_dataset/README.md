# JD (Job Description) Dataset

**Owner:** Ng Yong Hin (AI / NLP Engineer)

This folder holds real job descriptions for the 10 target roles (6 IT and 4 Business). We use them to (a) check the skill lists in `job_role_skills` against the market (FR-03), (b) find skills that are missing from the library (FR-02), and (c) evaluate the L1 and L2 extractors in Sprint 4 (FR-04, FR-14).

> **Status (Sprint 3):** `jd_dataset.csv` holds 350 real JDs, 35 for each of the 10 roles, so the target of 30 per role is met. 65 of them (6 IT roles) were copied by hand from JobStreet and Indeed Malaysia on 2026-10-12. The other 285 come from the Kaggle dataset "LinkedIn Job Postings (2023-2024)" (US postings, CC BY-SA 4.0). All 140 Business-role JDs are US postings, so adding Malaysian copies for those roles is the next step. `gold/gold_sample.csv` (60 of the 65 manual JDs) is unchanged. See [DATASET_SUMMARY.md](DATASET_SUMMARY.md) for counts, region mix, sources, filters and the attribution.

## Sources

1. **Public Kaggle datasets.** Download them by hand into `data/raw/kaggle/`. Add one row per file to `data/raw/kaggle/LICENSES.csv` (`file,dataset,license,downloaded`). Check each licence before you use a dataset and record it there. The licence is copied into every JD's `source_license`. In use: `postings.csv` from [arshkon/linkedin-job-postings](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) (CC BY-SA 4.0, attribution in [DATASET_SUMMARY.md](DATASET_SUMMARY.md#attribution-and-licences)). The other files of that dataset are not used. `ingest_jds.py --profile` prints each file's columns, row count, language, date range, region mix and title-to-role counts. Large files are streamed, never loaded whole.
2. **Manual copies** from JobStreet Malaysia, LinkedIn or company career pages. Save each one as `data/raw/manual/<ROLE_CODE>/<n>.txt`:
   ```
   https://… 2026-10-01          <- line 1: source URL and date collected
   Title: Junior Data Analyst    <- optional header lines (Title / Location / Company / Seniority)
   Location: Kuala Lumpur

   <JD body>
   ```
3. **Public job-board APIs (Phase 6, not built yet).** The collector (Greenhouse or Remotive APIs) will save raw JSON to `data/raw/api/<source>/<date>/*.json`. `ingest_jds.py` can already read that layout: a JSON list of jobs, or an object with a `jobs` list in Greenhouse or Remotive style, with `source = api:<source>` or a `source` value set in the file (for example `api:greenhouse:<board>`). Phase 6 will therefore not need to change this pipeline. There is an example in `samples/api/`.
4. **No web scraping.** Scraping LinkedIn, JobStreet or Indeed breaks their terms of service. Kaggle files are downloaded by hand as published by their authors, under the licence recorded in `LICENSES.csv`.

`data/raw/` is listed in `.gitignore`. Never commit raw files. Only the cleaned, anonymised `jd_dataset.csv` is committed.

**Target:** 30 or more JDs per role (Sprint 3). The Sprint 2 target was 60 in total (10 per role, NFR-09 in the project proposal).

**Company aliases (optional):** `data/raw/company_aliases.txt` lists other names of the employers (short forms such as "DXC", brands, parent groups), one per line, with `#` for comments. They are masked like the `Company:` header. This file is git-ignored with the rest of `data/raw/`.

## Pipeline

```powershell
python data/jd_dataset/ingest_jds.py --profile   # describe each Kaggle CSV; writes nothing
python data/jd_dataset/ingest_jds.py          # data/raw -> jd_dataset.csv (options: --cap, --employer-cap, --seed)
python data/jd_dataset/analyse_jd_skills.py   # -> jd_skill_frequency.csv, unmatched_terms.csv, role_skill_diff.csv
python data/jd_dataset/make_gold_sample.py    # -> gold/gold_sample.csv (60), gold_labels.csv (empty), gold_labels_draft.csv
python data/jd_dataset/load_jds.py            # -> job_descriptions (source='scraped'); add --dry-run to test
```

To test with the examples, pass `--raw-dir data/jd_dataset/samples`, `--dataset data/jd_dataset/samples/jd_dataset_sample.csv` and `--out-dir data/jd_dataset/samples`.

### Cleaning rules (`ingest_jds.py`)

- **Role:** the title is matched against keyword rules (`jd_common.ROLE_TITLE_RULES`, first match wins). For manual files, the folder name decides the role. Titles that match none of the 10 roles are skipped. Broad keywords need context. Bare "security" needs an IT word: "Security Officer" is a guard, while "Information System Security Officer" is CYBER_ANALYST. "Front end" needs a development word. Clearance wording, product names such as "Marketing Cloud", pay rates and the part of a title after "for" / "with" are ignored. "Business Intelligence Analyst" and "Financial Data Analyst" are DATA_ANALYST. All the decisions are listed in DATASET_SUMMARY.md and tested in `tests/test_jd_ingest.py`.
- **Seniority:** `entry` (intern, graduate, trainee, fresh), `junior` (junior, associate) or `mid`. Titles with senior, lead, principal, manager, architect, chief, supervisor and similar words are **skipped**, because SEAGAS targets graduates. A Kaggle experience-level column (LinkedIn `formatted_experience_level`) only refines a plain title: Internship / Entry level → entry, Associate → junior, Director / Executive → skipped.
- **Region:** `Malaysia`, `other APAC`, `remote` or `other`, derived from `location` (`jd_common.region_of`) and reported per role for the JD-bias discussion.
- **Text:** HTML is removed. The employer blurb ("About the company" / "About us") is removed up to the next "Perks and benefits:" or "Key Highlights" line, or to the end. Emails (also bare domains such as "@example.com") become `[EMAIL]`, URLs and social handles become `[URL]`, phone numbers become `[PHONE]`, and company names become `[COMPANY]` in the text and the title. Company names cover every manual or API company name in the batch, its core form without the legal suffix or "(Malaysia)", the aliases in `company_aliases.txt`, and any "… Sdn Bhd / Berhad / Pte Ltd / Inc". A Kaggle row also masks its own company name and that name's distinctive brand words, matched case-sensitively (for example "Apex" for "Apex Systems"). It does not mask the names of the thousands of other employers in the file. Runs of whitespace are collapsed.
- **Filters:** texts shorter than 300 characters are dropped. Duplicates are dropped by an MD5 hash of the normalised text.
- **Kaggle sampling:** a large file must not swamp the dataset. Per role and Kaggle file, at most `--cap` JDs are drawn. By default this is what the role still needs to reach 30 from the other sources, plus 5 (0 if it already has 30). The draw happens after the filters above, uses seed 42, and prefers entry and junior postings, then Malaysia, then other APAC, then the rest. At most `--employer-cap` (default 5) JDs per employer per role are drawn. The employer is the website domain, else the company name, else the company id, read before anonymisation. Manual and API JDs are never capped.
- `company` is always `Anonymised`.
- `jd_ref` values (`JD-DA-0001`, and so on) are stable. The existing `jd_dataset.csv` is read first, and its rows keep their jd_ref and text, also when their raw file is not in `data/raw/`. A raw JD with the same text hash, or the same source and URL, counts as already present. New JDs get the next number per role, ordered by source and text hash. Re-running gives an identical file, and adding a file never renumbers old JDs. `--rebuild` starts from scratch and renumbers, so never use it once gold labels exist. To drop a JD, delete its row from `jd_dataset.csv`.

### Fields (`jd_dataset.csv`)

`jd_ref, role_code, title, company, location, region, seniority, source, source_url, source_license, collected_date, raw_text`

- `source` is one of `kaggle:<dataset>`, `manual`, `api:<source>[:<board>]`, or `sample` (fictional test data only).
- `source_url` is the original posting URL (from the first line of a manual file, the URL column in Kaggle data, or `absolute_url` / `url` in API data).
- `source_license` is set per row. Rows from `kaggle:arshkon/linkedin-job-postings` are `CC BY-SA 4.0`, and they must keep their attribution when reused.

Role codes: `DATA_ANALYST` (DA), `DATA_SCIENTIST` (DS), `SOFTWARE_DEV` (SD), `CYBER_ANALYST` (CY), `CLOUD_ENGINEER` (CE), `WEB_DEV` (WD), `BUSINESS_ANALYST` (BA), `FINANCIAL_ANALYST` (FA), `HR_EXEC` (HR), `MARKETING_EXEC` (MK).

### Frequency analysis (`analyse_jd_skills.py`)

This is a keyword baseline. It matches skill names and aliases with word boundaries, ignores case, keeps the longest match when matches overlap, and **never uses ambiguous aliases**. For each role it suggests an importance: `required` if at least 50% of the role's JDs mention the skill, `preferred` for 20–50%, and `bonus` for 10–20%. `role_skill_diff.csv` compares these suggestions with `seed_job_role_skills.sql`. The script **never changes the seed**. Yong Hin decides what to update. Frequent terms that the library does not cover go to `unmatched_terms.csv`. The script uses spaCy noun chunks if spaCy and `en_core_web_sm` are installed, and plain n-grams otherwise.

### Loading into the DB (`load_jds.py`)

Each JD becomes a `job_descriptions` row with `source='scraped'`, `profile_id=NULL`, `role_id` taken from the `role_code`, and `nlp_status='pending'`. Loading is idempotent: a JD is skipped if a `scraped` row with the same `md5(raw_text)` already exists. The table has no `jd_ref` column, and schema.sql is not changed. The connection string comes from `backend/.env` and is never printed.

## Gold set (Sprint 4 evaluation)

`make_gold_sample.py` draws 10 JDs per role with seed 42. The committed `gold/gold_sample.csv` (60 JDs, IT roles only) was drawn from the Sprint 2 dataset. Do not re-run the script on the larger dataset, because it would draw a different sample. **Gold labels must be made by a person.** The system being evaluated must not generate them, or the evaluation means nothing. `gold_labels_draft.csv` is a keyword pre-fill that only saves typing. Every row must be checked and corrected by hand before it goes into `gold_labels.csv`. See [gold/ANNOTATION_GUIDE.md](gold/ANNOTATION_GUIDE.md).

## `samples/`

These are **fictional** example JDs written to test the pipeline. They are not real postings. The folder has 8 usable JDs (manual, Kaggle-format and Greenhouse-API-format, one or more per IT role) plus one duplicate, two texts that are too short, one senior title and one non-target title (an armed security officer), which test each filter. Do not load `samples/` into the DB and do not report numbers from it.
