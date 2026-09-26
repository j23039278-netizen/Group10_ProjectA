-- ============================================================
-- SEAGAS — Seed data: required skills per job role (job_role_skills)
-- Author: Ng Yong Hin
--
-- Maps each of the 6 job_roles to skills in skills_library, with an
-- importance level:
--   required  = core skill for an entry/junior hire in this role
--   preferred = commonly asked for, strengthens the application
--   bonus     = nice to have
--
-- Run AFTER database/schema.sql:
--   psql -U postgres -d seagas_db -f database/seed_job_role_skills.sql
--
-- Safe to run more than once: existing (role, skill) pairs are updated,
-- not duplicated. Roles and skills are matched by role_code and
-- skill_name, so the UUIDs in each person's database do not matter.
--
-- NOTE: uses only the 32 skills currently in skills_library. When the
-- library is expanded to 100–150 skills, extend these lists (e.g. add
-- network security / SIEM skills to CYBER_ANALYST) and validate them
-- against the collected job-description dataset.
-- ============================================================

BEGIN;

CREATE TEMP TABLE seed_role_skills (
    role_code  VARCHAR(30),
    skill_name VARCHAR(100),
    importance VARCHAR(10)
) ON COMMIT DROP;

INSERT INTO seed_role_skills (role_code, skill_name, importance) VALUES
    -- ── Data Analyst ─────────────────────────────────────────
    ('DATA_ANALYST', 'SQL',                         'required'),
    ('DATA_ANALYST', 'Excel',                       'required'),
    ('DATA_ANALYST', 'Python',                      'required'),
    ('DATA_ANALYST', 'Power BI',                    'required'),
    ('DATA_ANALYST', 'Data Analysis',               'required'),
    ('DATA_ANALYST', 'Data Visualisation',          'required'),
    ('DATA_ANALYST', 'Statistical Analysis',        'required'),
    ('DATA_ANALYST', 'Communication',               'preferred'),
    ('DATA_ANALYST', 'Tableau',                     'preferred'),
    ('DATA_ANALYST', 'Problem Solving',             'preferred'),
    ('DATA_ANALYST', 'R',                           'bonus'),
    ('DATA_ANALYST', 'Machine Learning',            'bonus'),
    ('DATA_ANALYST', 'Git',                         'bonus'),

    -- ── Data Scientist ───────────────────────────────────────
    ('DATA_SCIENTIST', 'Python',                    'required'),
    ('DATA_SCIENTIST', 'Machine Learning',          'required'),
    ('DATA_SCIENTIST', 'Statistical Analysis',      'required'),
    ('DATA_SCIENTIST', 'SQL',                       'required'),
    ('DATA_SCIENTIST', 'Data Analysis',             'required'),
    ('DATA_SCIENTIST', 'Deep Learning',             'required'),
    ('DATA_SCIENTIST', 'Data Visualisation',        'preferred'),
    ('DATA_SCIENTIST', 'Natural Language Processing','preferred'),
    ('DATA_SCIENTIST', 'Git',                       'preferred'),
    ('DATA_SCIENTIST', 'Problem Solving',           'preferred'),
    ('DATA_SCIENTIST', 'Communication',             'preferred'),
    ('DATA_SCIENTIST', 'R',                         'bonus'),
    ('DATA_SCIENTIST', 'Cloud Computing',           'bonus'),
    ('DATA_SCIENTIST', 'Research Skills',           'bonus'),
    ('DATA_SCIENTIST', 'AI Literacy',               'bonus'),

    -- ── Software Developer ───────────────────────────────────
    ('SOFTWARE_DEV', 'Java',                        'required'),
    ('SOFTWARE_DEV', 'Python',                      'required'),
    ('SOFTWARE_DEV', 'JavaScript',                  'required'),
    ('SOFTWARE_DEV', 'Git',                         'required'),
    ('SOFTWARE_DEV', 'SQL',                         'required'),
    ('SOFTWARE_DEV', 'Problem Solving',             'required'),
    ('SOFTWARE_DEV', 'Docker',                      'preferred'),
    ('SOFTWARE_DEV', 'Linux',                       'preferred'),
    ('SOFTWARE_DEV', 'Teamwork',                    'preferred'),
    ('SOFTWARE_DEV', 'Communication',               'preferred'),
    ('SOFTWARE_DEV', 'C++',                         'bonus'),
    ('SOFTWARE_DEV', 'FastAPI',                     'bonus'),
    ('SOFTWARE_DEV', 'Flask',                       'bonus'),
    ('SOFTWARE_DEV', 'Node.js',                     'bonus'),
    ('SOFTWARE_DEV', 'React',                       'bonus'),

    -- ── Cybersecurity Analyst ────────────────────────────────
    ('CYBER_ANALYST', 'Linux',                      'required'),
    ('CYBER_ANALYST', 'Problem Solving',            'required'),
    ('CYBER_ANALYST', 'Python',                     'required'),
    ('CYBER_ANALYST', 'Cloud Computing',            'required'),
    ('CYBER_ANALYST', 'Communication',              'preferred'),
    ('CYBER_ANALYST', 'SQL',                        'preferred'),
    ('CYBER_ANALYST', 'AWS',                        'preferred'),
    ('CYBER_ANALYST', 'Azure',                      'preferred'),
    ('CYBER_ANALYST', 'Research Skills',            'preferred'),
    ('CYBER_ANALYST', 'Docker',                     'bonus'),
    ('CYBER_ANALYST', 'Git',                        'bonus'),
    ('CYBER_ANALYST', 'C++',                        'bonus'),

    -- ── Cloud Engineer ───────────────────────────────────────
    ('CLOUD_ENGINEER', 'Cloud Computing',           'required'),
    ('CLOUD_ENGINEER', 'AWS',                       'required'),
    ('CLOUD_ENGINEER', 'Linux',                     'required'),
    ('CLOUD_ENGINEER', 'Docker',                    'required'),
    ('CLOUD_ENGINEER', 'Git',                       'required'),
    ('CLOUD_ENGINEER', 'Azure',                     'preferred'),
    ('CLOUD_ENGINEER', 'Python',                    'preferred'),
    ('CLOUD_ENGINEER', 'Problem Solving',           'preferred'),
    ('CLOUD_ENGINEER', 'Teamwork',                  'preferred'),
    ('CLOUD_ENGINEER', 'SQL',                       'bonus'),
    ('CLOUD_ENGINEER', 'Node.js',                   'bonus'),

    -- ── Web Developer ────────────────────────────────────────
    ('WEB_DEV', 'JavaScript',                       'required'),
    ('WEB_DEV', 'React',                            'required'),
    ('WEB_DEV', 'Node.js',                          'required'),
    ('WEB_DEV', 'Git',                              'required'),
    ('WEB_DEV', 'SQL',                              'required'),
    ('WEB_DEV', 'Python',                           'preferred'),
    ('WEB_DEV', 'Teamwork',                         'preferred'),
    ('WEB_DEV', 'Communication',                    'preferred'),
    ('WEB_DEV', 'Problem Solving',                  'preferred'),
    ('WEB_DEV', 'Docker',                           'bonus'),
    ('WEB_DEV', 'Flask',                            'bonus'),
    ('WEB_DEV', 'FastAPI',                          'bonus'),
    ('WEB_DEV', 'Data Visualisation',               'bonus');

-- Fail loudly if any role_code or skill_name is misspelled or missing,
-- instead of silently skipping that row.
DO $$
DECLARE missing TEXT;
BEGIN
    SELECT string_agg(s.role_code || ' / ' || s.skill_name, ', ') INTO missing
    FROM seed_role_skills s
    LEFT JOIN job_roles      jr ON jr.role_code  = s.role_code
    LEFT JOIN skills_library sl ON sl.skill_name = s.skill_name
    WHERE jr.role_id IS NULL OR sl.skill_id IS NULL;
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'Unknown role or skill in seed: %', missing;
    END IF;
END $$;

INSERT INTO job_role_skills (role_id, skill_id, importance)
SELECT jr.role_id, sl.skill_id, s.importance
FROM seed_role_skills s
JOIN job_roles      jr ON jr.role_code  = s.role_code
JOIN skills_library sl ON sl.skill_name = s.skill_name
ON CONFLICT (role_id, skill_id) DO UPDATE SET importance = EXCLUDED.importance;

COMMIT;
