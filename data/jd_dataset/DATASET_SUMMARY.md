# JD Dataset Summary (Sprint 2)

**Owner:** Ng Yong Hin (AI / NLP Engineer) · **Built:** 2026-10-12 with `ingest_jds.py` · **File:** `jd_dataset.csv`

Every figure below comes from `jd_dataset.csv` and the ingest log of 2026-10-12. Re-check them if the dataset is rebuilt.

## Counts per role

| Role | JDs | JobStreet | Indeed | entry | junior | mid | Median length (chars) |
|---|---:|---:|---:|---:|---:|---:|---:|
| DATA_ANALYST (DA) | 11 | 10 | 1 | 4 | 6 | 1 | 2,171 |
| DATA_SCIENTIST (DS) | 10 | 5 | 5 | 7 | 3 | 0 | 1,792 |
| SOFTWARE_DEV (SD) | 13 | 12 | 1 | 7 | 6 | 0 | 1,503 |
| CYBER_ANALYST (CY) | 10 | 6 | 4 | 5 | 4 | 1 | 1,525 |
| CLOUD_ENGINEER (CE) | 10 | 6 | 4 | 6 | 3 | 1 | 1,769 |
| WEB_DEV (WD) | 11 | 10 | 1 | 4 | 6 | 1 | 1,532 |
| **Total** | **65** | **49** | **16** | **33** | **28** | **4** | **1,652** |

All six roles meet the Sprint 2 target of at least 10 JDs per role (60 in total). The Sprint 3 goal of 30 or more per role is not met yet.

Text length after cleaning ranges from 438 to 5,139 characters (117,770 characters and about 16,700 words in total).

## Sources and licence

| Source (`source`) | Site | JDs | Licence / terms note |
|---|---|---:|---|
| `manual` | JobStreet Malaysia (`my.jobstreet.com`) | 49 | Copied by hand for non-commercial academic research |
| `manual` | Indeed Malaysia (`malaysia.indeed.com`) | 16 | Copied by hand for non-commercial academic research |
| `kaggle:*` | none | 0 | No Kaggle dataset used in Sprint 2 |
| `api:*` | none | 0 | Phase 6 collector not built yet (planned for Sprint 3) |

- Each JD keeps its original posting URL in `source_url`. Tracking parameters were removed by hand.
- No web scraper was used. Every posting was opened and copied by a person.
- The raw copies stay in `data/raw/` (git-ignored). Only the cleaned and anonymised text in `jd_dataset.csv` is committed.

**Collection period:** all 65 JDs were collected on 2026-10-12 (single collection date).

**Seniority:** taken from the `Seniority:` header set by hand in 62 files. The other 3 files have no header, so the title rules classified them as `mid`. The 4 `mid` rows are JD-CE-0008, JD-CY-0002, JD-DA-0005 and JD-WD-0003. 29 of the 65 titles contain "intern" or "internship".

**Location:** Kuala Lumpur 32, Selangor 25, Penang 6, Johor 2. 11 postings are marked hybrid and 2 remote.

## Filters applied (ingest log, 2026-10-12)

| Step | Rows removed |
|---|---:|
| Files read | 65 |
| Title not one of the 6 roles | 0 (for manual files the folder name sets the role, so this filter does not apply) |
| Senior / management title | 0 (the hand-set `Seniority:` header takes priority over the title rules) |
| Shorter than 300 characters after cleaning | 0 |
| Duplicate text (MD5 of normalised text) | 0 |
| **Kept** | **65** |

## Anonymisation

| Rule | Effect on this batch |
|---|---|
| "About the company" / "About us" employer blurb removed | 27 JDs (8,241 characters) |
| Company names, their core forms and the alias list (`data/raw/company_aliases.txt`) → `[COMPANY]` | 17 replacements in 13 JDs, plus 1 title |
| E-mail → `[EMAIL]`, URL → `[URL]`, phone → `[PHONE]` | 0 (none were left in the copied bodies) |
| `company` column | `Anonymised` for every row |

A final check of `raw_text` found no `@`, no `http`/`www`, no runs of 8 or more digits, no "Sdn Bhd", "Berhad", "Pte Ltd" or "Pty Ltd", and none of the employer names or their short forms. Street and building names (for example "Bangsar South") and product or platform names that the posting needs (for example Shopee, Lazada) are kept.

## Derived files

| File | Contents |
|---|---|
| `jd_skill_frequency.csv` | 233 rows: share of each role's JDs that mention each library skill |
| `unmatched_terms.csv` | 300 frequent terms that no library skill or alias covers (n-grams; spaCy not installed) |
| `role_skill_diff.csv` | 189 rows comparing suggested and current importance in `seed_job_role_skills.sql`. **For manual review only. The seed has not been changed.** |
| `gold/gold_sample.csv` | 60 JDs (10 per role, seed 42) for the Sprint 4 evaluation |
| `gold/gold_labels_draft.csv` | 500 keyword pre-fill rows. These are not labels. Every row must be checked by hand. |
| `gold/gold_labels.csv` | Header only. It is filled by hand. |

## Known limitations

- **Small sample.** With 10 to 13 JDs per role, a single posting moves a skill's share by 8 to 10 percentage points. The importance suggestions are therefore only indicative.
- **Gold set overlaps the dataset.** The gold sample contains 60 of the 65 JDs, so the frequency analysis and the gold evaluation use almost the same postings until more JDs are collected.
- **Bias.** All postings are Malaysian, come from two job boards, were collected on a single day and were chosen by hand for entry or junior IT roles. See section 3.1 of `docs/report_drafts/dataset_description.md`.
