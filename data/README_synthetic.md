# Synthetic Student Dataset

**Author:** Ng Yong Hin (AI / NLP Engineer)

5,000 anonymised, synthetic student profiles for the SEAGAS POC. Every table and column
matches `database/schema.sql`. No real student data is used.

**v2 (Sprint 2):** the data is now generated against the skills library v2
(138 skills, `data/skills/skills_library.csv`). All 138 skills appear in
`student_skills` at least once.

> **Team note:** regenerating changes UUIDs and distributions. If you loaded the
> old data, first run `data/delete_synthetic_data.sql`, then load the new seed.

## Load into PostgreSQL (no Python needed)

Run `database/schema.sql`, `database/seed_skills_library_v2.sql` and
`database/seed_job_role_skills.sql` first (or run `backend/start_backend.bat`), then:

```bash
psql -U postgres -d seagas_db -f data/output/seed_synthetic_students.sql
```

This inserts rows into `users`, `student_profiles`, `student_skills`,
`student_projects` and `student_certifications`, all inside one transaction.

**Demo login:** any account from `student0001@synthetic.example.com` to
`student5000@synthetic.example.com`. The password is `Seagas@2026`.

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
python generate_synthetic_data.py              # 5000 students, seed 42 (default)
python generate_synthetic_data.py --n 500      # smaller demo dataset
```

The default is 5000 students, which matches the committed `data/output/`.
Use `--n 500` for a quick demo set.

- The role skill lists come from `database/seed_job_role_skills.sql`.
  `required` skills become the role's *core* skills, and `preferred` + `bonus`
  skills become *secondary*. Edit the role mappings there, not in the script.
- The script stops with an error if any role, project or certification uses a
  skill name that is not in `data/skills/skills_library.csv`. If the CSV is
  missing, it falls back to the 32 skills in `schema.sql`.
- Output is fully reproducible: the same seed gives byte-identical CSVs and
  SQL, including UUIDs and the bcrypt hash. Only the timestamp in the header
  lines changes.

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
  With seed 42, the mean core-skill coverage is 89.8% for strong, 71.6% for
  average and 39.7% for weak students (see `summary_stats.txt`). This gives the
  Advisor Dashboard a realistic spread of readiness scores.
- **Projects and certifications:** each role has 5–6 project templates that use
  v2 skills (for example a Mini SOC home lab or an Infrastructure-as-Code lab),
  plus 25 real certifications (CompTIA Security+, CEH, CCNA, AWS SAA, AZ-900,
  CKA, Terraform Associate, Google Data Analytics, PL-300 and others).
- **Consistent evidence:** skills used in a generated project get
  `evidence_type = project`, and skills covered by a certification get
  `certification`. The `project_count`, `certification_count` and
  `internship_count` fields match the rows in the detail tables.
- **Proficiency:** depends on archetype, year of study and whether there is
  evidence beyond coursework.
- **Noise:** 0–2 random off-role skills are added per student. They are
  drawn from the whole skills library.
- **Names:** romanised Malaysian names (Chinese, Malay and Indian) plus a few
  international names. All 5,000 names are unique (ignoring case and extra
  spaces), so students are easy to tell apart in the Advisor Dashboard.
- **Emails:** all use `synthetic.example.com`, a domain reserved for examples (RFC 2606). It passes Pydantic `EmailStr` validation, and no real address can be
  hit.
