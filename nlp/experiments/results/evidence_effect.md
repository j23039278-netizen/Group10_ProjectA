# Evidence from projects and certifications: effect on readiness

`python nlp/experiments/evidence_effect.py --method hybrid` · rules `2026-10-30` · 5000 synthetic students (`data/output/`, `2026-10-28-business`), each against their own target role · 25 s

`nlp.derive_evidence()` adds project, certification and internship evidence to the skills a student lists, from their projects (technologies, title, description) and certifications (name; issuer only when the name gives no skill). Only a **beginner** skill can change, from Developing to Strong (rule C); every other status is the same with and without it.

## Website scenario (stored evidence empty, as for real users)

The website has no evidence input when a student adds a skill, so `evidence_type` is empty for real users. Without derived evidence a beginner skill can never be Strong.

With derived evidence, **2133 of 122038 required-skill rows (1.7%) move from Developing to Strong**, for 1455 of 5000 students (29.1%). Mean readiness rises from 48.98 to 50.01 (+1.02 points).

| Archetype | Students | Rows | Developing → Strong | Students with a change | Mean readiness without | with | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| strong | 1228 | 29996 | 166 (0.6%) | 143 | 73.00 | 73.34 | +0.33 |
| average | 2446 | 59604 | 1091 (1.8%) | 810 | 50.21 | 51.27 | +1.07 |
| weak | 1326 | 32438 | 876 (2.7%) | 502 | 24.49 | 26.06 | +1.58 |

| Role | Students | Rows | Developing → Strong | Students with a change | Mean readiness without | with | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Business Analyst | 417 | 9591 | 177 (1.8%) | 122 | 52.33 | 53.40 | +1.07 |
| Cloud Engineer | 350 | 8750 | 165 (1.9%) | 110 | 47.13 | 48.20 | +1.07 |
| Cybersecurity Analyst | 426 | 11928 | 165 (1.4%) | 115 | 48.45 | 49.16 | +0.71 |
| Data Analyst | 682 | 16368 | 300 (1.8%) | 195 | 47.80 | 48.94 | +1.13 |
| Data Scientist | 412 | 10712 | 199 (1.9%) | 133 | 47.71 | 48.87 | +1.16 |
| Financial Analyst | 417 | 9591 | 141 (1.5%) | 101 | 45.15 | 46.08 | +0.92 |
| HR Executive | 416 | 9568 | 150 (1.6%) | 111 | 48.90 | 49.72 | +0.81 |
| Marketing Executive | 417 | 9591 | 199 (2.1%) | 136 | 51.55 | 52.80 | +1.26 |
| Software Developer | 827 | 20675 | 366 (1.8%) | 245 | 48.34 | 49.32 | +0.98 |
| Web Developer | 636 | 15264 | 271 (1.8%) | 187 | 51.98 | 53.05 | +1.07 |

By the number of projects and certifications the student lists:

| Projects + certifications | Students | Rows | Developing → Strong | Students with a change | Mean readiness without | with | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 411 | 10035 | 0 (0.0%) | 0 | 21.00 | 21.00 | +0.00 |
| 1 | 937 | 22916 | 448 (2.0%) | 304 | 31.27 | 32.40 | +1.13 |
| 2 | 1184 | 28793 | 755 (2.6%) | 489 | 43.82 | 45.34 | +1.53 |
| 3+ | 2468 | 60294 | 930 (1.5%) | 662 | 62.85 | 63.76 | +0.91 |

## Stored scenario (synthetic evidence as generated)

The generator writes `evidence_type` from the same projects and certifications, so derived evidence adds little: 14 of 122038 rows (0.0%) move from Developing to Strong; mean readiness 50.21 → 50.21 (+0.01). The rows that change:

| Student skill | Evidence from | Rows |
|---|---|---:|
| Cloud Computing | project: Serverless Image Resizer | 5 |
| Cloud Computing | project: Infrastructure as Code Lab | 4 |
| CRM Software | certification: HubSpot Content Marketing Certification | 4 |
| CRM Software | certification: HubSpot Email Marketing Certification, HubSpot Content Marketing Certification | 1 |

Status transitions, all scenarios (without → with):

| Scenario | Transition | Rows |
|---|---|---:|
| stored | developing → strong | 14 |
| website | developing → strong | 2133 |

## Derived evidence against the generator's evidence

The generator knows which skills each project and certification stands for (the project template's skills, the certification's skill list). Per student skill:

| Evidence | Both | Derived only | Generator only | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| project | 28411 | 94 | 0 | 99.7% | 100.0% |
| certification | 3133 | 10 | 7453 | 99.7% | 29.6% |

Project evidence (project or internship) is close to complete because synthetic projects list their skills in `technologies`. Certification recall is lower by design: keyword extraction reads only the certification's name, and the generator's lists include skills the name does not say ("Google Data Analytics Professional Certificate" stands for SQL, Tableau and R too). "Derived only" rows:

| Student skill | Evidence from | Rows |
|---|---|---:|
| Cloud Computing | project: Serverless Image Resizer | 47 |
| Cloud Computing | project: Infrastructure as Code Lab | 35 |
| CRM Software | certification: HubSpot Content Marketing Certification | 6 |
| Cloud Computing | internship: Serverless Image Resizer | 4 |
| Cloud Computing | project: Infrastructure as Code Lab, Serverless Image Resizer | 4 |
| CRM Software | certification: HubSpot Email Marketing Certification | 3 |
| Cloud Computing | project: Serverless Image Resizer, Infrastructure as Code Lab | 2 |
| Cloud Computing | internship: Infrastructure as Code Lab | 2 |

## Notes

- Cloud Computing rows come from `IMPLIED_SKILLS` (an AWS / Azure / GCP project or certification is also Cloud Computing evidence), which the generator's project templates do not list. CRM Software rows come from "HubSpot" in a certification name, a catalogue alias of CRM Software: a HubSpot Academy marketing certification is not CRM evidence, a known false positive (`docs/NLP_CLASSIFICATION_RULES.md`, section 4a).
- Only rule C depends on evidence, so the transitions and the Δ are the same for `keyword` and `hybrid` (checked); the absolute readiness differs (hybrid also gives Developing for related skills).
- The effect is bounded by the beginner skills that a project or certification names. The generator makes a skill with project or certification evidence more likely intermediate or advanced, so few synthetic beginner skills have one, and students with no projects or certifications cannot gain. Per skill the gain is half its weight (Developing 0.5 → Strong 1.0).
- `DERIVED_EVIDENCE_NEEDS_PROOF` (off) would count only projects / certifications with an evidence file or link. The synthetic data has no evidence files, so with it on the "with" columns would equal "without".

Per student: `evidence_effect_students.csv`; groups: `evidence_effect.csv`.
