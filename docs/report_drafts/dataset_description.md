# Dataset Description (draft)

> Draft for the SEAGAS final report, Sprint 2. Author: Ng Yong Hin.
> All figures come from generated files: `data/skills/skills_library.csv`,
> `data/output/summary_stats.txt` and `data/output/students_meta.csv` (seed 42, generated 2026-09-29).
> Re-check the figures if these files are regenerated.

SEAGAS uses three datasets: (1) a curated **skills library** that serves as the controlled vocabulary for all matching, (2) a **synthetic student dataset** for development, testing and the Advisor Dashboard, and (3) a **job-description (JD) dataset** for validating role templates and evaluating skill extraction. No real student data is used at any stage.

## 1. Skills Library

The skills library is the reference taxonomy. Student skills, job-role templates and skills extracted from JDs are all mapped onto it. Version 2 has **138 skills**: the 32 seed skills from the database schema (v1) and 106 skills added in Sprint 2. The library is kept in a single CSV source file. A build script checks the file and generates both the database seed and a JSON taxonomy for the NLP module. This keeps the database and the NLP module consistent.

Each skill has a canonical name, one of four top-level categories (matching the database constraint and the assessment dimensions), a finer subcategory, a list of aliases, a list of *ambiguous* aliases, and a one-sentence description.

**Table 1. Skills library v2 by category and subcategory**

| Category | Subcategory (count) | Total |
|---|---|---|
| Technical | Programming Language (15), Data & BI (14), Security Practice (14), Security Tool (11), Web Framework (9), DevOps (7), Database (5), Software Engineering (4), Web Development (4), Infrastructure (3), Design (2) | 88 |
| AI_Digital | ML/AI (15), Cloud (5), Data & BI (1) | 21 |
| Analytical | Analytical (14), Data & BI (1) | 15 |
| Soft | Soft (14) | 14 |
| **Total** | | **138** |

The library has 356 aliases (for example "Postgres" → *PostgreSQL*, "pen testing" → *Ethical Hacking*) and 30 ambiguous aliases. Ambiguous aliases are short or everyday terms that often produce false matches in JDs, such as "CV" (usually a résumé, not Computer Vision), "R", "Go", "Excel" ("excel in…"), "REST" ("the rest of…") and "Shell" (also a major employer in Malaysia). They are kept out of the database and excluded from baseline keyword matching. Automated tests enforce four constraints: skill names are unique, every alias belongs to exactly one skill, no alias equals another skill's name, and all 32 v1 skills are present with unchanged names. The v1 names must stay unchanged because job-role templates and learning resources reference them.

Two design decisions affect the assessment dimensions. First, each domain is placed in a single category, so that a dimension score keeps one meaning: all security practices and tools are *Technical*, and all cloud-platform skills are *AI_Digital*. Second, practices that JDs often list separately from their umbrella skill were split out as their own skills. Examples are *Agile / Scrum* (previously an alias of Project Management), and *MySQL* and *PostgreSQL* (previously aliases of SQL).

## 2. Synthetic Student Dataset

### 2.1 Rationale

Real student records are personal data under Malaysia's Personal Data Protection Act 2010 [1]. They were also not available during development. We therefore generated a synthetic population that matches the database schema exactly. This lets the team build and test profile management, gap analysis and the Advisor Dashboard without privacy risk.

### 2.2 Generation method

The generator (`data/generate_synthetic_data.py`) creates **5,000 students** with a fixed random seed (42). The output is byte-for-byte reproducible, including UUIDs and password hashes. Each student is assigned:

- a **target role**, one of the six job roles, weighted towards the more common graduate roles;
- an **archetype** (strong 25%, average 50%, weak 25%). The archetype controls the probability of holding the role's core and secondary skills, the GPA distribution, the number of projects and certifications, and the chance of an internship;
- **skills**, sampled from the role template. *Core* skills are the role's `required` skills in `job_role_skills`, and *secondary* skills are its `preferred` and `bonus` skills. The generator reads these lists directly from the role-mapping seed, so the synthetic ground truth cannot drift from the templates used for scoring. Each student also gets up to two random off-role skills from the whole library as noise;
- **consistent evidence**. Skills used in a generated project are tagged `project`, and skills covered by a certification are tagged `certification`. The certifications are 25 real industry certificates, such as CompTIA Security+, CCNA, AWS Solutions Architect – Associate and Google Data Analytics. Profile counters (`project_count`, `certification_count`, `internship_count`) equal the rows in the detail tables;
- a **proficiency** level, which depends on archetype, year of study and whether the skill has evidence beyond coursework;
- **romanised Malaysian names** (Chinese, Malay and Indian, plus a few international names), and e-mail addresses under the reserved `example.com` domain [2]. All accounts share one demo password, stored as a bcrypt hash [3].

### 2.3 Resulting distribution

**Table 2. Synthetic dataset summary (seed 42)**

| Measure | Value |
|---|---|
| Students | 5,000 |
| Student–skill entries | 78,327 (mean 15.7 per student; min 1, max 36) |
| Projects / certifications | 8,814 / 4,060 |
| GPA | mean 2.99 (range 2.00–4.00) |
| Target role | Software Developer 25.2%, Data Analyst 20.3%, Web Developer 18.9%, Data Scientist 12.5%, Cybersecurity Analyst 12.5%, Cloud Engineer 10.6% |
| Archetype | average 48.9%, weak 26.5%, strong 24.6% |
| Year of study | Y1 15.6%, Y2 29.3%, Y3 35.2%, Y4 19.8% |
| Internships | none 71.2%, one 26.5%, two 2.3% |
| Proficiency | intermediate 52.9%, advanced 27.0%, beginner 20.1% |
| Library coverage | all 138 skills are held by at least one student |

The archetypes produce clearly separated readiness levels. Mean core-skill coverage is **89.8%** for strong students, **71.6%** for average students and **39.7%** for weak students. Per role, mean coverage is between 64.4% (Cloud Engineer) and 69.2% (Web Developer). This spread lets the Advisor Dashboard and readiness scoring be tested across the full range. The per-student archetype and coverage are stored in `students_meta.csv`, which is not loaded into the database. This file serves as ground truth for checking that computed readiness scores rank students sensibly.

### 2.4 Limitations

The distributions are designed, not observed. The archetype shares, skill probabilities and role weights are plausible assumptions, not measurements of real INTI or Swinburne cohorts. Skills are sampled independently within a role, so real co-occurrence patterns (for example Pandas almost always appearing with Python) are only partly captured, mainly through the project templates. Results obtained on this dataset show that the system behaves consistently. They do not measure how accurate it is for real students.

## 3. Job-Description Dataset

### 3.1 Purpose and sources

The JD dataset has three uses: (a) validating each role template against market demand, (b) finding skills missing from the library, and (c) evaluating the L1 (keyword) and L2 (semantic) extractors in Sprint 4. Sources are, in order of preference:

1. public Kaggle job-posting datasets, each used only after its licence is checked and recorded;
2. postings copied by hand from JobStreet Malaysia, LinkedIn and company career pages, with the source URL and collection date;
3. (planned, Phase 6) public job-board APIs such as Greenhouse, whose job-board API is designed for public use [4].

Automated scraping of job portals is excluded because it breaches their terms of service.

The target is at least 30 JDs per role (180 in total), and ideally 50–100 per role.

> **[TO COMPLETE once raw data is collected]** Final counts per role and per source, the licence of each Kaggle dataset, the collection period, and the share of entry / junior / mid postings.

### 3.2 Cleaning and anonymisation

`ingest_jds.py` processes each posting in these steps:

1. Map the title to one of the six roles using ordered keyword rules. Titles that match none of the roles are dropped.
2. Drop senior and management postings, since SEAGAS targets graduates.
3. Strip HTML.
4. Replace e-mail addresses, URLs, phone numbers and company names with placeholders. Company names include every name seen in the batch and any "… Sdn Bhd / Berhad / Pte Ltd" pattern.
5. Collapse whitespace.
6. Drop texts shorter than 300 characters.
7. Remove duplicates using a hash of the normalised text.

The company field is always stored as "Anonymised". Raw files stay outside version control.

### 3.3 Frequency analysis

A keyword baseline counts the share of each role's JDs that mention each library skill. It uses word-boundary matching, keeps the longest match when matches overlap, and ignores ambiguous aliases. From this share it suggests an importance level: required if at least 50% of the role's JDs mention the skill, preferred for 20–50%, and bonus for 10–20%. The suggestions are compared with the current role templates, but the templates are only changed after manual review. Frequent terms that the library does not cover are listed as candidates for new skills.

### 3.4 Gold annotation set

For the Sprint 4 evaluation, 60 JDs (10 per role, fixed seed) are sampled for manual annotation, following a one-page guideline (`data/jd_dataset/gold/ANNOTATION_GUIDE.md`). The labels must be produced by a person, not by the system under evaluation. A keyword pre-fill is provided only to reduce typing, and every row is checked by hand. If time allows, a second annotator labels a subset, and inter-annotator agreement is reported with Cohen's κ [5].

## 4. Ethical Considerations

- **No real student data.** All student profiles are synthetic. The e-mail addresses use a reserved domain [2], so no real person can be contacted or identified.
- **Anonymised JDs.** Company names and contact details are removed from JD text. Only the cleaned dataset is committed, and raw postings stay local.
- **Respect for data sources.** Only datasets with a recorded licence, hand-copied postings used for non-commercial academic research, and (later) officially provided public APIs are used. Scraping is excluded.
- **Bias.** The JD sample reflects the postings that are publicly visible during the collection window. It may over-represent large employers, Klang Valley locations and English-language postings. International API postings (Phase 6) may not reflect the Malaysian market. The synthetic students reflect the designers' assumptions. These limitations are reported alongside all results.

## References

[1] *Personal Data Protection Act 2010 (Act 709)*, Laws of Malaysia, 2010.

[2] D. Eastlake 3rd and A. Panitz, "Reserved Top Level DNS Names," IETF, RFC 2606, Jun. 1999.

[3] N. Provos and D. Mazières, "A future-adaptable password scheme," in *Proc. USENIX Annual Technical Conference, FREENIX Track*, Monterey, CA, USA, 1999, pp. 81–91.

[4] Greenhouse Software, "Job Board API," Greenhouse Developer Documentation. [Online]. Available: https://developers.greenhouse.io/job-board.html

[5] J. Cohen, "A coefficient of agreement for nominal scales," *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960.
