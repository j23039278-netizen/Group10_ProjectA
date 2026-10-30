# JD Dataset Summary (Sprint 3)

**Owner:** Ng Yong Hin (AI / NLP Engineer) · **Built:** 2026-10-30 with `ingest_jds.py` (the 65 manual JDs date from 2026-10-12) · **File:** `jd_dataset.csv`

Every figure below comes from `jd_dataset.csv` and the ingest log of 2026-10-30. Re-check them if the dataset is rebuilt.

## Counts per role

| Role | JDs | JobStreet | Indeed | Kaggle (LinkedIn US) | entry | junior | mid | Median length (chars) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DATA_ANALYST (DA) | 35 | 10 | 1 | 24 | 17 | 17 | 1 | 2,369 |
| DATA_SCIENTIST (DS) | 35 | 5 | 5 | 25 | 25 | 10 | 0 | 3,343 |
| SOFTWARE_DEV (SD) | 35 | 12 | 1 | 22 | 25 | 10 | 0 | 2,909 |
| CYBER_ANALYST (CY) | 35 | 6 | 4 | 25 | 23 | 11 | 1 | 3,172 |
| CLOUD_ENGINEER (CE) | 35 | 6 | 4 | 25 | 25 | 9 | 1 | 3,076 |
| WEB_DEV (WD) | 35 | 10 | 1 | 24 | 22 | 12 | 1 | 2,031 |
| BUSINESS_ANALYST (BA) | 35 | 0 | 0 | 35 | 9 | 26 | 0 | 2,582 |
| FINANCIAL_ANALYST (FA) | 35 | 0 | 0 | 35 | 18 | 17 | 0 | 2,602 |
| HR_EXEC (HR) | 35 | 0 | 0 | 35 | 22 | 13 | 0 | 3,631 |
| MARKETING_EXEC (MK) | 35 | 0 | 0 | 35 | 26 | 9 | 0 | 3,057 |
| **Total** | **350** | **49** | **16** | **285** | **212** | **134** | **4** | **2,820** |

**All 10 roles meet the Sprint 3 target of at least 30 JDs per role, so no role is short.** Each role has 35 JDs (30 plus the default margin of 5). Seniority is skewed to entry level because the draw prefers entry and junior postings (see "Kaggle sampling" below), and all 285 Kaggle JDs are entry or junior.

Text length after cleaning ranges from 316 to 9,179 characters (1,099,921 characters and about 151,600 words in total). Kaggle postings are longer than the manual copies: their median is 3,214 characters, against 1,652 for the manual ones. They often keep benefits and equal-opportunity paragraphs.

## Region mix (JD bias)

`region` is derived from the `location` text only (`jd_common.region_of`): Malaysia, other APAC, remote (the location says remote, anywhere or work from home) or other.

| Role | Malaysia | other APAC | remote | other |
|---|---:|---:|---:|---:|
| DATA_ANALYST | 11 | 0 | 0 | 24 |
| DATA_SCIENTIST | 10 | 0 | 0 | 25 |
| SOFTWARE_DEV | 13 | 0 | 0 | 22 |
| CYBER_ANALYST | 10 | 0 | 0 | 25 |
| CLOUD_ENGINEER | 10 | 0 | 0 | 25 |
| WEB_DEV | 11 | 0 | 0 | 24 |
| BUSINESS_ANALYST | 0 | 0 | 0 | 35 |
| FINANCIAL_ANALYST | 0 | 0 | 0 | 35 |
| HR_EXEC | 0 | 0 | 0 | 35 |
| MARKETING_EXEC | 0 | 0 | 0 | 35 |
| **Total** | **65** | **0** | **0** | **285** |

Every "other" JD is a US posting: 47 different states or "United States", led by "United States" (44), CA (31), TX (20), VA and NY (17 each). The LinkedIn file has only 2 non-US locations (Philippines) in 123,849 rows. None of the 285 drawn locations says "remote", although 58 of their texts mention remote work. So **the IT roles are about 30% Malaysian and 70% US, and the four Business roles are 100% US**. US postings use different titles (HR Generalist, Recruiter or HR Coordinator instead of HR Executive; Marketing Coordinator or Specialist instead of Marketing Executive) and mention US-specific items such as GAAP, SOX, FLSA, EEO statements and US benefits. Skill shares for the Business roles therefore describe the US market, not the Malaysian one, until Malaysian copies are added (see "Next steps").

## Sources and licences

| Source (`source`) | Site / dataset | JDs | `source_license` |
|---|---|---:|---|
| `manual` | JobStreet Malaysia (`my.jobstreet.com`) | 49 | Copied manually for non-commercial academic research |
| `manual` | Indeed Malaysia (`malaysia.indeed.com`) | 16 | Copied manually for non-commercial academic research |
| `kaggle:arshkon/linkedin-job-postings` | LinkedIn Job Postings (2023-2024), file `postings.csv` only | 285 | CC BY-SA 4.0 |
| `api:*` | none | 0 | Phase 6 collector not built yet |

- Each JD keeps its original posting URL in `source_url`: the JobStreet or Indeed URL for the manual copies, and the LinkedIn `job_posting_url` for the Kaggle rows.
- No web scraper was used by this project. The manual JDs were opened and copied by a person, and the Kaggle file was downloaded by hand from Kaggle on 2026-10-30.
- Raw files stay in `data/raw/` (git-ignored). Only the cleaned and anonymised text in `jd_dataset.csv` is committed.

**Collection period:** the manual JDs were copied on 2026-10-12. The Kaggle postings were listed on LinkedIn between 2023-12-05 and 2024-04-20, and their `collected_date` is the download date 2026-10-30.

## Kaggle file profile (`ingest_jds.py --profile`)

| Item | `postings.csv` |
|---|---|
| Size / rows | 517 MB, 123,849 postings (streamed, never loaded whole) |
| Columns used | `title`, `description`, `location`, `company_name` (employer key, then masked), `job_posting_url`, `formatted_experience_level` |
| Language | 99% of descriptions look English |
| Dates (`original_listed_time`) | 2023-12-05 to 2024-04-20 |
| Region | 123,847 US ("other"), 2 other APAC (Philippines), 0 Malaysia |
| Experience level | Mid-Senior 41,489 · Entry 36,708 · (blank) 29,409 · Associate 9,826 · Director 3,746 · Internship 1,449 · Executive 1,222 |

The other files of that Kaggle dataset (companies, salaries, skills and so on) are not used.

## Filters applied (ingest log, 2026-10-30)

| Step | Kaggle `postings.csv` |
|---|---:|
| Rows read | 123,849 |
| Title not one of the 10 roles | 114,370 |
| Senior / management title or level (Director, Executive) | 3,759 |
| Shorter than 300 characters after cleaning | 99 |
| Duplicate text (MD5 of normalised text) | 482 |
| **Candidates after filters** | **5,139** |
| Skipped by the per-employer cap (5 per employer per role) | 0 |
| Not drawn (per-role cap) | 4,854 |
| **Added** | **285** |

The 65 manual JDs were kept as they are, with their jd_refs, from the previous `jd_dataset.csv` (their raw files are not in this `data/raw/`). For their filter log see the Sprint 2 build of 2026-10-12: 65 read, 0 removed.

Candidates per role after the filters (entry or junior / mid): DA 461 (184 / 277), DS 234 (97 / 137), SD 989 (373 / 616), CY 455 (182 / 273), CE 420 (123 / 297), WD 351 (101 / 250), BA 497 (95 / 402), FA 276 (154 / 122), HR 934 (496 / 438), MK 522 (369 / 153). Every role had more entry or junior candidates than it needed, so no `mid` posting was drawn.

### Title rules (`jd_common.ROLE_TITLE_RULES`)

- **Business roles:** BUSINESS_ANALYST (business / business systems / business process analyst), FINANCIAL_ANALYST (financial or finance analyst, FP&A, financial planning analyst, financial reporting analyst, budget analyst), HR_EXEC (recruiter, talent acquisition, HR, HRIS, human resources, people operations) and MARKETING_EXEC (marketing coordinator, specialist, assistant, associate, intern or executive, digital marketing, social media, content marketing, SEO).
- **Order decisions:** "Business Intelligence Analyst" and "Business Data Analyst" stay DATA_ANALYST. "Financial Reporting Analyst" is FINANCIAL_ANALYST. "Financial Data Analyst" is deliberately DATA_ANALYST, because its head noun is "data analyst" and the work is SQL and BI on finance data, not budgeting or forecasting. Recruiter titles are checked before the IT rules ("Technical Recruiter - Cloud" is HR_EXEC). "HR Data Analyst" and "Marketing Data Analyst" stay DATA_ANALYST.
- **Fixed false positives:** the bare word "security" now counts only with an IT word in the title. In the Kaggle file it matched 1,584 titles before the fix, many of them guards ("Security Officer", "Armed Security Officer", "Security Guard"), while "Information System Security Officer" stays CYBER_ANALYST. The same context check applies to "front end", which US retail uses for the checkout area ("Retail Front End Supervisor"). The tail of a title after "for", "with" or "supporting", clearance wording ("with Security Clearance"), product names ("Salesforce Marketing Cloud", "Oracle Cloud"), places ("St Cloud") and pay rates ("$15hr") are ignored. Sales, volunteer and teaching titles, cyber-insurance titles, CNC or HVAC "programmers" and the "Online Data Analyst" search-rating gig are excluded. "Cybersecurity" written as one word now matches. Chief, AVP / SVP / EVP, president, leader, supervisor and "Mgr" are treated as senior.
- **Seniority:** title rules first. LinkedIn's `formatted_experience_level` only refines a plain title: Internship / Entry level → entry, Associate → junior, Director / Executive → senior (skipped), Mid-Senior → left to the title.
- Tricky titles are tested in `tests/test_jd_ingest.py`.

### Kaggle sampling

- **Per-role, per-file cap (`--cap`):** by default a Kaggle file adds what the role still needs to reach 30 JDs from the other sources, plus a margin of 5 (0 if the role already has 30). With 10 to 13 manual JDs, the IT roles took 22 to 25 and the Business roles took 35.
- **Draw:** after the seniority, length and duplicate filters, seeded with 42. Entry and junior postings come first, then Malaysia, then other APAC, then the rest. The Kaggle file had no Malaysian postings, so the region order did not change anything here.
- **Per-employer cap (`--employer-cap`, default 5):** the employer is the website domain if the file has one, otherwise `company_name` (then `company_id`), read before anonymisation. The 285 JDs come from 246 employers, with at most 4 from one employer in one role. The cap was never reached with this file, but it matters for files dominated by a few employers (for example the Techsalerator Malaysia file, about 94% Bosch and ZF).

### Stable jd_refs

The existing `jd_dataset.csv` is read first. Its rows keep their jd_ref and text even when their raw file is not present, and new JDs get the next number per role. The 65 jd_refs from Sprint 2 (and so `gold/gold_sample.csv`) are unchanged: all 65 rows are byte-identical to the committed version except for the new `region` column. Running `ingest_jds.py` twice on the same `data/raw/` produced byte-identical files (MD5 `d53359de…`). Both properties are tested in `tests/test_jd_ingest.py`.

## Anonymisation

| Rule | Effect on the 285 Kaggle JDs |
|---|---|
| Company names (the row's own `company_name`, its core form and its distinctive brand words such as "Apex" for "Apex Systems"), plus the manual company and alias lists → `[COMPANY]` | 1,046 replacements in 199 JDs, plus 4 titles |
| E-mail (also bare domains such as "@example.com") → `[EMAIL]` | 47 in 42 JDs |
| URL (also "https //…") and social handles ("@AcmeCorp") → `[URL]` | 47 in 34 JDs |
| Phone → `[PHONE]` | 21 in 16 JDs |
| `company` column | `Anonymised` for every row |

A final check of the Kaggle `raw_text` found no `http`/`www`, no runs of 8 or more digits and no "Sdn Bhd", "Berhad", "Pte Ltd" or "Pty Ltd". One `@` is left, in the phrase "<name> (Financial Analyst) @ [EMAIL]". The manual rows are unchanged from Sprint 2 (see that check in the Sprint 2 summary, which still holds).

## Attribution and licences

The 285 rows with `source = kaggle:arshkon/linkedin-job-postings` are adapted from:

> **LinkedIn Job Postings (2023-2024)** by **arshkon** on Kaggle, <https://www.kaggle.com/datasets/arshkon/linkedin-job-postings>, licensed under **CC BY-SA 4.0** (<https://creativecommons.org/licenses/by-sa/4.0/>). Only `postings.csv` was used.

- **Changes made:** 285 of the 123,849 postings were selected (title rules, seniority, length, de-duplication and a seeded, capped draw). Their text was cleaned: HTML was removed, the employer blurb was removed, e-mails, URLs, social handles, phone numbers and company names were replaced with placeholders, and whitespace was collapsed. The title was masked the same way, the company was set to "Anonymised", and `role_code`, `seniority` and `region` were added.
- **Licence of the adapted rows:** these rows are redistributed under the same licence, CC BY-SA 4.0, and every one of them carries `source_license = "CC BY-SA 4.0"`. Anyone who reuses them must keep the attribution above and share their adaptations under CC BY-SA 4.0.
- **Not affected:** the ShareAlike term covers this adapted posting text only. The code in this repository (`ingest_jds.py`, `jd_common.py`, the backend and so on) is a separate work and is not affected. The 65 manual rows are not from this dataset and keep their own `source_license`.
- The original postings were written by the employers. The dataset author published them on Kaggle under CC BY-SA 4.0, and this project relies on that licence.

**IEEE reference for the report:**

> [1] arshkon, "LinkedIn Job Postings (2023-2024)," Kaggle, 2024. [Online]. Available: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings. Licensed under CC BY-SA 4.0. [Accessed: Oct. 30, 2026].

## Derived files

| File | Contents |
|---|---|
| `jd_skill_frequency.csv` | 600 rows: share of each role's JDs that mention each library skill |
| `unmatched_terms.csv` | 300 frequent terms that no library skill or alias covers (spaCy noun chunks) |
| `role_skill_diff.csv` | 257 rows comparing suggested and current importance in `seed_job_role_skills.sql`. **For manual review only. The seed has not been changed.** |
| `gold/gold_sample.csv` | Unchanged: 60 of the 65 Sprint 2 JDs (10 per IT role, seed 42). It has no Kaggle and no Business rows. |
| `gold/gold_labels*.csv` | Unchanged |

## Known limitations

- **Region bias.** 285 of the 350 JDs (81%) are US LinkedIn postings, including all 140 Business-role JDs. Malaysian wording, qualifications (SPM, Diploma) and local tools are under-represented. See "Region mix" above.
- **Time gap.** The Kaggle postings date from December 2023 to April 2024, about 2.5 years older than the manual copies.
- **Residual personal data.** Contact person names (for example a recruiter's first name before "[EMAIL]") are not removed, because the pipeline has no name recogniser. Brand names of parent groups or partners that are not in `company_name` can also remain. Check before quoting any JD text.
- **Title noise.** Title rules are keywords, so a few postings at the edge of a role remain, such as "Grain Marketing Specialist" (commodity marketing) in MARKETING_EXEC.
- **Gold set.** The gold sample covers only the 6 IT roles and the manual JDs, so the Kaggle rows and the Business roles are not part of the Sprint 4 gold evaluation yet.

## Next steps

- No role is short of 30, so **no manual JobStreet copies are needed to reach the target** (0 for each of the 10 roles).
- To reduce the region bias, add about **10 Malaysian JobStreet copies for each Business role** (BUSINESS_ANALYST, FINANCIAL_ANALYST, HR_EXEC, MARKETING_EXEC), so they match the IT roles' 10 to 13 Malaysian JDs. Save them in `data/raw/manual/<ROLE_CODE>/` and re-run `ingest_jds.py`. They are added with new numbers, and the Kaggle rows stay as they are.
