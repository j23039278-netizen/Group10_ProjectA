# Job Readiness Score: formula and justification

**Owner:** Soh Way Miin (Carl), with Ng Yong Hin for the match statuses · **Code:**
`backend/assessment_service.py` · **Statuses:** `nlp/matcher.py`, rules in
[`NLP_CLASSIFICATION_RULES.md`](NLP_CLASSIFICATION_RULES.md) · **Sensitivity script:**
`data/jrs_sensitivity.py` · **Status (1 November 2026):** implemented; written up after
the lecturer meeting of 22 October asked us to research and justify the formula.

The Job Readiness Score answers one question: *of the skills this job asks for, how
much does the student's profile show, counting the important ones more?* It is a
decision-support indicator for students and advisors, not a hiring prediction. Every
point in it can be traced to one required skill and the reason stored for it.

## 1. Formula

For one assessment (a student against a role template or an analysed job description),
each required skill *i* gets an importance weight *wᵢ* and a status credit *cᵢ*:

| Importance (from the role template or JD) | Weight *w* | | Status (from the matcher) | Credit *c* |
|---|---:|---|---|---:|
| required | 3 | | Strong | 1.0 |
| preferred | 2 | | Developing | 0.5 |
| bonus | 1 | | Gap | 0 |

**Readiness = 100 × Σ (wᵢ × cᵢ) / Σ wᵢ**, rounded to 2 decimals (0 to 100).

The statuses come from the decision table in `NLP_CLASSIFICATION_RULES.md`: Strong is
the same skill at intermediate / advanced level, or at beginner level with a project,
certification or internship behind it; Developing is a beginner skill without that
evidence, or a different but similar / related skill; Gap is nothing close enough.

**Worked example** (the `match_skills` example in `NLP_INTERFACE.md`):

| Required skill | Importance | Status | Points |
|---|---|---|---|
| SQL | required (3) | Strong (1.0) | 3.0 |
| Python | required (3) | Developing (0.5) | 1.5 |
| Power BI | required (3) | Gap (0) | 0 |
| Azure | preferred (2) | Developing (0.5) | 1.0 |
| Docker | bonus (1) | Gap (0) | 0 |
| **Total** | **12** | | **5.5** |

Readiness = 100 × 5.5 / 12 = **45.83**.

## 2. Why this formula

### 2.1 Weighted coverage of the job's requirements

The score is a weighted share of the job's own requirements, so it changes with the
job: the same student can be 80% ready for Data Analyst and 40% for Cloud Engineer, which
is what a skill-gap tool should show. It also keeps the score explainable, a requirement
in our Team and Project Plan: the Skill Gap page lists each required skill with its
status and the reason, and the advisor sees the same rows. A model that learns a score
from data would need labelled hiring outcomes, which a proof of concept with synthetic
students does not have.

### 2.2 Importance weights 3 / 2 / 1

Job descriptions separate must-have from nice-to-have requirements, and the role
templates and JD analysis keep that as required / preferred / bonus. The 3 / 2 / 1
weights keep required skills dominant without making the others irrelevant: a missing
required skill costs as much as 1.5 preferred or 3 bonus skills. In our role templates
required skills are 38% of the rows, preferred 34% and bonus 28%, so with these weights
required skills carry about half of the score.

### 2.3 Developing = half credit

Developing covers two cases that are both "part of the way there": the right skill at
beginner level without project, certification or internship evidence, and a different
skill that is similar or related (for example MySQL for PostgreSQL). Half credit is the
neutral choice between "has it" and "does not have it"; the statuses are ordered
categories, not measurements, so we did not try to be more precise than that.

### 2.4 Sensitivity: the choice of weights does not change who is ahead

`data/jrs_sensitivity.py` re-scores the latest role-template assessment of every
student (5,001 assessments, 121,246 required-skill rows) with other weights and credits
and compares them with the current scheme:

| Scheme | Mean | Spearman ρ vs current | Students changing band (70 / 40) |
|---|---:|---:|---:|
| **current 3/2/1, developing 0.5** | 48.3 | 1.000 | 0 (0.0%) |
| equal 1/1/1, developing 0.5 | 42.9 | 0.987 | 953 (19.1%) |
| steeper 4/2/1, developing 0.5 | 50.4 | 0.998 | 325 (6.5%) |
| 3/2/1, developing 0.25 | 44.8 | 0.994 | 479 (9.6%) |
| 3/2/1, developing 0.75 | 51.9 | 0.993 | 491 (9.8%) |
| required skills only | 61.6 | 0.949 | 1,959 (39.2%) |

The order of the students hardly changes with any reasonable weighting (ρ ≥ 0.987), so
comparisons between students and over time do not depend on the exact weights. What the
weights do change is the level of the score, and therefore which band a student near a
boundary falls into. Ignoring preferred and bonus skills would move 39% of students
between bands, so we keep them. Measured on the local database on 1 November 2026, with
the assessments made before the matching-rule update of 30 October; run the script again
after `start_backend.bat` has re-assessed the students.

### 2.5 Readiness bands 70 / 40

The advisor dashboard groups students as On Track (≥ 70), Developing (40 to 69) and
Needs Support (< 40). The defaults follow the representative synthetic students in
`NLP_CLASSIFICATION_RULES.md` section 6: across roles and methods the strong students
average about 69 to 76, the average ones 45 to 54 and the weak ones 20 to 27. So 70 is
where strong students begin and 40 lies between average and weak. With the current
scheme the 5,001 latest assessments split 862 / 2,377 / 1,762. Because the right
boundaries depend on the institution, admins can change both values in
**Admin → System Settings**.

## 3. The seven dimensions

Each assessment also stores seven dimension scores, shown as bars on the Dashboard,
the Skill Gap page and the advisor's student page.

| Dimension | Column | How it is worked out | In the readiness score? |
|---|---|---|---|
| Technical Skills | `score_technical` | The formula above over the job's Technical skills only | Yes (its skills) |
| AI / Digital Skills | `score_ai_digital` | The same, AI_Digital skills | Yes (its skills) |
| Analytical Skills | `score_analytical` | The same, Analytical skills | Yes (its skills) |
| Communication | `score_communication` | The same, Soft skills | Yes (its skills) |
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
| **No data yet** | An experience dimension is 0, or a skill dimension is 0 and the student lists no skill of that category | Nothing is recorded in the profile yet; the student is told what to add |
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

- **The weights are a design choice, not learned.** Section 2.4 shows the ranking is
  stable, but the absolute level has not been checked against employers' judgement.
  There is no industry partner yet to do this.
- **Skill levels are self-reported.** Evidence from projects and certifications helps,
  but a student can still overstate a level.
- **Every required skill of one importance counts the same.** SQL and Git both count 3
  when required, even if an employer cares more about one of them.
- **Synthetic data.** The figures in sections 2.4 and 2.5 come from synthetic students;
  the planned evaluation with 25 UAD students and the SUS test will be the first check
  with real users.
- **MQF mapping and Malaysian competency surveys** (section 4) are still to be
  researched in detail.

## 6. Where it is in the code

| What | Where |
|---|---|
| Weights, credits, formula, dimensions | `backend/assessment_service.py` (`IMPORTANCE_WEIGHTS`, `STATUS_CREDIT`, `weighted`, `category_score`) |
| Strong / Developing / Gap | `nlp/matcher.py`, `docs/NLP_CLASSIFICATION_RULES.md` |
| Evidence from projects and certifications | `nlp/evidence.py` |
| Readiness bands | `backend/settings.py` (`readiness_on_track`, `readiness_needs_support`), Admin → System Settings |
| "Not required" / "No data yet" | `frontend/src/utils/dimensions.js`, `frontend/src/components/DimensionBar.jsx` |
| Sensitivity analysis | `data/jrs_sensitivity.py` |
| Tests | `tests/test_backend_api.py` (`TestAssessment`), `nlp/tests/test_matcher.py` |
