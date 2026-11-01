# Role template retune: effect on readiness

Synthetic cohort, 5,000 students, each assessed against their own target role offline as `data/run_assessments.py` does: stored `evidence_type` plus `nlp.derive_evidence()`, `match_skills(method="hybrid")`, and the readiness weights of `backend/assessment_service.py` (required 3, preferred 2, bonus 1; Strong 1, Developing 0.5, Gap 0). Rules `2026-10-31`. Changes: `docs/report_drafts/role_template_retune.md`.

| Run | Cohort | Role templates | Skills library |
|---|---|---|---|
| before | `2026-10-28-business` (old) | before the retune (24.4 skills per role) | 166 skills |
| template | `2026-10-28-business` (old) | retuned (30.1 skills per role) | 172 skills (v4) |
| after | `2026-10-31-role-retune` (regenerated, seed 42) | retuned | 172 skills (v4) |

Advisor bands are the dashboard defaults: On Track at 70 or above, Needs Support below 40.

## Summary

| Run | Mean readiness | Median | Rows per student | Strong | Developing | Gap | On track | Needs support |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before | 50.2 | 51.9 | 24.4 | 38.1% | 13.1% | 48.9% | 19.4% | 31.6% |
| template | 43.5 | 44.2 | 30.5 | 30.7% | 13.4% | 55.9% | 6.4% | 40.9% |
| after | 45.7 | 46.7 | 30.5 | 33.4% | 13.8% | 52.8% | 10.5% | 37.2% |

- **Template effect** (same students, before → template): mean readiness 50.2 → 43.5 (-6.7). The old students were generated from the old templates, so they do not have the added skills: most added rows are Gaps.
- **Dashboard view** (before → after, what advisors see once the new data is loaded): 50.2 → 45.7 (-4.5). Strong on required rows is unchanged (56.4% → 56.9%); the drop comes from the template mix, explained below.

## Template effect: same students, old vs retuned templates

| Role | Students | Mean readiness | Δ | Strong / Developing / Gap (% of rows) | Required rows S / D / G | On track / Developing / Needs support (% of students) |
|---|---:|---:|---:|---|---|---|
| Data Analyst | 682 | 49.2 → 41.5 | -7.6 | 37.2 / 10.3 / 52.6 → 28.7 / 11.8 / 59.5 | 59 / 13 / 27 → 60 / 14 / 26 | 19 / 51 / 30 → 1 / 55 / 44 |
| Data Scientist | 412 | 49.1 → 39.6 | -9.5 | 37.2 / 10.3 / 52.5 → 29.0 / 10.6 / 60.4 | 59 / 11 / 30 → 59 / 12 / 29 | 17 / 50 / 33 → 1 / 49 / 50 |
| Software Developer | 827 | 49.5 → 42.6 | -6.9 | 39.2 / 11.1 / 49.7 → 31.0 / 11.4 / 57.6 | 57 / 13 / 30 → 57 / 12 / 31 | 18 / 49 / 34 → 6 / 53 / 42 |
| Cybersecurity Analyst | 426 | 49.4 → 46.5 | -2.9 | 35.6 / 18.2 / 46.2 → 32.7 / 17.2 / 50.1 | 51 / 23 / 26 → 51 / 23 / 26 | 19 / 48 / 33 → 13 / 51 / 35 |
| Cloud Engineer | 350 | 48.4 → 40.0 | -8.4 | 36.4 / 13.0 / 50.5 → 27.5 / 11.2 / 61.3 | 53 / 15 / 32 → 53 / 15 / 32 | 17 / 45 / 37 → 1 / 51 / 48 |
| Web Developer | 636 | 53.2 → 37.6 | -15.7 | 41.0 / 12.0 / 47.0 → 26.8 / 8.8 / 64.4 | 60 / 16 / 24 → 60 / 16 / 24 | 24 / 50 / 25 → 0 / 49 / 51 |
| Business Analyst | 417 | 53.6 → 51.7 | -1.8 | 40.1 / 14.5 / 45.3 → 36.5 / 19.8 / 43.7 | 57 / 17 / 26 → 55 / 16 / 29 | 26 / 47 / 27 → 18 / 56 / 26 |
| Financial Analyst | 417 | 46.3 → 46.2 | -0.1 | 35.9 / 11.1 / 53.0 → 33.7 / 16.1 / 50.2 | 55 / 14 / 31 → 56 / 12 / 32 | 11 / 51 / 38 → 9 / 54 / 36 |
| HR Executive | 416 | 49.9 → 46.3 | -3.6 | 39.6 / 13.1 / 47.4 → 34.2 / 16.3 / 49.4 | 53 / 12 / 34 → 53 / 12 / 34 | 20 / 46 / 35 → 12 / 49 / 39 |
| Marketing Executive | 417 | 53.0 → 47.9 | -5.1 | 36.5 / 20.9 / 42.6 → 33.8 / 20.9 / 45.2 | 55 / 21 / 24 → 55 / 25 / 20 | 22 / 52 / 26 → 10 / 59 / 31 |
| **All** | 5000 | 50.2 → 43.5 | -6.7 | 38.1 / 13.1 / 48.9 → 30.7 / 13.4 / 55.9 | 56 / 15 / 28 → 56 / 15 / 28 | 19 / 49 / 32 → 6 / 53 / 41 |

Status of the same students on the rows of the retuned template:

| Role | Kept at the same level | Moved one level | Added |
|---|---|---|---|
| Data Analyst | 21 rows, 37% Strong, 52% Gap | 1 rows, 55% Strong, 34% Gap | 9 rows, 7% Strong, 79% Gap |
| Data Scientist | 18 rows, 37% Strong, 53% Gap | 7 rows, 41% Strong, 47% Gap | 10 rows, 6% Strong, 83% Gap |
| Software Developer | 18 rows, 39% Strong, 51% Gap | 6 rows, 42% Strong, 44% Gap | 8 rows, 6% Strong, 83% Gap |
| Cybersecurity Analyst | 22 rows, 38% Strong, 43% Gap | 4 rows, 27% Strong, 66% Gap | 4 rows, 11% Strong, 74% Gap |
| Cloud Engineer | 21 rows, 39% Strong, 49% Gap | 3 rows, 26% Strong, 58% Gap | 10 rows, 5% Strong, 89% Gap |
| Web Developer | 20 rows, 43% Strong, 45% Gap | 2 rows, 34% Strong, 38% Gap | 14 rows, 2% Strong, 95% Gap |
| Business Analyst | 18 rows, 41% Strong, 43% Gap | 4 rows, 40% Strong, 50% Gap | 5 rows, 19% Strong, 41% Gap |
| Financial Analyst | 16 rows, 39% Strong, 50% Gap | 5 rows, 30% Strong, 55% Gap | 5 rows, 21% Strong, 46% Gap |
| HR Executive | 20 rows, 42% Strong, 43% Gap | 2 rows, 23% Strong, 73% Gap | 4 rows, 0% Strong, 69% Gap |
| Marketing Executive | 12 rows, 40% Strong, 33% Gap | 7 rows, 43% Strong, 41% Gap | 5 rows, 7% Strong, 80% Gap |

Rows kept at the same level score as before. Added rows are mostly Gaps, as expected for students generated without them; the six v4 skills cannot match at all for this cohort except through a related skill (Developing). Web Developer falls most (-15.7): its template gained 14 rows (Angular, AWS, Azure, C#, CI/CD, Java and others) that the old Web Developer students rarely have. Business Analyst and Financial Analyst hardly move: their added rows are mostly generic soft skills (Communication, Teamwork, Time Management), which the generator gives to students of every role.

## Dashboard view: old cohort and templates vs regenerated cohort and retuned templates

| Role | Students | Mean readiness | Δ | Strong / Developing / Gap (% of rows) | Required rows S / D / G | On track / Developing / Needs support (% of students) |
|---|---:|---:|---:|---|---|---|
| Data Analyst | 682 → 687 | 49.2 → 43.9 | -5.2 | 37.2 / 10.3 / 52.6 → 31.5 / 12.2 / 56.4 | 59 / 13 / 27 → 61 / 14 / 25 | 19 / 51 / 30 → 5 / 57 / 39 |
| Data Scientist | 412 → 443 | 49.1 → 41.5 | -7.6 | 37.2 / 10.3 / 52.5 → 31.3 / 11.0 / 57.7 | 59 / 11 / 30 → 60 / 12 / 28 | 17 / 50 / 33 → 5 / 49 / 46 |
| Software Developer | 827 → 789 | 49.5 → 43.1 | -6.4 | 39.2 / 11.1 / 49.7 → 32.8 / 11.9 / 55.3 | 57 / 13 / 30 → 56 / 13 / 31 | 18 / 49 / 34 → 8 / 50 / 42 |
| Cybersecurity Analyst | 426 → 410 | 49.4 → 47.9 | -1.5 | 35.6 / 18.2 / 46.2 → 34.6 / 16.9 / 48.5 | 51 / 23 / 26 → 53 / 21 / 26 | 19 / 48 / 33 → 12 / 52 / 35 |
| Cloud Engineer | 350 → 428 | 48.4 → 44.0 | -4.4 | 36.4 / 13.0 / 50.5 → 31.9 / 12.8 / 55.3 | 53 / 15 / 32 → 54 / 15 / 31 | 17 / 45 / 37 → 7 / 53 / 40 |
| Web Developer | 636 → 576 | 53.2 → 41.8 | -11.5 | 41.0 / 12.0 / 47.0 → 30.9 / 11.7 / 57.4 | 60 / 16 / 24 → 57 / 16 / 27 | 24 / 50 / 25 → 5 / 52 / 44 |
| Business Analyst | 417 | 53.6 → 53.9 | +0.3 | 40.1 / 14.5 / 45.3 → 38.6 / 19.0 / 42.4 | 57 / 17 / 26 → 57 / 16 / 27 | 26 / 47 / 27 → 26 / 47 / 27 |
| Financial Analyst | 417 | 46.3 → 47.6 | +1.3 | 35.9 / 11.1 / 53.0 → 35.8 / 15.0 / 49.2 | 55 / 14 / 31 → 57 / 11 / 31 | 11 / 51 / 38 → 12 / 55 / 32 |
| HR Executive | 416 | 49.9 → 49.4 | -0.5 | 39.6 / 13.1 / 47.4 → 37.3 / 16.0 / 46.7 | 53 / 12 / 34 → 55 / 12 / 33 | 20 / 46 / 35 → 16 / 52 / 32 |
| Marketing Executive | 417 | 53.0 → 49.4 | -3.6 | 36.5 / 20.9 / 42.6 → 36.1 / 19.0 / 44.9 | 55 / 21 / 24 → 58 / 23 / 19 | 22 / 52 / 26 → 16 / 56 / 28 |
| **All** | 5000 | 50.2 → 45.7 | -4.5 | 38.1 / 13.1 / 48.9 → 33.4 / 13.8 / 52.8 | 56 / 15 / 28 → 57 / 15 / 28 | 19 / 49 / 32 → 10 / 52 / 37 |

Why readiness is lower with the regenerated cohort although students cover their required skills as often as before: the generator gives each required skill with probability p_core (0.75 / 0.55 / 0.28 for strong / average / weak students) and each preferred or bonus skill with p_sec (0.30 / 0.15 / 0.06). The retune moved weight from required to preferred rows:

| Rows | Before: per student | Strong | After (regenerated): per student | Strong |
|---|---:|---:|---:|---:|
| required | 9.3 | 56.4% | 8.1 | 56.9% |
| preferred | 8.3 | 28.4% | 13.4 | 26.1% |
| bonus | 6.8 | 24.6% | 9.0 | 23.2% |

Required rows carried 54% of the readiness weight before and 41% after. Preferred and bonus rows are Strong far less often, so the weighted mean falls by about 4.5 points. The readiness of a real student changes in the same direction only where the retuned template asks for skills they have not listed.

## Notes

- Regenerating with seed 42 changes every synthetic student (names, roles, archetypes, skills), because the number of random draws depends on the template sizes. Per-role student counts therefore differ between the old and regenerated cohorts.
- The advisor thresholds (70 / 40) were not changed. With the retuned templates fewer synthetic students are On Track; whether the thresholds should follow is a product decision, not part of this retune.
- `before` reproduces `evidence_effect.md` (stored scenario, mean readiness 50.21), so the offline assessment matches the earlier experiment.
- Numbers per role and run: `role_retune_effect.csv`.
