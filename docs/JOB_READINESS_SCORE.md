# Job Readiness Score: formula and justification

**Owner:** Soh Way Miin (Carl), with Ng Yong Hin for the match statuses and the tiered
formula · **Code:** `backend/readiness.py`, `backend/assessment_service.py` · **Statuses:**
`nlp/matcher.py`, rules in [`NLP_CLASSIFICATION_RULES.md`](NLP_CLASSIFICATION_RULES.md) ·
**Sensitivity script:** `data/jrs_sensitivity.py` · **Status (5 November 2026):** tiered
formula implemented; written up after the lecturer meeting of 22 October asked us to
research and justify the formula.

The Job Readiness Score answers one question: *of the skills this job asks for, how
much does the student's profile show, counting the important ones more?* It is a
decision-support indicator for students and advisors, not a hiring prediction. Every
point in it can be traced to the job's skills and the reason stored for each.

## 1. Formula

For one assessment (a student against a role template or an analysed job description),
every skill the job asks for belongs to one importance tier and has one status credit:

| Importance tier (from the role template or JD) | Tier weight | | Status (from the matcher) | Credit |
|---|---:|---|---|---:|
| required | 0.70 | | Strong | 1.0 |
| preferred | 0.25 | | Developing | 0.5 |
| bonus | 0.05 | | Gap | 0 |

The coverage *C* of a tier is the mean credit of that tier's skills. Then:

**Readiness = 100 × (0.70 C_required + 0.25 C_preferred + 0.05 C_bonus) / (sum of the
weights of the tiers this job has)**, rounded to 2 decimals (0 to 100).

A tier the job does not have drops out of both the top and the bottom. A job with no
skills scores 0. A missing importance counts as required.

The statuses come from the decision table in `NLP_CLASSIFICATION_RULES.md`: Strong is
the same skill at intermediate / advanced level, or at beginner level with a project,
certification or internship behind it; Developing is a beginner skill without that
evidence, or a different but similar / related skill; Gap is nothing close enough.

**Worked example** (the `match_skills` example in `NLP_INTERFACE.md`):

| Skill | Importance | Status | Credit |
|---|---|---|---:|
| SQL | required | Strong | 1.0 |
| Python | required | Developing | 0.5 |
| Power BI | required | Gap | 0 |
| Azure | preferred | Developing | 0.5 |
| Docker | bonus | Gap | 0 |

C_required = 1.5 / 3 = 0.5, C_preferred = 0.5 and C_bonus = 0, and all three tiers are
present, so readiness = 100 × (0.70 × 0.5 + 0.25 × 0.5 + 0.05 × 0) / 1.00 = **47.5**. With
only the three required rows, as when a pasted job description has no other tier,
readiness = 100 × (0.70 × 0.5) / 0.70 = **50.0**.

**What this means, and what it does not.**

- If every required skill is Strong, the score is at least 70 whenever the job has
  required skills and other tiers, and 100 when it has only required skills. With every
  other skill a Gap the score is exactly 70 when all three tiers are present, 73.68 with
  required and preferred only, and 93.33 with required and bonus only.
- It does **not** follow that On Track (≥ 70) means all required skills are met, because
  preferred and bonus also score. With every preferred and bonus skill Strong, a job with
  all three tiers reaches 70 at a required coverage of 0.57. In the synthetic cohort of
  section 2.4, 862 of the 1,319 On Track students do not have all their required skills
  Strong, and 530 of those have a required skill at Gap. Read the required rows on the
  Skill Gap page, not the band alone.

## 2. Why this formula

### 2.1 Weighted coverage of the job's requirements

The score is a weighted share of the job's own requirements, so it changes with the
job: the same student can be 80% ready for Data Analyst and 40% for Cloud Engineer, which
is what a skill-gap tool should show. It also keeps the score explainable, a requirement
in our Team and Project Plan: the Skill Gap page lists each required skill with its
status and the reason, and the advisor sees the same rows. A model that learns a score
from data would need labelled hiring outcomes, which a proof of concept with synthetic
students does not have.

### 2.2 Tier weights 70 / 25 / 5

Job descriptions separate must-have from nice-to-have requirements, and the role
templates and JD analysis keep that as required / preferred / bonus. Each tier is scored
on its own coverage, so the share of the score that a tier carries is fixed by its weight
and not by how many skills the template lists: required skills carry 70% of the score
whether a role has 6 of them or 10, next to 8 or 17 preferred skills. Preferred and bonus
still count, so that going beyond the minimum shows in the score, but they cannot
outweigh the required skills.

The weights do not make every skill worth the same across roles. One required skill is
worth 70 / 10 = 7 points in a role with 10 required skills and 70 / 6 = 11.67 in a role
with 6, and one bonus skill is worth 5 / 13 = 0.38 points in a role with 13. The values
70 / 25 / 5 are a design choice (section 5). Section 2.4 compares them with other splits.

### 2.3 Developing = half credit

Developing covers two cases that are both "part of the way there": the right skill at
beginner level without project, certification or internship evidence, and a different
skill that is similar or related (for example MySQL for PostgreSQL). Half credit is the
neutral choice between "has it" and "does not have it"; the statuses are ordered
categories, not measurements, so we did not try to be more precise than that.

### 2.4 Sensitivity: the choice of weights does not change who is ahead

`data/jrs_sensitivity.py` re-scores the latest role-template assessment of every
student (5,000 assessments, 153,275 skill rows) with other weights and credits and
compares them with the current scheme:

| Scheme | Mean | Spearman ρ vs current | Students changing band (70 / 40) |
|---|---:|---:|---:|
| **current tiers 70/25/5, developing 0.5** | 53.5 | 1.000 | 0 (0.0%) |
| old points 3/2/1, developing 0.5 | 44.5 | 0.964 | 1,448 (29.0%) |
| tiers 75/20/5, developing 0.5 | 54.9 | 0.999 | 229 (4.6%) |
| tiers 60/30/10, developing 0.5 | 50.3 | 0.997 | 482 (9.6%) |
| tiers 50/35/15, developing 0.5 | 47.1 | 0.988 | 1,046 (20.9%) |
| tiers 70/25/5, developing 0.25 | 49.6 | 0.994 | 497 (9.9%) |
| tiers 70/25/5, developing 0.75 | 57.4 | 0.992 | 580 (11.6%) |
| required skills only | 62.4 | 0.982 | 1,197 (23.9%) |

The order of the students hardly changes among the tier schemes (ρ ≥ 0.988), so
comparisons between students do not depend much on the exact split. What the weights do
change is the level of the score, and therefore which band a student near a boundary
falls into: from 4.6% of students for 75/20/5 to 20.9% for 50/35/15. Ignoring preferred
and bonus skills would move 24% of students between bands, so we keep them. This shows
that the score is stable, not that the weights are right. Measured on the local database
on 5 November 2026, after `python data/run_assessments.py --auto` re-assessed the
synthetic students. The statuses are those of the rules of 31 October: only 3 of the
153,275 rows differ from the assessments before that run, all for one student whose
latest assessment had been a keyword run.

### 2.5 Readiness bands 70 / 40

The advisor dashboard groups students as On Track (≥ 70), Developing (40 to 69) and
Needs Support (< 40). These values did not change with the formula. On the representative
synthetic students in `NLP_CLASSIFICATION_RULES.md` section 6, across roles and methods,
the strong students average about 75 to 81, the average ones 51 to 60 and the weak ones
24 to 32. So 70 lies just below the strong students and 40 lies between average and weak.
With the current scheme the 5,000 latest assessments split 1,319 / 2,300 / 1,381 (26.4% /
46.0% / 27.6%); with the old points on the same statuses they split 488 / 2,520 / 1,992.

By archetype (`data/output/students_meta.csv`), 76.8% of strong students are On Track,
below the proposal's target of at least 80%, and 78.9% of weak students are Needs Support,
above its target of at least 75%. The weights were not tuned to reach the first target.
Part of the shortfall comes from the data: `database/migrate_existing_db.sql` moves 620 ICT
students to a role offered to their course (Software Developer to Web Developer, Data
Scientist to Data Analyst), while their skills were generated for the old role. Among
strong students, 85.6% of the 1,068 who kept their role are On Track and 12.9% of the 147
who were moved. Because the right boundaries depend on the institution, admins can change
both values in **Admin → System Settings**.

### 2.6 Why the formula changed (November 2026)

Until 5 November 2026 readiness was 100 × Σ (weight × credit) / Σ weight over all of a
role's skills, with weights required 3, preferred 2, bonus 1. All tiers shared one
denominator, so the score fell as a template got longer. After the role retune of 31
October, required skills were 27% of the template rows and 41% of the weight. A student
with every required skill Strong and everything else Gap scored only 29 to 55 depending
on the role. The same students moved to the new templates lost 6.7 points on average and
15.7 for Web Developer without any change in their skills
(`nlp/experiments/results/role_retune_effect.md`).

On the same statuses the new formula raises the mean from 44.5 to 53.5. The score rises
for most students, but 309 score lower (by at most 8.99 points): those who cover
preferred and bonus skills better than required ones. Of the 1,448 students who change
band, 832 move from Developing to On Track, 613 from Needs Support to Developing, 2 from
Developing to Needs Support and 1 from On Track to Developing.

Assessments stored before this date keep the score they were given, so a student's
history can show a step that comes from the formula and not from their skills. Committed
results of earlier experiments under `nlp/experiments/results/` use the old formula.

## 3. The seven dimensions

Each assessment also stores seven dimension scores. The Dashboard, the Skill Gap page and the
advisor's student page show the four skill dimensions as bars. The three experience dimensions
are stored but not shown as a percentage: those pages list up to three of the student's records
instead, because "75% project experience" says less than the projects themselves.

The four skill dimensions **stay on points of 3 / 2 / 1**: 100 × Σ (weight × credit) / Σ
weight over the job's skills of that category, with required 3, preferred 2, bonus 1 and
the credits of section 1. This is a known inconsistency with the overall score, which uses
tiers: the same skill counts differently in a bar and in the overall score, and the overall
score is not an average of the bars. On the 5,000 latest assessments the overall score
averages 53.5 while the bars average 47.3 (Technical), 45.7 (AI / Digital), 41.3
(Analytical) and 35.7 (Soft), and for 1,272 students it is above all four bars. We accept
this for now because a bar covers one category, where a tier may hold a single skill or
none, so tier weights would let one skill move a bar by up to 70 points. The Skill Gap page
and "How is this calculated?" tell students that the two count differently.

| Dimension | Column | How it is worked out | In the readiness score? |
|---|---|---|---|
| Technical Skills | `score_technical` | Points of 3 / 2 / 1 over the job's Technical skills only | Yes (its skills) |
| AI / Digital Skills | `score_ai_digital` | The same, AI_Digital skills | Yes (its skills) |
| Analytical Skills | `score_analytical` | The same, Analytical skills | Yes (its skills) |
| Soft Skills | `score_communication` | The same, Soft skills | Yes (its skills) |
| Project Experience | `score_project_exp` | 25 per project, at most 100 | No |
| Certification | `score_certification` | 33 per certification, at most 100 | No |
| Industry Experience | `score_industry_exp` | 50 per internship project or work experience (not volunteering), at most 100 | No |

The three experience dimensions are not added to the readiness score, for two reasons.
First, projects, certifications and internships already raise the matching skills to
Strong (rule C and the derived evidence of 30 October), so adding them again would count
the same evidence twice. Second, they describe the profile, not the job: the same three
values appear for every job, while the readiness score is meant to compare the student
with one job.

### 3.1 Zero, "Not required" and "No data yet"

The lecturer asked how a zero should be read when it may mean missing information
rather than a lack of skill. Since 1 November the pages show three cases differently
(`frontend/src/utils/dimensions.js`):

| Shown as | When | Meaning |
|---|---|---|
| **Not required** | The skill dimension is NULL | The job asks for no skill of this category, so there is nothing to score |
| **No data yet** | A skill dimension is 0 and the student lists no skill of that category | Nothing is recorded in the profile yet; the student is told what to add |
| **0%** | A skill dimension is 0 while the student does list skills of that category | A real result: none of the listed skills is close to what the job asks for |

The readiness score itself has no "no data" case: a profile with no skills cannot be
assessed (the assessment asks the student to add a skill first).

## 4. Link to the Malaysian Qualifications Framework (preliminary)

The lecturer also suggested aligning the skill categories with MQF 2.0 (Malaysian
Qualifications Agency). MQF 2.0 describes learning outcomes in five clusters: knowledge
and understanding; cognitive skills; functional work skills (practical, interpersonal,
communication, digital and numeracy skills, and leadership, autonomy and responsibility);
personal and entrepreneurial skills; and ethics and professionalism. A first mapping of
our categories:

| SEAGAS category | Closest MQF 2.0 cluster |
|---|---|
| Technical | Knowledge and understanding; functional work skills (practical skills) |
| AI / Digital | Functional work skills (digital skills) |
| Analytical | Cognitive skills; functional work skills (numeracy skills) |
| Soft | Functional work skills (interpersonal, communication, leadership); personal and entrepreneurial skills; ethics and professionalism |

This mapping has not been checked against the MQF document skill by skill yet; that is
part of the research work still to do (see section 5).

## 5. Limitations and what is still to be validated

- **The weights 70 / 25 / 5 are a design choice, not learned.** Section 2.4 shows the
  ranking is stable, but the absolute level has not been checked against employers'
  judgement. The check of the weights with advisors (AHP) is still to do, and there is no
  industry validation: there is no industry partner yet to do this.
- **On Track does not mean all required skills are met** (section 1).
- **Skill levels are self-reported.** Evidence from projects and certifications helps,
  but a student can still overstate a level.
- **Every skill of one tier counts the same.** SQL and Git count the same when both are
  required, even if an employer cares more about one of them. A skill's worth also
  depends on how many skills share its tier (section 2.2).
- **Scores before and after 5 November 2026 are not comparable** (section 2.6).
- **The dimensions and the overall score count differently** (section 3).
- **Synthetic data.** The figures in sections 2.4 and 2.5 come from synthetic students;
  the planned evaluation with 25 UAD students and the SUS test will be the first check
  with real users.
- **MQF mapping and Malaysian competency surveys** (section 4) are still to be
  researched in detail.

## 6. Where it is in the code

| What | Where |
|---|---|
| Tier weights, credits, formula | `backend/readiness.py` (`TIER_WEIGHTS`, `STATUS_CREDIT`, `tier_coverage`, `tiered_readiness`) |
| Dimensions (points of 3 / 2 / 1) | `backend/assessment_service.py` (`IMPORTANCE_WEIGHTS`, `weighted`, `category_score`) |
| Strong / Developing / Gap | `nlp/matcher.py`, `docs/NLP_CLASSIFICATION_RULES.md` |
| Evidence from projects and certifications | `nlp/evidence.py` |
| Readiness bands | `backend/settings.py` (`readiness_on_track`, `readiness_needs_support`), Admin → System Settings |
| "Not required" / "No data yet" | `frontend/src/utils/dimensions.js`, `frontend/src/components/DimensionBar.jsx` |
| Sensitivity analysis | `data/jrs_sensitivity.py` |
| Tests | `tests/test_readiness.py`, `tests/test_backend_api.py` (`TestAssessment`), `nlp/tests/test_matcher.py` |
