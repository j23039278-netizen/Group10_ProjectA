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
  section 2.4, 969 of the 1,484 On Track students do not have all their required skills
  Strong, and 567 of those have a required skill at Gap. Read the required rows on the
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
| **current tiers 70/25/5, developing 0.5** | 55.5 | 1.000 | 0 (0.0%) |
| old points 3/2/1, developing 0.5 | 45.9 | 0.960 | 1,584 (31.7%) |
| tiers 75/20/5, developing 0.5 | 57.0 | 0.999 | 246 (4.9%) |
| tiers 60/30/10, developing 0.5 | 52.1 | 0.997 | 522 (10.4%) |
| tiers 50/35/15, developing 0.5 | 48.7 | 0.987 | 1,126 (22.5%) |
| tiers 70/25/5, developing 0.25 | 51.6 | 0.994 | 514 (10.3%) |
| tiers 70/25/5, developing 0.75 | 59.4 | 0.992 | 580 (11.6%) |
| required skills only | 65.0 | 0.979 | 1,247 (24.9%) |

The order of the students hardly changes among the tier schemes (ρ ≥ 0.987), so
comparisons between students do not depend much on the exact split. What the weights do
change is the level of the score, and therefore which band a student near a boundary
falls into: from 4.9% of students for 75/20/5 to 22.5% for 50/35/15. Ignoring preferred
and bonus skills would move 25% of students between bands, so we keep them. This shows
that the score is stable, not that the weights are right. Measured on 5 November 2026 on
a copy of the local database, reloaded with the synthetic data version
`2026-11-05-ict-roles` and re-assessed with `python data/run_assessments.py` (hybrid). The
statuses are those of the rules of 31 October.

### 2.5 Who needs support: status by year of study and recent activity

Sprint 3 feedback: a low score alone does not mean a student needs the advisor. A new
Year 1 student naturally lists few skills, so under a single 40% limit almost every first-
year student was shown as Needs Support, and the students who really needed help were
hidden among them. Since 12 November 2026 the advisor dashboard status
(`backend/student_status.py`) compares the latest score with what is expected for the
student's year of study, and keeps Needs Support for students who are also not active:

| Status | Rule |
|---|---|
| On Track | score ≥ the year's On Track level |
| Developing | between the year's two levels |
| Getting Started | below the lower level, a Year 1 student whose account is younger than 120 days |
| Improving | below the lower level, but an activity was saved, started or completed in the last 30 days, or the score went up at an assessment in that time |
| Needs Support | below the lower level, not a new Year 1 student and not active in the last 30 days |
| Not Assessed | no assessment yet |

| Year of study | On Track from | Below expected under |
|---|---|---|
| Year 1 | 45 | 20 |
| Year 2 | 55 | 30 |
| Year 3 | 65 | 35 |
| Year 4 and above, or not set | 70 | 40 (section 2.6) |

The year levels are a starting point for the institution to adjust; all of them, the 30-day
window and the 120-day new-student period are System Settings (`year_expectations`,
`support_active_days`, `new_student_days`). On the current data (5,012 students) Needs
Support falls from 1,221 to 776 students, and in Year 1 from 275 to 27; 76 new Year 1
students are Getting Started. The score itself does not change, only how the dashboard
reads it, and each student's status comes with its reason so the advisor can check it.

### 2.6 Readiness bands 70 / 40

The advisor dashboard groups students as On Track (≥ 70), Developing (40 to 69) and
Needs Support (< 40). These values did not change with the formula. On the representative
synthetic students in `NLP_CLASSIFICATION_RULES.md` section 6, across roles and methods,
the strong students average about 75 to 81, the average ones 51 to 60 and the weak ones
24 to 31. So 70 lies just below the strong students and 40 lies between average and weak.
With the current scheme the 5,000 latest assessments split 1,484 / 2,296 / 1,220 (29.7% /
45.9% / 24.4%); with the old points on the same statuses they split 514 / 2,658 / 1,828.

By archetype (`data/output/students_meta.csv`), 85.3% of strong students are On Track,
above the proposal's target of at least 80%, and 76.9% of weak students are Needs Support,
above its target of at least 75%. The weights were not tuned to reach these targets. Before
the data version `2026-11-05-ict-roles` the figures were 76.8% and 78.9%, and the first
missed its target because of the data: `database/migrate_existing_db.sql` moved 620 ICT
students to a role offered to their course (Software Developer to Web Developer, Data
Scientist to Data Analyst), while their skills stayed generated for the old role. The
generator now gives these students the ICT role from the start. Of the 147 strong students
among them, 83.0% are now On Track (12.9% before); the other 1,068 strong students did not
change (85.6%). Both targets are met on synthetic students, so this shows that the bands
separate the generated archetypes, not that they fit real students (section 5). Because
the right boundaries depend on the institution, admins can change both values in
**Admin → System Settings**.

### 2.6 Why the formula changed (November 2026)

Until 5 November 2026 readiness was 100 × Σ (weight × credit) / Σ weight over all of a
role's skills, with weights required 3, preferred 2, bonus 1. All tiers shared one
denominator, so the score fell as a template got longer. After the role retune of 31
October, required skills were 27% of the template rows and 41% of the weight. A student
with every required skill Strong and everything else Gap scored only 29 to 55 depending
on the role. The same students moved to the new templates lost 6.7 points on average and
15.7 for Web Developer without any change in their skills
(`nlp/experiments/results/role_retune_effect.md`).

On the same statuses the new formula raises the mean from 45.9 to 55.5. The score rises
for most students, but 256 score lower (by at most 8.99 points): those who cover
preferred and bonus skills better than required ones. Of the 1,584 students who change
band, 971 move from Developing to On Track, 610 from Needs Support to Developing, 2 from
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
averages 55.5 while the bars average 49.0 (Technical), 46.9 (AI / Digital), 42.3
(Analytical) and 36.1 (Soft), and for 1,370 students it is above all four bars. We accept
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
- **Synthetic data.** The figures in sections 2.4 to 2.6 come from synthetic students;
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
| Student status (who needs support) | `backend/student_status.py`; levels per year and time windows in `backend/settings.py` (`year_expectations`, `support_active_days`, `new_student_days`) |
| "Not required" / "No data yet" | `frontend/src/utils/dimensions.js`, `frontend/src/components/DimensionBar.jsx` |
| Sensitivity analysis | `data/jrs_sensitivity.py` |
| Real job descriptions covered (section 7) | `backend/jd_fit.py` (`JD_FIT_THRESHOLD`), `GET /api/assessments/{id}/jd-fit`, `frontend/src/pages/SkillGap.jsx` |
| Cohort figures for section 7 | `data/jd_fit_cohort.py` |
| What a recommendation is worth (section 8) | `backend/readiness.py` (`skill_points`, `expected_gain`, `gain_between`), `nlp/matcher.py` (`status_after_activity`), `recommendation/engine.py` (`priority_key`, `first_steps`) |
| Importance of stored rows | `backend/assessment_service.py` (`load_match_rows`) |
| Cohort figures for section 8 | `data/rec_order_effect.py` |
| Tests | `tests/test_readiness.py`, `tests/test_jd_fit.py`, `tests/test_recommendation_engine.py`, `tests/test_backend_api.py` (`TestAssessment`, `TestJdFit`, `TestRecommendationPriority`), `nlp/tests/test_matcher.py` |

## 7. Real job descriptions covered (JD fit)

The Skill Gap page of a role-template assessment also says: *You cover at least 60% of
the skills in X of the N real job descriptions we analysed for this role.* A role template
is wider than one job, so the readiness score alone can look discouraging to a student who
would suit some real jobs. This number sits beside readiness and never feeds into it.

For each JD of the role in `data/jd_dataset/jd_skill_evidence.csv`, its skills are the
`skill_name` values of its `jd_ref`. A skill the student lists under the same name earns
1.0 if it is intermediate or advanced, or has project, certification or internship
evidence (stored or derived), and 0.5 at beginner level without it; any other skill earns
0. A JD's coverage is the mean over its skills, and X counts the JDs at 0.60 or above. It
is worked out from the student's current skills when the page is read, so it can differ
from the stored assessment, and the response says so (`based_on`, `computed_at`). There is
no figure for a pasted JD or for a role with no JDs in the file, such as an admin-created
role.

On the synthetic students (`python data/jd_fit_cohort.py`, 5 November 2026, data version
`2026-11-05-ict-roles`, latest role-template assessment of 5,000 students):

| Archetype | Students | Mean X | Mean N | X = 0 |
|---|---:|---:|---:|---:|
| strong | 1,215 | 10.3 | 34.7 | 1.4% |
| average | 2,508 | 2.7 | 34.8 | 28.4% |
| weak | 1,277 | 0.4 | 34.8 | 80.0% |

Spearman ρ between X and readiness is 0.826. This shows that the number separates the
generated archetypes, not that it fits real students or predicts hiring.

**Limits.**

- **Same name only.** A similar skill earns nothing here, though it can be Developing in
  the readiness score (rule A), so a student with MySQL gets no credit for PostgreSQL.
- **The JD skills come from hybrid extraction**, whose test-set F1 is 0.739 (recall 0.652,
  on 42 test JDs of the six IT roles, so Business JDs were not part of that test). A skill
  can be missed, and a skill named anywhere in the text counts, even if it describes the
  employer and is not a requirement. Three JDs with no skills found are left out, so N is
  34 for Business Analyst, Financial Analyst and Marketing Executive.
- **The Business JDs come from the United States**, not Malaysia (`data/jd_dataset/README.md`).
- **The 60% is a design choice from a pilot.** It has not been validated with employers,
  advisors or real students.
- **X cannot be compared across roles.** On similar mean readiness, Software Developer
  averages 1.4 and Financial Analyst 7.9, because JDs differ in how many skills they name.
- **Covered is not a job match.** Coverage is a mean of credits, not a share of skills
  listed (a student listing every skill of a JD at beginner level without evidence reaches
  only 50%), and it says nothing about seniority or whether an employer would hire.

## 8. What a recommendation is worth

The Recommendations page says what to do first and what it adds to the score. Readiness is
linear in the credits, so the points are exact:

- **Points of one skill** = 100 × tier weight / (sum of the weights of the tiers this job
  has) / (number of skills in its tier). `sum(points × credit)` over a job's skills is the
  readiness score.
- **`expected_gain`** = points × (1 − current credit): the most this skill can add, which it
  adds when it reaches Strong. Shown as "up to +X".
- **`gain_if_completed`** = points × max(0, credit after − current credit): what completing
  this resource adds. Shown as "+X points", or "No score change on its own" when it is 0.

**Credit after** (`status_after_activity` in `nlp/matcher.py`, the only copy): Strong if the
resource is intermediate or advanced, or its type gives project, certification or
internship evidence (a competition counts as a project); otherwise Developing. A missing
difficulty counts as beginner. So a beginner course takes a Gap to Developing (half the
points) and leaves a Developing skill where it is (0). Both numbers are rounded to 1 decimal
for display, so the score can differ from a displayed gain by up to 0.05.

**Order of the skills:** required gap, required developing, preferred gap, preferred
developing, bonus gap, bonus developing, then skill name.

**`first_steps`** (the "Do these first" card) walks the skills in that order and takes the
first 3 that have a resource worth doing. A resource the student has completed is never
picked. A skill with a resource completed after the assessment was created is skipped,
because its status is out of date until the student runs the assessment again. For each
skill it picks the highest `gain_if_completed` among free and free-to-learn resources, or
among all resources if those would add nothing, keeping the existing resource order on a
tie. A skill where nothing adds points is skipped.

**Importance of stored rows.** `skill_match_results.importance` is written from 6 November
2026 and not backfilled. Older rows are read as the role template's importance, then as
required (`load_match_rows`). So an older row follows any later change to the template.

Measured with `python data/rec_order_effect.py` on 6 November 2026, on a copy of the local
database reloaded with the data version `2026-11-05-ict-roles` and re-assessed (hybrid):
latest role-template assessment of 5,000 synthetic students, no activities completed.

| | Old order | New order |
|---|---:|---:|
| Required share of the first three skills | 8.6% | 74.7% |
| Students with a required skill to do who have one in the first three | 22.5% | 100.0% |
| Median position of the first required skill | 7 | 1 |
| Gain if all three reach Strong, mean / median | +6.1 / +4.4 | +18.2 / +19.5 |
| Gain from completing the first resource of each, mean / median | +4.5 / +3.2 | +13.0 / +13.2 |

`first_steps` on the same students: 73.9% required, gain +16.7 mean / +17.5 median, 3.4% of
the resources shown are paid. All 5,000 stored assessments satisfy `sum(points × credit) =
readiness_score` within 0.02.

These figures depend on the matching method. A machine without `nlp/requirements.txt` falls
back to keyword, which finds no related skills, so more skills are Gaps and each is worth
more. On the same data with keyword (mean readiness 52.1, not 55.5) the new order gives
74.7%, 100.0%, position 1, +19.4 and +14.1, and `first_steps` gives 74.0% required, +17.6 mean,
+18.8 median and 2.2% paid.

**Limits.**

- **The gain is arithmetic on the score, measured on synthetic students.** It does not show
  that a student learned the skill or became more employable.
- **Pasted job descriptions count every skill as required** until importance is extracted
  from them, so their order is only gap, developing, then name, and their label always says
  required.
- **With the semantic and hybrid methods the rise can be larger than the gain.** Adding a
  skill to a profile can also make a related skill of the job Developing (rule A), for
  example AWS for Azure. The gain counts only the skill the resource teaches. Simulating the
  `first_steps` of every 25th student (200 students, 600 steps, hybrid), the rise equalled the
  gain in 85.2% of steps and was larger in 14.8%, by +2.06 on average, and was never smaller.
  With the keyword method it is exact.
- **The number assumes the same job and an assessment run again.** The score does not change
  until the student runs the assessment again. An assessment scored before 5 November 2026
  also carries the old formula (section 2.6), so its next score moves by more than the gain.
- **Later resources of an out-of-date skill.** Below the card, the list still shows gains from
  the stored status, so after a beginner course a second beginner course on that skill still
  shows "+X points" until the student runs the assessment again.
