# Synthetic Student Dataset

**Author:** Ng Yong Hin (AI / NLP Engineer)

500 anonymised, synthetic student profiles for the SEAGAS POC. Every table and column
matches `database/schema.sql`. No real student data is used.

## Load into PostgreSQL (no Python needed)

Run `database/schema.sql` first, then:

```bash
psql -U postgres -d seagas_db -f data/output/seed_synthetic_students.sql
```

This inserts rows into `users`, `student_profiles`, `student_skills`,
`student_projects` and `student_certifications`, all inside one transaction.

**Demo login:** any account from `student0001@synthetic.seagas.test` to
`student0500@synthetic.seagas.test`. The password is `Seagas@2026`.

**Remove all synthetic data** (cascades to their assessments too):

```bash
psql -U postgres -d seagas_db -f data/delete_synthetic_data.sql
```

The data is deterministic (same seed means the same UUIDs). To reload it,
run the delete script first.

## Regenerate

```bash
pip install faker bcrypt
cd data
python generate_synthetic_data.py              # 500 students, seed 42
python generate_synthetic_data.py --n 300 --seed 7
```

The script stops with an error if it uses a skill name that is not in
`skills_library` in `schema.sql`. When the skills library is expanded, add
the new skills to `ROLES`, `PROJECTS` and `CERTIFICATIONS` in the script.

## Output files (`data/output/`)

| File | Purpose |
|------|---------|
| `seed_synthetic_students.sql` | Ready-to-run insert script. Skills are resolved by `skill_name`. |
| `users.csv`, `student_profiles.csv`, `student_skills.csv`, `student_projects.csv`, `student_certifications.csv` | The same data as CSV, with arrays in PostgreSQL `{...}` format |
| `students_meta.csv` | Ground truth for each student (target role, archetype, core-skill coverage). It is **not** loaded into the database. Use it to check that readiness scores rank students sensibly. |
| `summary_stats.txt` | Distribution statistics for the Dataset section of the report |

## How the data is generated

- **Target role:** each student gets one of the 6 `job_roles`, weighted toward
  Software Developer and Data Analyst.
- **Archetype:** strong 25%, average 50% and weak 25%. The archetype controls
  how likely the student is to have the role's core and secondary skills, plus
  their GPA, number of projects and certifications, and chance of an internship.
  With seed 42, the mean core-skill coverage is about 93% for strong, 70% for
  average and 37% for weak students. This gives the Advisor Dashboard a
  realistic spread of readiness scores.
- **Consistent evidence:** skills used in a generated project get
  `evidence_type = project`, and skills covered by a certification get
  `certification`. The `project_count`, `certification_count` and
  `internship_count` fields match the rows in the detail tables.
- **Proficiency:** depends on archetype, year of study and whether there is
  evidence beyond coursework.
- **Noise:** 0–2 random off-role skills are added per student.
- **Names:** romanised Malaysian names (Chinese, Malay and Indian) plus a few
  international names.
- **Emails:** all use the reserved `.test` domain, so no real address can be
  hit.
