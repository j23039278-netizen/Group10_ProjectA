# Gold Annotation Guide — JD Skills (SEAGAS)

**Purpose:** a hand-checked set of skill labels for 60 JDs (10 per role, `gold_sample.csv`).
Sprint 4 uses it to measure the L1 (keyword) and L2 (semantic) extractors.

> **Rule:** the gold labels must come from a person. Do not paste the output of the
> system being evaluated. `gold_labels_draft.csv` comes from a simple keyword
> baseline. It is only there to save typing. Check every draft row, fix it or
> delete it, and add any skills it missed. Then copy the result into `gold_labels.csv`.

## Output format (`gold_labels.csv`)

| Column | Value |
|---|---|
| `jd_ref` | e.g. `JD-CY-0003` (from `gold_sample.csv`) |
| `skill_name` | the canonical name from `data/skills/skills_library.csv`, or `NEW: <term>` if the library does not have the skill |
| `importance` | `required`, `preferred` or `bonus` |
| `evidence_text` | the shortest phrase or sentence from the JD that shows the skill |

Use one row for each skill in each JD. If the JD mentions a skill several times, keep the strongest importance and give one piece of evidence.

## What counts as a skill

- **Label** tools, languages, platforms, methods and practices (for example *Python*, *SIEM*, *Terraform*, *incident response*, *data cleaning*), plus soft or analytical skills that are stated as a requirement (for example "strong communication skills").
- **Map synonyms** to the canonical name. For example: "Postgres" → `PostgreSQL`, "pen testing" → `Ethical Hacking`, "IaC" → `Terraform` only when Terraform is the tool meant, otherwise `NEW: Infrastructure as Code`.
- **Do not label** degrees, years of experience, languages such as English or Malay, company benefits, generic words ("computer", "technology"), or job duties that are not skills ("attend meetings").
- **Ambiguous terms:** read the context. "CV" usually means a résumé, not Computer Vision. "Go" can be the language or just the verb. "Excel" can be the tool or "excel in". "Shell" can be the company. Only label the term when the JD clearly means the skill.
- **Umbrella and specific skills:** if the JD names both (for example "cloud platforms such as AWS"), label both `Cloud Computing` and `AWS`.

## Importance

| Importance | Typical cues |
|---|---|
| `required` | "must have", "required", "essential", "minimum", "you have…", and anything under a *Requirements* / *Qualifications* heading with no softer wording |
| `preferred` | "preferred", "desirable", "ideally", "good to have", "familiarity with", "exposure to" |
| `bonus` | "nice to have", "a plus", "an advantage", "bonus points" |

A duty listed under *Responsibilities* with no qualifier counts as `required`. If you cannot decide, choose the weaker level and add `?` at the end of `evidence_text`, so the item can be discussed.

## Skills the library does not have

Write `NEW: <term>` in `skill_name`, for example `NEW: DevOps`. After annotation, these rows and `unmatched_terms.csv` together tell us which skills to add to the library. Adding a skill later does not change the gold labels. Only the `NEW:` rows need to be re-mapped.

## Process

1. Annotator A labels all 60 JDs.
2. If time allows, annotator B labels 12 of them (2 per role). Report the agreement (Cohen's κ on skill presence) in the report.
3. Resolve disagreements together, then freeze `gold_labels.csv` with a commit.
