-- ============================================================
-- SEAGAS — Seed data: skills per job role (job_role_skills)
-- Author: Ng Yong Hin
--
-- Maps each of the 6 job_roles to skills in skills_library, with an
-- importance level:
--   required  = core skill for an entry/junior hire in this role
--   preferred = commonly asked for, strengthens the application
--   bonus     = nice to have
--
-- Run AFTER database/schema.sql and database/seed_skills_library_v2.sql:
--   psql -U postgres -d seagas_db -f database/seed_skills_library_v2.sql
--   psql -U postgres -d seagas_db -f database/seed_job_role_skills.sql
--
-- Safe to run more than once: existing (role, skill) pairs are updated,
-- not duplicated, and pairs that are no longer listed for a role in this
-- file are removed. Roles and skills are matched by role_code and
-- skill_name, so the UUIDs in each person's database do not matter.
--
-- v2 (Sprint 2): uses the skills library v2 (data/skills/skills_library.csv).
-- Each role has ~8-10 required, 6-10 preferred and 4-8 bonus skills.
-- These lists are also read by data/generate_synthetic_data.py
-- (required -> core, preferred + bonus -> secondary), so keep the
-- one-row-per-line ('ROLE', 'Skill', 'importance') format.
--
-- TODO (after Phase 4): re-tune importance levels against the JD skill
-- frequency analysis (data/jd_dataset/jd_skill_frequency.csv).
-- ============================================================

\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP TABLE seed_role_skills (
    role_code  VARCHAR(30),
    skill_name VARCHAR(100),
    importance VARCHAR(10)
) ON COMMIT DROP;

INSERT INTO seed_role_skills (role_code, skill_name, importance) VALUES
    -- ── Data Analyst ──────────────────────────────────────
    ('DATA_ANALYST',    'SQL',                             'required'),
    ('DATA_ANALYST',    'Excel',                           'required'),
    ('DATA_ANALYST',    'Python',                          'required'),
    ('DATA_ANALYST',    'Power BI',                        'required'),
    ('DATA_ANALYST',    'Data Analysis',                   'required'),
    ('DATA_ANALYST',    'Data Visualisation',              'required'),
    ('DATA_ANALYST',    'Statistical Analysis',            'required'),
    ('DATA_ANALYST',    'Data Cleaning',                   'required'),
    ('DATA_ANALYST',    'Pandas',                          'required'),
    ('DATA_ANALYST',    'Tableau',                         'preferred'),
    ('DATA_ANALYST',    'ETL',                             'preferred'),
    ('DATA_ANALYST',    'Critical Thinking',               'preferred'),
    ('DATA_ANALYST',    'Problem Solving',                 'preferred'),
    ('DATA_ANALYST',    'Communication',                   'preferred'),
    ('DATA_ANALYST',    'Stakeholder Communication',       'preferred'),
    ('DATA_ANALYST',    'Presentation Skills',             'preferred'),
    ('DATA_ANALYST',    'Attention to Detail',             'preferred'),
    ('DATA_ANALYST',    'R',                               'bonus'),
    ('DATA_ANALYST',    'Machine Learning',                'bonus'),
    ('DATA_ANALYST',    'Git',                             'bonus'),
    ('DATA_ANALYST',    'Looker',                          'bonus'),
    ('DATA_ANALYST',    'Google Analytics',                'bonus'),
    ('DATA_ANALYST',    'A/B Testing',                     'bonus'),
    ('DATA_ANALYST',    'Data Warehousing',                'bonus'),

    -- ── Data Scientist ────────────────────────────────────
    ('DATA_SCIENTIST',  'Python',                          'required'),
    ('DATA_SCIENTIST',  'Machine Learning',                'required'),
    ('DATA_SCIENTIST',  'Statistical Analysis',            'required'),
    ('DATA_SCIENTIST',  'SQL',                             'required'),
    ('DATA_SCIENTIST',  'Data Analysis',                   'required'),
    ('DATA_SCIENTIST',  'Scikit-learn',                    'required'),
    ('DATA_SCIENTIST',  'Pandas',                          'required'),
    ('DATA_SCIENTIST',  'Feature Engineering',             'required'),
    ('DATA_SCIENTIST',  'Model Evaluation',                'required'),
    ('DATA_SCIENTIST',  'Deep Learning',                   'preferred'),
    ('DATA_SCIENTIST',  'NumPy',                           'preferred'),
    ('DATA_SCIENTIST',  'Data Visualisation',              'preferred'),
    ('DATA_SCIENTIST',  'Natural Language Processing',     'preferred'),
    ('DATA_SCIENTIST',  'Data Cleaning',                   'preferred'),
    ('DATA_SCIENTIST',  'Jupyter',                         'preferred'),
    ('DATA_SCIENTIST',  'Git',                             'preferred'),
    ('DATA_SCIENTIST',  'Problem Solving',                 'preferred'),
    ('DATA_SCIENTIST',  'Communication',                   'preferred'),
    ('DATA_SCIENTIST',  'R',                               'bonus'),
    ('DATA_SCIENTIST',  'TensorFlow',                      'bonus'),
    ('DATA_SCIENTIST',  'PyTorch',                         'bonus'),
    ('DATA_SCIENTIST',  'Apache Spark',                    'bonus'),
    ('DATA_SCIENTIST',  'MLOps',                           'bonus'),
    ('DATA_SCIENTIST',  'Generative AI',                   'bonus'),
    ('DATA_SCIENTIST',  'Cloud Computing',                 'bonus'),
    ('DATA_SCIENTIST',  'Research Skills',                 'bonus'),

    -- ── Software Developer ────────────────────────────────
    ('SOFTWARE_DEV',    'Java',                            'required'),
    ('SOFTWARE_DEV',    'Python',                          'required'),
    ('SOFTWARE_DEV',    'JavaScript',                      'required'),
    ('SOFTWARE_DEV',    'Git',                             'required'),
    ('SOFTWARE_DEV',    'SQL',                             'required'),
    ('SOFTWARE_DEV',    'Object-Oriented Programming',     'required'),
    ('SOFTWARE_DEV',    'Data Structures & Algorithms',    'required'),
    ('SOFTWARE_DEV',    'Unit Testing',                    'required'),
    ('SOFTWARE_DEV',    'REST API',                        'required'),
    ('SOFTWARE_DEV',    'Problem Solving',                 'required'),
    ('SOFTWARE_DEV',    'Docker',                          'preferred'),
    ('SOFTWARE_DEV',    'Linux',                           'preferred'),
    ('SOFTWARE_DEV',    'CI/CD',                           'preferred'),
    ('SOFTWARE_DEV',    'Agile / Scrum',                   'preferred'),
    ('SOFTWARE_DEV',    'Spring Boot',                     'preferred'),
    ('SOFTWARE_DEV',    'C#',                              'preferred'),
    ('SOFTWARE_DEV',    'Teamwork',                        'preferred'),
    ('SOFTWARE_DEV',    'Communication',                   'preferred'),
    ('SOFTWARE_DEV',    'C++',                             'bonus'),
    ('SOFTWARE_DEV',    'TypeScript',                      'bonus'),
    ('SOFTWARE_DEV',    'Microservices',                   'bonus'),
    ('SOFTWARE_DEV',    'Cloud Computing',                 'bonus'),
    ('SOFTWARE_DEV',    'FastAPI',                         'bonus'),
    ('SOFTWARE_DEV',    'Node.js',                         'bonus'),
    ('SOFTWARE_DEV',    'React',                           'bonus'),

    -- ── Cybersecurity Analyst ─────────────────────────────
    ('CYBER_ANALYST',   'Cybersecurity',                   'required'),
    ('CYBER_ANALYST',   'Network Security',                'required'),
    ('CYBER_ANALYST',   'Networking',                      'required'),
    ('CYBER_ANALYST',   'Linux',                           'required'),
    ('CYBER_ANALYST',   'SIEM',                            'required'),
    ('CYBER_ANALYST',   'Incident Response',               'required'),
    ('CYBER_ANALYST',   'Vulnerability Assessment',        'required'),
    ('CYBER_ANALYST',   'Security Operations (SOC)',       'required'),
    ('CYBER_ANALYST',   'Log Analysis',                    'required'),
    ('CYBER_ANALYST',   'Problem Solving',                 'required'),
    ('CYBER_ANALYST',   'Python',                          'preferred'),
    ('CYBER_ANALYST',   'Firewall Management',             'preferred'),
    ('CYBER_ANALYST',   'Wireshark',                       'preferred'),
    ('CYBER_ANALYST',   'Security Frameworks',             'preferred'),
    ('CYBER_ANALYST',   'Threat Intelligence',             'preferred'),
    ('CYBER_ANALYST',   'Identity & Access Management',    'preferred'),
    ('CYBER_ANALYST',   'Windows Server',                  'preferred'),
    ('CYBER_ANALYST',   'Cloud Computing',                 'preferred'),
    ('CYBER_ANALYST',   'AWS',                             'preferred'),
    ('CYBER_ANALYST',   'Communication',                   'preferred'),
    ('CYBER_ANALYST',   'Ethical Hacking',                 'bonus'),
    ('CYBER_ANALYST',   'Nmap',                            'bonus'),
    ('CYBER_ANALYST',   'Splunk',                          'bonus'),
    ('CYBER_ANALYST',   'Digital Forensics',               'bonus'),
    ('CYBER_ANALYST',   'Cryptography',                    'bonus'),
    ('CYBER_ANALYST',   'Kali Linux',                      'bonus'),
    ('CYBER_ANALYST',   'Bash',                            'bonus'),
    ('CYBER_ANALYST',   'Risk Analysis',                   'bonus'),

    -- ── Cloud Engineer ────────────────────────────────────
    ('CLOUD_ENGINEER',  'Cloud Computing',                 'required'),
    ('CLOUD_ENGINEER',  'AWS',                             'required'),
    ('CLOUD_ENGINEER',  'Linux',                           'required'),
    ('CLOUD_ENGINEER',  'Docker',                          'required'),
    ('CLOUD_ENGINEER',  'Kubernetes',                      'required'),
    ('CLOUD_ENGINEER',  'Terraform',                       'required'),
    ('CLOUD_ENGINEER',  'CI/CD',                           'required'),
    ('CLOUD_ENGINEER',  'Networking',                      'required'),
    ('CLOUD_ENGINEER',  'Identity & Access Management',    'required'),
    ('CLOUD_ENGINEER',  'Git',                             'required'),
    ('CLOUD_ENGINEER',  'Azure',                           'preferred'),
    ('CLOUD_ENGINEER',  'GCP',                             'preferred'),
    ('CLOUD_ENGINEER',  'Python',                          'preferred'),
    ('CLOUD_ENGINEER',  'Bash',                            'preferred'),
    ('CLOUD_ENGINEER',  'Monitoring & Observability',      'preferred'),
    ('CLOUD_ENGINEER',  'Serverless',                      'preferred'),
    ('CLOUD_ENGINEER',  'Ansible',                         'preferred'),
    ('CLOUD_ENGINEER',  'Problem Solving',                 'preferred'),
    ('CLOUD_ENGINEER',  'Teamwork',                        'preferred'),
    ('CLOUD_ENGINEER',  'Go',                              'bonus'),
    ('CLOUD_ENGINEER',  'Network Security',                'bonus'),
    ('CLOUD_ENGINEER',  'SQL',                             'bonus'),
    ('CLOUD_ENGINEER',  'Microservices',                   'bonus'),
    ('CLOUD_ENGINEER',  'PowerShell',                      'bonus'),
    ('CLOUD_ENGINEER',  'Documentation',                   'bonus'),

    -- ── Web Developer ─────────────────────────────────────
    ('WEB_DEV',         'JavaScript',                      'required'),
    ('WEB_DEV',         'TypeScript',                      'required'),
    ('WEB_DEV',         'HTML',                            'required'),
    ('WEB_DEV',         'CSS',                             'required'),
    ('WEB_DEV',         'React',                           'required'),
    ('WEB_DEV',         'Node.js',                         'required'),
    ('WEB_DEV',         'REST API',                        'required'),
    ('WEB_DEV',         'Git',                             'required'),
    ('WEB_DEV',         'SQL',                             'required'),
    ('WEB_DEV',         'Express.js',                      'preferred'),
    ('WEB_DEV',         'PostgreSQL',                      'preferred'),
    ('WEB_DEV',         'UI/UX Design',                    'preferred'),
    ('WEB_DEV',         'Unit Testing',                    'preferred'),
    ('WEB_DEV',         'Agile / Scrum',                   'preferred'),
    ('WEB_DEV',         'Teamwork',                        'preferred'),
    ('WEB_DEV',         'Communication',                   'preferred'),
    ('WEB_DEV',         'Problem Solving',                 'preferred'),
    ('WEB_DEV',         'Vue.js',                          'bonus'),
    ('WEB_DEV',         'Python',                          'bonus'),
    ('WEB_DEV',         'PHP',                             'bonus'),
    ('WEB_DEV',         'MongoDB',                         'bonus'),
    ('WEB_DEV',         'GraphQL',                         'bonus'),
    ('WEB_DEV',         'Docker',                          'bonus'),
    ('WEB_DEV',         'Figma',                           'bonus');

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

-- Remove mappings that are no longer listed for a seeded role
-- (e.g. v1 placeholder skills that were replaced).
DELETE FROM job_role_skills jrs
USING job_roles jr
WHERE jrs.role_id = jr.role_id
  AND jr.role_code IN (SELECT DISTINCT role_code FROM seed_role_skills)
  AND NOT EXISTS (
        SELECT 1
        FROM seed_role_skills s
        JOIN skills_library sl ON sl.skill_name = s.skill_name
        WHERE s.role_code = jr.role_code
          AND sl.skill_id = jrs.skill_id);

INSERT INTO job_role_skills (role_id, skill_id, importance)
SELECT jr.role_id, sl.skill_id, s.importance
FROM seed_role_skills s
JOIN job_roles      jr ON jr.role_code  = s.role_code
JOIN skills_library sl ON sl.skill_name = s.skill_name
ON CONFLICT (role_id, skill_id) DO UPDATE SET importance = EXCLUDED.importance;

COMMIT;
