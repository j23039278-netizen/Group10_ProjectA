# Strong / Developing / Gap classification rules (S2-12-01)

**Owner:** Ng Yong Hin (AI / NLP Engineer) · **Code:** `nlp/matcher.py`, called as
`nlp.match_skills()` · **Settings:** `nlp/config.py` · **Tests:** `nlp/tests/test_matcher.py`
· **Status (2026-10-30):** implemented and tested; proposals A and C of section 7 adopted
on 2026-10-28, proposal B not adopted. Since 2026-10-30, evidence is also derived from the
student's projects and certifications (`nlp/evidence.py`, section 4a).

Every skill a job requires gets exactly one status. **Strong** means the student has the
same skill and backs it with intermediate / advanced level, or, at beginner level, with a
project, certification or internship. **Developing** means the student is part of the way
there: the skill at beginner level with no evidence or coursework only, or a different
skill that is similar or related. **Gap** means nothing in the profile is close enough.
The readiness score then weighs these statuses (section 6).

## 1. Decision table

| # | The student has, compared with the required skill | Level / evidence of that student skill | Status | `similarity_score` |
|---|---|---|---|---|
| 1 | The same skill (same `skill_id`, name, alias or spelling) | intermediate or advanced, or beginner with project, certification or internship evidence | **Strong** | 1.0 |
| 2 | The same skill | beginner with no evidence or coursework only | **Developing** | 1.0 |
| 3 | A different skill, similarity ≥ `MATCH_THRESHOLD` (0.60) | any | **Developing** | cosine |
| 4 | A different skill, `RELATED_THRESHOLD` (0.50) ≤ similarity < 0.60 | any | **Developing** | cosine |
| 5 | Nothing above, or no skills in the profile | – | **Gap** | 0.0 |

- *Evidence* is `evidence_type`: project, certification, coursework or internship. For a
  beginner, only project, certification or internship makes the skill Strong; coursework
  alone does not (rule C, `STRONG_EVIDENCE` in `nlp/matcher.py`). The backend adds the
  evidence that the student's projects and certifications show before matching
  (section 4a), so a beginner skill used in a listed project counts as Strong.
- Only the same skill can be Strong. A different skill is at most Developing however
  close it is (rule A). Rows 3 and 4 differ only in the reason shown to the student.
- Rows 3–4 exist only for `method="semantic"` and `"hybrid"`. `"keyword"` uses rows 1, 2
  and 5.
- In `"hybrid"`, row 1 or 2 is always tried first; similarity is only computed for
  required skills that no student skill matches exactly.

## 2. Thresholds

| Setting (`nlp/config.py`) | Value | Meaning |
|---|---|---|
| `MATCH_THRESHOLD` | 0.60 | At or above: very close to the skill (row 3); in JD extraction, counts as the skill |
| `RELATED_THRESHOLD` | 0.50 | At or above, below MATCH: related, not the same skill (row 4) |
| `SKILL_TEXT_MODE` | `name_aliases` | Each skill is embedded as one text, "Name: alias, alias" |
| `MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence Transformers model, 384 dimensions, CPU |

The values were chosen from 60 hand-labelled JD phrase / skill pairs. At 0.60:
precision 1.000, recall 0.867, F1 0.929. The method and the near-threshold pairs are in
[`nlp/experiments/THRESHOLDS.md`](../nlp/experiments/THRESHOLDS.md). The thresholds
live only in `nlp/config.py`; nothing else hard-codes them.

`similarity_score` is cut (not rounded) to 3 decimals, the precision of
`skill_match_results.similarity_score`, and the thresholds are applied to that value. A
stored 0.599 is therefore never classified as ≥ 0.60.

## 3. How each method picks the student skill

| Method | Which student skill decides a required skill |
|---|---|
| `keyword` | A student skill that is the same skill: same `skill_id` when both sides have one, otherwise the same canonical name after catalogue lookup ("PowerBI", "Power-BI" and "Power BI" are one skill; "Java" and "JavaScript" are two). If several entries match, one with level or evidence wins. No similarity is computed. |
| `semantic` | The student skill with the highest cosine similarity to the required skill. Catalogue skills reuse the cached skill embeddings; a name outside the catalogue is embedded from the name alone. The same skill scores 1.0. Ties go to the better status, then to the skill listed first. |
| `hybrid` | `keyword` first. `semantic` only for required skills with no exact match, so a beginner SQL entry decides SQL (Developing) even if the student also lists an advanced MySQL. |

Every `MatchResult` also carries:

- `matching_method`: the method passed to `match_skills()`, the same on every row.
- `matched_student_skill`: the name of the student skill that decided the row; `None`
  for a gap.

## 4. Reason templates

`reason` is one plain-English sentence (two for the related case) built from a fixed
template, never free text (`REASONS` in `nlp/matcher.py`). `{student}` is the deciding
student skill, `{skill}` the required skill, and `{detail}` its level and evidence, e.g.
"advanced, with project and coursework evidence". When the evidence was derived from the
student's records (section 4a), `{detail}` also names them, at most two (`MAX_TITLES`)
and then "N more": "beginner, with project evidence from Sales Dashboard", "beginner, with
project and certification evidence from Sales Dashboard, AWS Certified Cloud Practitioner
and 1 more". The titles are the student's own project / certification titles as entered.

| Case | Decision table row | Template |
|---|---|---|
| `same_strong` | 1 | You list {student} ({detail}), which matches this skill, so this is marked Strong. |
| `same_developing` | 2 | You list {student} ({detail}). A beginner skill needs project, certification or internship evidence to count as Strong, so this is marked Developing. |
| `similar` | 3 | You list {student} ({detail}), which is very close to {skill} but not the same skill, so this is marked Developing. |
| `related` | 4 | You list {student} ({detail}). It is closely related to {skill} but not the same skill, so this is marked Developing. |
| `gap_keyword` | 5, keyword | No skill in your profile is {skill} or another name for it, so this is marked as a Gap. |
| `gap_similar` | 5, semantic / hybrid | No skill in your profile is {skill} or close enough to it, so this is marked as a Gap. |
| `gap_empty` | 5, empty profile | Your profile lists no skills yet, so this is marked as a Gap. |

## 4a. Evidence from projects and certifications

The website has no evidence input when a student adds a skill, so for real users
`student_skills.evidence_type` is empty and row 1 at beginner level could never fire.
Students do list projects (with technologies and a description) and certifications.
`nlp.derive_evidence(student_skills, projects, certifications)` (`nlp/evidence.py`) reads
them at assessment time; `backend/assessment_service.py` calls it just before
`match_skills()`.

| A record | gives this evidence to a student skill when | Evidence type |
|---|---|---|
| Project | its `technologies` contain the skill (catalogue lookup, aliases resolved: "Postgres" → PostgreSQL), or keyword extraction finds the skill in `project_title` or `description` | `project`; `internship` when `project_type` is internship |
| Certification | keyword extraction finds the skill in `cert_name`; `issuer` only when the name gives no skill | `certification` |

- Only skills the student lists get evidence; no skill is added to the profile.
- Stored `evidence_type` is kept, first and in its order; derived types are appended. It is
  computed for each assessment and never written back to `student_skills`.
- Keyword extraction only (`extract_skills(method="keyword")`, no model): fast, and every
  piece of evidence traces back to a word the student wrote.
- **Free text never evidences a soft skill or a trait** (category Soft, plus Problem
  Solving, Critical Thinking, Decision Making, Systems Thinking): "good communication and
  teamwork" in a description is a claim, not something the project showed. The same skill
  listed in `technologies` counts.
- **Issuer as a fallback.** Issuers are organisations, and their names contain skills:
  "CNCF / Linux Foundation" (Kubernetes certification → Linux), "Tableau / Salesforce"
  (→ CRM Software), "DeepLearning.AI" (Machine Learning certification → Deep Learning).
  Reading the issuer only when the name gives nothing removes all of these and keeps the
  useful case, a certification named "Cloud Practitioner" from "Amazon Web Services".
- **Implied skills** (`IMPLIED_SKILLS`): AWS, Azure or GCP evidence is also Cloud Computing
  evidence, so "AWS Certified Cloud Practitioner" evidences AWS and Cloud Computing.
- `evidence_sources` on each returned skill names the project / certification behind each
  derived type; the reason shows them (section 4).

**Proof flag.** `DERIVED_EVIDENCE_NEEDS_PROOF` in `nlp/config.py` (default **off**) counts
a project or certification only when it has at least one evidence file or link in
`student_evidence_files`. The trade-off:

| | Off (default) | On |
|---|---|---|
| Who gains | every student who lists a project / certification using the skill | only students who also upload proof |
| Risk | a student can type a project that never happened and turn beginner skills Strong | a real project without an upload stays Developing; the student must know to upload |
| Effort for the student | none beyond the profile they already fill in | an upload or link per project / certification |
| Synthetic data | as measured below | no effect: the synthetic data has no evidence files |

Off is the default because the advisor already sees every project and certification, with
any proof, on the student's page; a beginner skill moves only from Developing to Strong
(half the skill's weight), and only for skills the student also lists. Turn it on if
advisors find unsupported projects inflating scores; bump `MATCH_RULES_VERSION` with it.
A certification's `credential_url` is not counted as proof; it could be, as it is a link
the advisor can check.

**Known limits.** "HubSpot" is a catalogue alias of CRM Software, so "HubSpot Content
Marketing Certification" gives CRM Software evidence; a HubSpot Academy marketing
certification is not CRM evidence. Keyword extraction reads only what a certification's
name says: "Google Data Analytics Professional Certificate" evidences Data Analysis, not the
SQL, Tableau and R the course also covers (recall 29.6% against the generator's lists,
precision 99.7%).

**Effect** (`nlp/experiments/evidence_effect.py`, `results/evidence_effect.md`; 5,000
synthetic students against their own target role, hybrid). With stored evidence emptied, as
for real users: 2,133 of 122,038 required-skill rows (1.7%) move from Developing to Strong,
for 1,455 students (29.1%); mean readiness +1.02 points (strong +0.33, average +1.07, weak
+1.58; by role +0.71 to +1.25). Students with no projects or certifications gain nothing.
With the evidence as generated (already derived from the same records), 14 rows change.
Batch runtime on 200 synthetic students: +0.8 ms per student (keyword 5.1 → 5.9 ms, hybrid
10.0 → 10.8 ms, including the database queries).

## 5. Worked examples

Real output of `match_skills()` on 2026-10-28, one student skill against one required
skill (importance `required`). The cosine is the full similarity before it is cut to
3 decimals.

| # | Example | Student skill (level, evidence) | Required skill | Cosine | `keyword` | `hybrid` |
|---|---|---|---|---:|---|---|
| 1 | Exact, strong | SQL (advanced, project) | SQL | 1.0 | Strong, 1.0 | Strong, 1.0 |
| 2 | Exact, beginner | Python (beginner, none) | Python | 1.0 | Developing, 1.0 | Developing, 1.0 |
| 3 | Semantic, very close | Business Analysis (intermediate, coursework) | Requirements Analysis | 0.6965 | Gap | Developing, 0.696 |
| 4 | Related | AWS (intermediate, certification) | Azure | 0.5250 | Gap | Developing, 0.524 |
| 5 | Word trap | Java (advanced, project) | JavaScript | 0.3139 | Gap | Gap, 0.0 |
| 6 | Missing | SQL (advanced, project) | Docker | 0.0333 | Gap | Gap, 0.0 |

The `hybrid` reasons:

1. You list SQL (advanced, with project evidence), which matches this skill, so this is
   marked Strong. *(row 1)*
2. You list Python (beginner). A beginner skill needs project, certification or
   internship evidence to count as Strong, so this is marked Developing. *(row 2)*
3. You list Business Analysis (intermediate, with coursework evidence), which is very
   close to Requirements Analysis but not the same skill, so this is marked Developing.
   *(row 3)*
4. You list AWS (intermediate, with certification evidence). It is closely related to
   Azure but not the same skill, so this is marked Developing. *(row 4)*
5. No skill in your profile is JavaScript or close enough to it, so this is marked as a
   Gap. *(row 5: 0.314 < 0.50)*
6. No skill in your profile is Docker or close enough to it, so this is marked as a Gap.
   *(row 5)*

Example 4 shows the 3-decimal cut: the cosine is just below 0.525, so the stored score
is 0.524. Tableau against a Power BI requirement scores 0.251, so it is a **Gap**, not
Developing (section 7, limit 2; proposal B not adopted).

## 6. Readiness score (S2-11-01)

The score is computed in `backend/assessment_service.py` (Carl). It is unchanged; the
matcher only supplies `match_status` for each required skill.

- Weight by importance: required 3, preferred 2, bonus 1.
- Credit by status: strong 1.0, developing 0.5, gap 0.
- Readiness = 100 × Σ (weight × credit) / Σ weight, rounded to 2 decimals.

*Example* (the `match_skills` example in `docs/NLP_INTERFACE.md`): SQL required, strong
(3 × 1); Python required, developing (3 × 0.5); Power BI required, gap (0); Azure
preferred, developing (2 × 0.5); Docker bonus, gap (0). That is 5.5 of 12 points, a
readiness of **45.83**.

*Representative synthetic students* (S2-11-02, `test_matcher.py`): for each role and
archetype, the student whose readiness is the median of that group. In all four roles
and with both methods, strong > average > weak:

| Role | Method | strong | average | weak | means (strong / average / weak) |
|---|---|---:|---:|---:|---|
| Data Analyst | keyword | 72.0 | 48.0 | 23.0 | 70.6 / 48.3 / 24.0 |
| Data Analyst | hybrid | 72.0 | 51.0 | 26.0 | 72.2 / 50.4 / 26.4 |
| Cybersecurity Analyst | keyword | 69.0 | 44.8 | 19.0 | 68.7 / 44.6 / 20.1 |
| Cybersecurity Analyst | hybrid | 73.3 | 50.9 | 25.0 | 73.5 / 50.8 / 25.5 |
| Business Analyst | keyword | 73.5 | 49.0 | 21.4 | 72.2 / 49.5 / 22.3 |
| Business Analyst | hybrid | 76.5 | 55.1 | 25.5 | 75.9 / 54.4 / 26.5 |
| HR Executive | keyword | 72.5 | 51.0 | 24.5 | 72.1 / 50.1 / 24.8 |
| HR Executive | hybrid | 73.5 | 51.0 | 26.5 | 73.4 / 51.8 / 26.4 |

Figures are with rules A and C and the synthetic data version `2026-10-28-business`
(Business students generated for the Business roles; only IT students count for the IT
roles). Until then the representative student was the one with the median core-skill
coverage. That pick proved fragile: many students share the median coverage, and for HR
Executive the first of them was a year-1 student whose skills were all beginner with
coursework only (rule C), who scored below the weak representative.

## 7. Known limits and proposals

These come from `nlp/experiments/results/compare_with_current.md` (200 synthetic
students × 6 roles, 30,400 required-skill rows, run before the decision). **Decision
(2026-10-28):** A and C adopted and implemented; B not adopted. The row counts below are
the expected effect measured in that comparison.

**Limit 1. Similarity Strong between two different skills happens only at the threshold
edge.** Of the 9,453 pairs of different catalogue skills, 5 reach 0.60 and 26 reach
0.50. In the comparison, 104 rows (0.3%) became Strong through a different skill, all
from two pairs:

| Required skill | Student skill | Cosine (stored) | Rows |
|---|---|---:|---:|
| Teamwork | Leadership | 0.6008 (0.600) | 81 |
| Cybersecurity / Security Operations (SOC) | SOC / Cybersecurity | 0.6012 (0.601) | 23 |

Leading a team is not the same as working in one. "Cybersecurity" is an umbrella term,
which the labelling rules in THRESHOLDS.md count as a non-match. *Proposal A
(adopted):* a similarity match between two **different** catalogue skills is at most
Developing; Strong needs the same skill (row 1). These 104 rows become Developing.

**Limit 2. Related tools are under-detected, not over-detected.** Name-and-alias
embeddings do not say "same family of tool": Tableau → Power BI 0.251, MySQL →
PostgreSQL 0.321, SQL → PostgreSQL 0.351, Communication → Stakeholder Communication
0.371, Linux → Kali Linux 0.317. All are Gap. Against today's substring logic, 305
Developing rows of this kind become Gap (SQL / PostgreSQL 142, Communication /
Stakeholder Communication 96, Linux / Kali Linux 67). Embedding descriptions instead
(`name_description`) would swing too far: MySQL → PostgreSQL 0.822 and TensorFlow →
PyTorch 0.856 would be Strong. *Proposal B (not
adopted):* treat two different skills in the same tool subcategory of the taxonomy
(Data & BI, Database, Cloud, Web Framework, Security Tool) as Developing, never Strong.
Whole subcategories are too broad (Data & BI holds Power BI and Pandas; Database holds
PostgreSQL and Redis). If this limit is addressed later, the preferred form is a
hand-curated `related_skills` column in `skills_library.csv` (e.g. Tableau ↔ Power BI,
SQL ↔ MySQL / PostgreSQL, Linux ↔ Kali Linux), always Developing. Until then these pairs
stay Gap; this is a known limitation for the report.

**Limit 3. Coursework alone counts as evidence.** In the synthetic data every skill
entry has evidence: 0 of 78,327 are beginner without evidence, and 11,322 of the 15,774
beginner entries have coursework only. So row 2 never fires there, and every same-skill
match is Strong. *Proposal C (adopted):* for a beginner, count only project,
certification or internship as evidence; coursework alone keeps a beginner at
Developing. In the comparison sample, 1,046 of the 6,789 same-skill rows (15.4%) move
from Strong to Developing. The website cannot yet record `evidence_type` when a student
adds a skill (the API accepts it). Since 2026-10-30 the evidence the student's projects and
certifications show is derived at assessment time instead (section 4a), so row 1 at
beginner level can fire for real users.

**Limit 4. The thresholds were tuned on JD phrase → skill pairs**, not skill ↔ skill
pairs. Re-check both on labelled skill pairs together with the gold set (Sprint 4).

## 8. Evidence

| What | Where |
|---|---|
| Boundary values (exactly at and just below MATCH and RELATED), missing skills, weak matches, word traps (Java / JavaScript, R / Ruby, MySQL / SQL), complete fields, reasons | `nlp/tests/test_matcher.py` |
| Related tools and word traps with the real model (similarities printed) | `test_related_tools_with_the_model`, `test_word_traps_with_the_model` |
| Readiness on representative synthetic students (S2-11-02) | `test_readiness_ranks_strong_average_weak_*` |
| Before / after against the current backend logic | `nlp/experiments/compare_with_current.py`, `results/compare_with_current.md` |
| Evidence from projects and certifications: aliases, internship, certification names, issuer fallback, no evidence from generic words, stored evidence kept, proof flag, reasons | `nlp/tests/test_evidence.py`; in the API: `test_project_gives_evidence_without_changing_stored_skills` (`tests/test_backend_api.py`) |
| Effect of derived evidence on readiness, per archetype and role | `nlp/experiments/evidence_effect.py`, `results/evidence_effect.md` |
