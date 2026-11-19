# Cross-market check of the Job Readiness Score (F03)

Produced 2026-11-20 by `data/analysis/f03_cross_market.py` from `data/jd_dataset/` and the local database. Lecturer feedback F03 (Sprint 3 review, 12 November 2026): the readiness score should be usable internationally.

**Scope.** Only the six IT roles have job descriptions from two markets: Malaysia (JobStreet and Indeed, copied by hand) and the US (LinkedIn, via Kaggle). The four Business roles have US postings only and are not compared here; adding Malaysian Business JDs is part of F06.

## Summary

- **Skill demand differs between the markets.** The order of skills by demand agrees only moderately (Spearman ρ 0.28 to 0.53 across the six IT roles). Malaysian JDs ask more often for BI and visualisation tools, testing and monitoring, and self-motivation; US JDs more often for cloud and DevOps tools, Java, Agile and identity management (section 2).
- **The role templates cover both markets.** Each market's JDs name at least 79% of the template skills of every role (section 1), so the skill lists themselves are not market-specific.
- **The importance tiers are market-specific.** Each market alone would give the same tier to 32-45% of the template skills, but a tier within one step to 72-91% (section 3).
- **The score orders students much the same under either market's demands** for most roles: the lower of the two correlations (SEAGAS against the Malaysian-only and the US-only template) ranges 0.57 to 0.89; it is weaker for Data Analyst (US 0.65), Software Developer (Malaysia 0.57). (section 4)

**What it means for SEAGAS.** The scoring method (tiered coverage, 70 / 25 / 5, rule C) does not depend on the country, and the skill catalogue and role skill lists transfer. What does not transfer as it is, is which skills are required, preferred or bonus: that is a property of the local job market. For use outside Malaysia, a role template should keep its skills but take its tiers from local job descriptions (a per-market template), and the result should be checked again with more Malaysian JDs (F06) and with Business roles once Malaysian Business JDs exist.

## 1. Do the two markets ask for the same skills?

Share of JDs that name each skill, Malaysia against US; Spearman ρ over every skill seen in the role (95% bootstrap interval, 2000 resamples of the JDs within each market) and over the template skills only.

| Role | JDs MY / US | Skills per JD MY / US | ρ all skills [95% CI] | ρ template skills | Template skills asked in MY / US |
|---|---|---|---|---|---|
| Data Analyst | 11 / 24 | 12.8 / 12.2 | 0.52 [0.31, 0.57] | 0.50 | 28 / 30 of 31 |
| Data Scientist | 10 / 25 | 13.6 / 13.4 | 0.53 [0.29, 0.54] | 0.62 | 30 / 34 of 35 |
| Software Developer | 13 / 22 | 9.9 / 11.1 | 0.45 [0.18, 0.47] | 0.41 | 30 / 32 of 32 |
| Cybersecurity Analyst | 10 / 25 | 9.0 / 11.4 | 0.43 [0.20, 0.55] | 0.36 | 24 / 30 of 30 |
| Cloud Engineer | 10 / 25 | 12.2 / 14.5 | 0.28 [0.16, 0.44] | 0.41 | 27 / 34 of 34 |
| Web Developer | 11 / 24 | 11.5 / 13.5 | 0.53 [0.21, 0.62] | 0.34 | 33 / 35 of 36 |

## 2. Skills common in one market only

Skills whose share differs by at least 20 percentage points (up to five per side; MY % / US %).

| Role | More often in Malaysian JDs | More often in US JDs |
|---|---|---|
| Data Analyst | Statistical Analysis (82 / 12); Data Visualisation (91 / 46); Python (73 / 29); Excel (73 / 42); Power BI (55 / 25) | Leadership (0 / 38); Agile / Scrum (0 / 29); Azure (0 / 21); Business Analysis (9 / 29) |
| Data Scientist | Power BI (50 / 8); Self-Motivation (40 / 4); Cloud Computing (40 / 8); Data Visualisation (70 / 40); Critical Thinking (40 / 12) | Statistical Analysis (20 / 84); Data Structures & Algorithms (0 / 36); Decision Making (0 / 20); Natural Language Processing (0 / 20) |
| Software Developer | Software Testing (46 / 14); Critical Thinking (31 / 0); Project Management (46 / 18) | Node.js (0 / 32); Java (23 / 50); Recruitment (0 / 23); Python (23 / 45) |
| Cybersecurity Analyst | SIEM (70 / 16); Log Analysis (40 / 4); Incident Response (50 / 24); Firewall Management (40 / 20) | Azure (0 / 28); Identity & Access Management (0 / 28); Python (10 / 36); Risk Analysis (10 / 36); Communication (40 / 64) |
| Cloud Engineer | Critical Thinking (50 / 12); Problem Solving (80 / 44); Monitoring & Observability (50 / 24); Self-Motivation (30 / 4); Documentation (40 / 16) | DevOps (10 / 56); Java (0 / 40); Python (20 / 60); AWS (50 / 76); Git (10 / 36) |
| Web Developer | Vue.js (45 / 12); Self-Motivation (36 / 4); PHP (36 / 8); Documentation (45 / 21); JavaScript (91 / 67) | Angular (9 / 58); Agile / Scrum (9 / 50); CI/CD (18 / 50); Java (9 / 33); Spring Boot (0 / 21) |

## 3. Would each market give a template skill the same importance?

Tier each market alone would suggest (≥ 50% required, ≥ 20% preferred, ≥ 10% bonus, else below), for the skills of the SEAGAS template.

| Role | Same tier | Within one tier |
|---|---|---|
| Data Analyst | 14 of 31 (45%) | 23 of 31 (74%) |
| Data Scientist | 13 of 35 (37%) | 30 of 35 (86%) |
| Software Developer | 11 of 32 (34%) | 29 of 32 (91%) |
| Cybersecurity Analyst | 11 of 30 (37%) | 23 of 30 (77%) |
| Cloud Engineer | 11 of 34 (32%) | 28 of 34 (82%) |
| Web Developer | 16 of 36 (44%) | 26 of 36 (72%) |

## 4. Would students be ranked the same in either market?

Every student whose target role is the IT role (synthetic students), from their current skills with keyword matching. *SEAGAS*: readiness against the role template. *MY / US template*: readiness against a template built from that market's JDs only (rule of section 3). *JD fit*: share of that market's JDs the student covers (60% rule, `backend/jd_fit.py`).

| Role | Students | ρ SEAGAS vs MY template | ρ SEAGAS vs US template | ρ MY vs US template | ρ SEAGAS vs JD fit MY | ρ SEAGAS vs JD fit US | Mean readiness SEAGAS / MY / US |
|---|---:|---|---|---|---|---|---|
| Data Analyst | 908 | 0.96 | 0.65 | 0.78 | 0.87 | 0.77 | 53.2 / 48.8 / 44.6 |
| Data Scientist | 222 | 0.89 | 0.89 | 0.81 | 0.79 | 0.84 | 57.0 / 41.9 / 57.3 |
| Software Developer | 390 | 0.57 | 0.83 | 0.54 | 0.56 | 0.78 | 51.2 / 37.7 / 55.7 |
| Cybersecurity Analyst | 411 | 0.89 | 0.75 | 0.70 | 0.88 | 0.80 | 49.7 / 49.6 / 45.6 |
| Cloud Engineer | 428 | 0.86 | 0.80 | 0.82 | 0.56 | 0.81 | 49.7 / 36.7 / 41.5 |
| Web Developer | 975 | 0.90 | 0.89 | 0.93 | 0.80 | 0.78 | 51.6 / 56.6 / 40.6 |

## Limits

- Few Malaysian JDs per role (10-13), so the intervals are wide; one JD moves a share by 8-10 points.
- The bootstrap intervals sit mostly below the estimate: resampling repeats JDs, which adds noise to the shares and pulls a rank correlation down. Read them as a rough range, not an exact 95% interval.
- Some differences are extraction noise rather than demand, e.g. Recruitment in US Software Developer JDs comes from LinkedIn hiring boilerplate.
- US postings are longer and, for five of the six roles, name slightly more skills per JD (section 1), which raises US shares a little across the board. Spearman compares orders, not levels, so it is less affected than raw shares.
- Students are synthetic, generated from the same skill catalogue: section 4 shows whether the score orders the same profiles alike under both markets' demands, not how real students would fare.
- Business roles are not covered (US only).
- The skill sets come from SEAGAS's own extraction (`jd_skill_evidence.csv`), so extraction errors affect both markets the same way.
