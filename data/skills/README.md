# Skills Library v2

**Owner:** Ng Yong Hin (AI / NLP Engineer). Aaron co-owns the library and adds recommendation resources for it.

`skills_library.csv` is the **only** file you edit by hand. Everything else is generated from it:

| Generated file | Used by |
|---|---|
| `database/seed_skills_library_v2.sql` | PostgreSQL `skills_library` table (backend, Swagger, assessments) |
| `nlp/resources/skills_taxonomy.json` | NLP extractor / matcher (Sprint 3), JD analysis |

## Editing the library

```powershell
# 1. edit data/skills/skills_library.csv
python data/skills/build_skills_seed.py              # validates, then regenerates the SQL + JSON
python -m pytest tests/test_skills_library.py -q     # all checks must pass
psql -U postgres -d seagas_db -f database/seed_skills_library_v2.sql
psql -U postgres -d seagas_db -f database/seed_job_role_skills.sql   # if role mappings changed
```

The seed is idempotent. It uses `ON CONFLICT (skill_name) DO UPDATE`, so running it again only updates category, aliases and description. It runs in a single transaction and stops at the first error.

## Columns

| Column | Meaning |
|---|---|
| `skill_name` | Canonical name. It must be unique (case-insensitive), at most 100 characters, and exactly the same as the name in the DB. |
| `category` | `Technical`, `AI_Digital`, `Analytical` or `Soft`. These are the only values allowed by the schema.sql CHECK constraint. |
| `subcategory` | A finer grouping (Programming Language, Web Framework, Database, DevOps, Cloud, Data & BI, Security Tool, Security Practice, ML/AI, Software Engineering, Design, Infrastructure, Analytical, Soft). It is used only by NLP and the report and is **not** stored in the DB. |
| `aliases` | Other spellings, separated by `\|`. They are stored in `skills_library.aliases`. |
| `ambiguous_aliases` | Terms that often match the wrong thing (`CV`, `R`, `Go`, `Excel`, `REST`, `Shell`, `PM`…), separated by `\|`. They are **not** stored in the DB. NLP may use them only when the case matches exactly and the context supports the skill. An ambiguous alias may repeat the skill's own name. This marks the name itself as ambiguous (for example `R`, `Go`, `Excel`). |
| `description` | A one-sentence description in English. |
| `source` | `v1` means the skill was seeded by schema.sql. `v2` means it was added in Sprint 2. |

## Rules (checked by the build script and pytest)

1. A skill name appears only once (case-insensitive).
2. Each alias (including ambiguous ones) belongs to one skill only and is never the same as another skill's name.
3. All 32 v1 skills from `schema.sql` are present, spelled exactly the same. **Never rename or delete a v1 skill.** Their names are referenced by `job_role_skills`, the synthetic data and Aaron's `recommendations_library`. Only their aliases and description may change.
4. The library has between 120 and 150 skills, and every skill has a description.

Do not edit `database/schema.sql`. Carl owns it. All changes to the library go into the v2 seed.

## Current contents

138 skills: 88 Technical, 21 AI_Digital, 15 Analytical and 14 Soft (32 from v1 and 106 added in v2). The v1 aliases that pointed at other skills (for example SQL → MySQL, Linux → Bash, Cloud Computing → AWS, Project Management → Agile) were removed.

**Category principle:** each domain sits in one category, so each assessment dimension has a clear meaning.

- **Security.** Both the practices and the tools are in `Technical`. The 7 security-practice skills moved there from `AI_Digital`.
- **Cloud.** Cloud Computing, AWS, Azure, GCP and Serverless are in `AI_Digital`, following the v1 categories.

Carl still needs to confirm the definition of `AI_Digital` and how the categories map to the assessment dimensions.
