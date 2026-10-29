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

Labelling happens in an Excel workbook (one sheet per JD: the JD text on top, the label table below). The scripts only move labels between the workbook and the CSV files and check them. They never create labels. Run every command from the repo root.

1. **Annotator A labels all 60 JDs.**
   ```bash
   python data/jd_dataset/gold/make_workbook.py
   ```
   This creates `gold/gold_workbook.xlsx`. The table on each sheet is pre-filled from `gold_labels_draft.csv` with `keep` empty. Set `keep` = `Y` (correct; fix the cells if needed) or `N` (wrong) on every row, then add the missing skills on the empty rows with `keep` = `Y`. `skill_name` and `importance` have drop-downs. Type `NEW: <term>` for a skill not in the list and click *Yes* on the warning. Yellow rows still need a Y or N. The README sheet links to every JD and counts the rows still to review. Use `note` for anything to discuss (it is not exported).
   ```bash
   python data/jd_dataset/gold/collect_workbook.py
   ```
   This writes `gold_labels.csv` from the `keep` = `Y` rows. Run it as often as you like: it lists errors (unknown skill name, bad importance, …), warnings (evidence not found in the JD text) and the JDs not started yet, plus a per-role summary. If there are errors, nothing is written. Fix the workbook, not the CSV, because the CSV is overwritten on every run.
2. **If time allows, annotator B labels 12 of the JDs (2 per role, seed 42).**
   ```bash
   python data/jd_dataset/gold/make_workbook.py --annotator B
   ```
   This creates `gold/gold_workbook_B.xlsx` with empty tables. B must not see the draft, A's workbook or `gold_labels.csv`. To choose the JDs yourself, add `--refs JD-CE-0001 JD-CY-0004 …`.
   ```bash
   python data/jd_dataset/gold/collect_workbook.py --annotator B
   ```
   This writes `gold_labels_B.csv` from every non-empty row (except rows with `keep` = `N`).
   ```bash
   python data/jd_dataset/gold/agreement.py
   ```
   This writes `gold/AGREEMENT.md` (Cohen's κ on skill presence, with and without sampled negatives, percent agreement, and weighted κ on importance) and `gold/agreement_disagreements.csv`. Put the κ figures in the report.
3. **Resolve the disagreements together.** Fix `gold_workbook.xlsx`, run `collect_workbook.py` again, then freeze `gold_labels.csv` with a commit.

`make_workbook.py` never overwrites an existing workbook, because it may already hold labels. Use `--force` only if you really want to start again.
