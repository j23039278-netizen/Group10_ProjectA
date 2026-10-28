-- ============================================================
-- SEAGAS — Upgrade an existing local database to the current schema.sql
--
-- schema.sql only runs on a brand-new database, so changes made to it later
-- never reach databases that were created before. This file applies those
-- changes. It is idempotent and start_backend.bat runs it on every start,
-- right after the schema check and before the seed files.
--
-- Run manually:
--     psql -U postgres -d seagas_db -f database/migrate_existing_db.sql
-- ============================================================

\set ON_ERROR_STOP on
SET client_min_messages = warning;   -- hide "already exists, skipping" notices

BEGIN;

-- skills_library: subcategory + source (Sprint 1 report, Figure 44)
ALTER TABLE skills_library ADD COLUMN IF NOT EXISTS subcategory VARCHAR(50);
ALTER TABLE skills_library ADD COLUMN IF NOT EXISTS source      VARCHAR(10);

-- student_resource_progress (FR-11): may be missing on databases created
-- before development tracking was added
CREATE TABLE IF NOT EXISTS student_resource_progress (
    progress_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id    UUID NOT NULL REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    resource_id   UUID NOT NULL REFERENCES recommendations_library(resource_id) ON DELETE CASCADE,
    assessment_id UUID REFERENCES assessments(assessment_id) ON DELETE SET NULL,
    skill_id      UUID REFERENCES skills_library(skill_id) ON DELETE SET NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'saved'
                  CHECK (status IN ('saved', 'in_progress', 'completed')),
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    skill_added   BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(profile_id, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_srp_profile ON student_resource_progress(profile_id);
CREATE INDEX IF NOT EXISTS idx_srp_status  ON student_resource_progress(profile_id, status);

-- recommendations_library: one row per (skill, resource title), so the
-- recommendations seed can run on every start without adding duplicates.
-- Older databases may already hold duplicates from running the seed twice;
-- keep the oldest copy and move any progress/recommendation rows onto it.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_resource_skill') THEN
        CREATE TEMP TABLE rl_dupes ON COMMIT DROP AS
        SELECT resource_id AS dupe_id, keep_id
        FROM (
            SELECT resource_id,
                   FIRST_VALUE(resource_id) OVER w AS keep_id,
                   ROW_NUMBER()             OVER w AS rn
            FROM recommendations_library
            WINDOW w AS (PARTITION BY skill_id, resource_title ORDER BY created_at, resource_id)
        ) ranked
        WHERE rn > 1;

        -- Move references to the kept copy, unless the student already has it
        UPDATE student_resource_progress srp SET resource_id = d.keep_id
        FROM rl_dupes d
        WHERE srp.resource_id = d.dupe_id
          AND NOT EXISTS (SELECT 1 FROM student_resource_progress x
                          WHERE x.profile_id = srp.profile_id AND x.resource_id = d.keep_id);
        UPDATE student_recommendations sr SET resource_id = d.keep_id
        FROM rl_dupes d
        WHERE sr.resource_id = d.dupe_id
          AND NOT EXISTS (SELECT 1 FROM student_recommendations x
                          WHERE x.assessment_id = sr.assessment_id AND x.resource_id = d.keep_id);
        DELETE FROM student_recommendations WHERE resource_id IN (SELECT dupe_id FROM rl_dupes);

        DELETE FROM recommendations_library WHERE resource_id IN (SELECT dupe_id FROM rl_dupes);
        ALTER TABLE recommendations_library
            ADD CONSTRAINT uq_resource_skill UNIQUE (skill_id, resource_title);
    END IF;
END $$;

-- skill_match_results.reason: the NLP matcher's one-sentence explanation
-- (docs/NLP_INTERFACE.md 6d), shown on the Skill Gap page
ALTER TABLE skill_match_results ADD COLUMN IF NOT EXISTS reason TEXT;

-- v_student_progress: read from student_resource_progress, which the app
-- writes to. It used to read student_recommendations, which nothing writes,
-- so the advisor cohort progress endpoint always returned an empty list.
CREATE OR REPLACE VIEW v_student_progress AS
SELECT
    sp.user_id,
    u.full_name,
    COUNT(*) FILTER (WHERE srp.status = 'completed')   AS completed_tasks,
    COUNT(*) FILTER (WHERE srp.status = 'in_progress') AS in_progress_tasks,
    COUNT(*) FILTER (WHERE srp.status = 'saved')       AS pending_tasks,
    COUNT(*)                                            AS total_tasks
FROM student_resource_progress srp
JOIN student_profiles sp ON sp.profile_id = srp.profile_id
JOIN users u             ON u.user_id     = sp.user_id
GROUP BY sp.user_id, u.full_name;

-- View: cohort skill gap summary (used by Advisor Dashboard cohort bar chart)
-- Only each student's latest assessment counts, so a student who ran several
-- assessments is not counted several times. total_assessments = students counted.
CREATE OR REPLACE VIEW v_cohort_skill_gaps AS
WITH latest AS (
    SELECT DISTINCT ON (profile_id) assessment_id
    FROM assessments
    ORDER BY profile_id, created_at DESC
)
SELECT
    sl.skill_name,
    sl.category,
    COUNT(*) FILTER (WHERE smr.match_status = 'gap')        AS gap_count,
    COUNT(*) FILTER (WHERE smr.match_status = 'developing') AS developing_count,
    COUNT(*) FILTER (WHERE smr.match_status = 'strong')     AS strong_count,
    COUNT(*)                                                 AS total_assessments,
    ROUND(
        COUNT(*) FILTER (WHERE smr.match_status = 'gap') * 100.0 / NULLIF(COUNT(*), 0),
        1
    )                                                        AS gap_percentage
FROM skill_match_results smr
JOIN latest l          ON l.assessment_id = smr.assessment_id
JOIN skills_library sl ON sl.skill_id = smr.skill_id
GROUP BY sl.skill_id, sl.skill_name, sl.category
ORDER BY gap_percentage DESC;

-- ── Audit log (NFR: security and accountability) ──────────────
-- Who did what and when: sign-ins (also failed), registrations, assessments,
-- JD analyses, advisors opening a student's record, admin account changes.
-- Written by backend/audit.py; read by GET /api/admin/audit-log.
CREATE TABLE IF NOT EXISTS audit_log (
    log_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES users(user_id) ON DELETE SET NULL,  -- NULL: anonymous (failed login)
    actor_email  VARCHAR(255),          -- kept if the account is deleted; attempted email on failed login
    actor_role   VARCHAR(20),
    action       VARCHAR(50)  NOT NULL, -- e.g. 'auth.login', 'assessment.run', 'admin.user_update'
    target_type  VARCHAR(30),           -- e.g. 'user', 'assessment', 'job_description'
    target_id    VARCHAR(64),
    details      JSONB,                 -- never passwords or tokens
    ip_address   VARCHAR(45),
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action     ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id    ON audit_log(user_id);

-- job_roles.source: 'seed' roles are maintained by the seed files, 'admin' roles
-- are added and edited in the Admin page
ALTER TABLE job_roles ADD COLUMN IF NOT EXISTS source VARCHAR(10) NOT NULL DEFAULT 'seed';

-- recommendations_library.source: same rule as job_roles. 'seed' resources come from
-- seed_recommendations_library_final.sql; 'admin' resources are added and edited in
-- the Admin page (Learning Resources)
ALTER TABLE recommendations_library ADD COLUMN IF NOT EXISTS source VARCHAR(10) NOT NULL DEFAULT 'seed';

-- student_profiles.is_complete: the backend now keeps it up to date (same rule as
-- refresh_profile_complete in backend/routers/students.py). Profiles saved before that
-- were left FALSE, so recompute them. Synthetic students keep their generated value.
UPDATE student_profiles sp SET is_complete = (
    COALESCE(TRIM(sp.programme), '')   <> ''
    AND COALESCE(TRIM(sp.university), '') <> ''
    AND sp.year_of_study IS NOT NULL
    AND COALESCE(TRIM(sp.target_role), '') <> ''
    AND EXISTS (SELECT 1 FROM student_skills ss WHERE ss.profile_id = sp.profile_id)
)
FROM users u
WHERE u.user_id = sp.user_id AND u.email NOT LIKE '%@synthetic.example.com';

-- Evidence files for projects and certifications (same definition as schema.sql)
CREATE TABLE IF NOT EXISTS student_evidence_files (
    file_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id    UUID NOT NULL REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    project_id    UUID REFERENCES student_projects(project_id) ON DELETE CASCADE,
    cert_id       UUID REFERENCES student_certifications(cert_id) ON DELETE CASCADE,
    file_name     VARCHAR(255) NOT NULL,
    content_type  VARCHAR(50)  NOT NULL
                  CHECK (content_type IN ('image/jpeg', 'image/png', 'application/pdf')),
    size_bytes    INTEGER      NOT NULL CHECK (size_bytes BETWEEN 1 AND 5242880),
    data          BYTEA        NOT NULL,
    uploaded_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_evidence_one_parent CHECK ((project_id IS NULL) <> (cert_id IS NULL))
);
CREATE INDEX IF NOT EXISTS idx_evidence_project ON student_evidence_files(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_cert    ON student_evidence_files(cert_id);

-- Evidence v2 (27 October): evidence can also be a link (videos, GitHub, Drive,
-- credential pages), files can be Word / PowerPoint, and evidence can belong to a
-- recommended activity (student_resource_progress): a student must attach at
-- least one piece before marking an activity complete. Safe to run more than once.
ALTER TABLE student_evidence_files ADD COLUMN IF NOT EXISTS kind VARCHAR(4) NOT NULL DEFAULT 'file';
ALTER TABLE student_evidence_files ADD COLUMN IF NOT EXISTS link_url TEXT;
ALTER TABLE student_evidence_files ADD COLUMN IF NOT EXISTS progress_id UUID
    REFERENCES student_resource_progress(progress_id) ON DELETE CASCADE;
ALTER TABLE student_evidence_files ALTER COLUMN data DROP NOT NULL;
ALTER TABLE student_evidence_files ALTER COLUMN content_type DROP NOT NULL;
-- Office type names are longer than 50 characters
ALTER TABLE student_evidence_files ALTER COLUMN content_type TYPE VARCHAR(100);
ALTER TABLE student_evidence_files ALTER COLUMN size_bytes DROP NOT NULL;
ALTER TABLE student_evidence_files DROP CONSTRAINT IF EXISTS chk_evidence_one_parent;
ALTER TABLE student_evidence_files DROP CONSTRAINT IF EXISTS student_evidence_files_content_type_check;
ALTER TABLE student_evidence_files DROP CONSTRAINT IF EXISTS student_evidence_files_size_bytes_check;
ALTER TABLE student_evidence_files DROP CONSTRAINT IF EXISTS chk_evidence_kind;
-- Exactly one owner: a project, a certification or a recommended activity
ALTER TABLE student_evidence_files ADD CONSTRAINT chk_evidence_one_parent
    CHECK (num_nonnulls(project_id, cert_id, progress_id) = 1);
-- A file has bytes of an allowed type (max 5 MB); a link has only an http(s) URL
ALTER TABLE student_evidence_files ADD CONSTRAINT chk_evidence_kind CHECK (
    (kind = 'file' AND data IS NOT NULL AND link_url IS NULL
        AND size_bytes BETWEEN 1 AND 5242880
        AND content_type IN ('image/jpeg', 'image/png', 'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'))
    OR (kind = 'link' AND data IS NULL AND content_type IS NULL AND size_bytes IS NULL
        AND link_url ~* '^https?://[^[:space:]]+$' AND length(link_url) <= 2000));
CREATE INDEX IF NOT EXISTS idx_evidence_progress ON student_evidence_files(progress_id);

-- ── Student accounts: student number, intake, first-login password ──
-- Students do not register themselves. An advisor uploads a list of new students
-- (student_intake_*), an admin creates their accounts with a student number and a
-- school email, and the student gets a temporary password by email
-- (email_outbox when no mail server is configured). must_change_password makes
-- the student choose a new password at first sign-in (also after an admin reset).
-- Safe to run more than once.
ALTER TABLE users ADD COLUMN IF NOT EXISTS student_number VARCHAR(9);
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_student_number ON users(student_number);

-- Numbers suggested for new students. Real Swinburne numbers look like 105967029;
-- 9xxxxxxxx is kept for the synthetic test students.
CREATE SEQUENCE IF NOT EXISTS student_number_seq START WITH 107000001 MINVALUE 100000000 MAXVALUE 899999999;

-- Next free student number. Synthetic test students get a fixed one from their
-- email (student0001@synthetic.example.com -> 900000001), so it is the same in
-- every teammate's database.
CREATE OR REPLACE FUNCTION next_student_number(p_email TEXT) RETURNS VARCHAR AS $$
DECLARE
    n VARCHAR(9);
BEGIN
    IF lower(p_email) ~ '^student[0-9]{1,8}@synthetic\.example\.com$' THEN
        RETURN '9' || lpad(substring(lower(p_email) from '^student([0-9]+)@'), 8, '0');
    END IF;
    LOOP
        n := nextval('student_number_seq')::text;
        EXIT WHEN NOT EXISTS (SELECT 1 FROM users WHERE student_number = n);
    END LOOP;
    RETURN n;
END $$ LANGUAGE plpgsql;

-- Every student account gets a number, whichever way it is inserted (intake,
-- synthetic seed file, tests): the seed files need no change.
CREATE OR REPLACE FUNCTION users_assign_student_number() RETURNS trigger AS $$
BEGIN
    IF NEW.role = 'student' AND NEW.student_number IS NULL THEN
        NEW.student_number := next_student_number(NEW.email);
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_student_number ON users;
CREATE TRIGGER trg_users_student_number
    BEFORE INSERT OR UPDATE OF role, student_number ON users
    FOR EACH ROW EXECUTE FUNCTION users_assign_student_number();

UPDATE users SET student_number = next_student_number(email)
WHERE role = 'student' AND student_number IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_users_student_number') THEN
        ALTER TABLE users ADD CONSTRAINT chk_users_student_number CHECK (
            (role = 'student' AND student_number ~ '^[0-9]{9}$')
            OR (role <> 'student' AND student_number IS NULL));
    END IF;
END $$;

-- A list of new students uploaded by an advisor (Excel / CSV)
CREATE TABLE IF NOT EXISTS student_intake_batches (
    batch_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by  UUID REFERENCES users(user_id) ON DELETE SET NULL,
    file_name    VARCHAR(255) NOT NULL,
    uploaded_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One new student from that list. student_number / school_email are what the
-- admin assigns (suggested by the system, editable) until the account is created.
CREATE TABLE IF NOT EXISTS student_intake_rows (
    row_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id        UUID NOT NULL REFERENCES student_intake_batches(batch_id) ON DELETE CASCADE,
    line_number     INTEGER      NOT NULL,                     -- row in the uploaded file
    full_name       VARCHAR(255) NOT NULL,
    phone           VARCHAR(30),
    personal_email  VARCHAR(255) NOT NULL,
    student_number  VARCHAR(9),
    school_email    VARCHAR(255),
    status          VARCHAR(10)  NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'created', 'rejected')),
    user_id         UUID REFERENCES users(user_id) ON DELETE SET NULL,   -- the account created
    note            TEXT,                                               -- why it was rejected
    processed_by    UUID REFERENCES users(user_id) ON DELETE SET NULL,
    processed_at    TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_intake_rows_batch  ON student_intake_rows(batch_id);
CREATE INDEX IF NOT EXISTS idx_intake_rows_status ON student_intake_rows(status);

-- Every notification email. status 'not_sent' = no mail server configured
-- (SMTP_HOST in backend/.env), so admins read it here and pass it on.
CREATE TABLE IF NOT EXISTS email_outbox (
    email_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    to_address       VARCHAR(255) NOT NULL,
    subject          VARCHAR(255) NOT NULL,
    body             TEXT         NOT NULL,
    status           VARCHAR(10)  NOT NULL CHECK (status IN ('sent', 'not_sent', 'failed')),
    error            TEXT,
    related_user_id  UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_email_outbox_created ON email_outbox(created_at DESC);


-- ── Course (27 October): every student belongs to Computer Science, Business or ICT ──
-- Set by the admin from the advisor's intake list (the Course column). Students
-- cannot change it. Synthetic students are split evenly by number: student N
-- -> N mod 3 = 1 CS, 2 BUSINESS, 0 ICT, the same in every database. Any other
-- student inserted without a course (tests, scripts) gets CS. Safe to run again.
ALTER TABLE users ADD COLUMN IF NOT EXISTS course VARCHAR(10);
ALTER TABLE student_intake_rows ADD COLUMN IF NOT EXISTS course VARCHAR(10);

CREATE OR REPLACE FUNCTION default_course(p_email TEXT) RETURNS VARCHAR AS $$
DECLARE
    n BIGINT;
BEGIN
    IF lower(p_email) ~ '^student[0-9]{1,8}@synthetic\.example\.com$' THEN
        n := substring(lower(p_email) from '^student([0-9]+)@')::BIGINT;
        RETURN CASE n % 3 WHEN 1 THEN 'CS' WHEN 2 THEN 'BUSINESS' ELSE 'ICT' END;
    END IF;
    RETURN 'CS';
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION users_assign_course() RETURNS trigger AS $$
BEGIN
    IF NEW.role = 'student' AND NEW.course IS NULL THEN
        NEW.course := default_course(NEW.email);
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_course ON users;
CREATE TRIGGER trg_users_course
    BEFORE INSERT OR UPDATE OF role, course ON users
    FOR EACH ROW EXECUTE FUNCTION users_assign_course();

UPDATE users SET course = default_course(email) WHERE role = 'student' AND course IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_users_course') THEN
        ALTER TABLE users ADD CONSTRAINT chk_users_course CHECK (
            (role = 'student' AND course IN ('CS', 'BUSINESS', 'ICT'))
            OR (role <> 'student' AND course IS NULL));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_intake_course') THEN
        ALTER TABLE student_intake_rows ADD CONSTRAINT chk_intake_course
            CHECK (course IS NULL OR course IN ('CS', 'BUSINESS', 'ICT'));
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_users_course ON users(course);

-- Synthetic students: programme name matching their course, chosen by target role.
-- Only rows that do not match yet are changed, so running this again changes nothing.
-- (start_backend.bat runs this file again right after loading the synthetic students.)
UPDATE student_profiles sp SET programme = CASE u.course
        WHEN 'BUSINESS' THEN CASE WHEN sp.target_role IN ('Data Analyst', 'Data Scientist')
                                  THEN 'Bachelor of Business (Business Analytics)'
                                  ELSE 'Bachelor of Business (Information Systems)' END
        WHEN 'ICT' THEN CASE sp.target_role
                            WHEN 'Cybersecurity Analyst' THEN 'Bachelor of Information and Communication Technology (Network Security)'
                            WHEN 'Cloud Engineer'        THEN 'Bachelor of Information and Communication Technology (Cloud and Networking)'
                            WHEN 'Data Analyst'          THEN 'Bachelor of Information and Communication Technology (Data Management)'
                            WHEN 'Data Scientist'        THEN 'Bachelor of Information and Communication Technology (Data Management)'
                            ELSE 'Bachelor of Information and Communication Technology (Software Systems)' END
        ELSE CASE sp.target_role
                 WHEN 'Cybersecurity Analyst' THEN 'Bachelor of Computer Science (Cybersecurity)'
                 WHEN 'Cloud Engineer'        THEN 'Bachelor of Computer Science (Cloud Computing)'
                 WHEN 'Data Analyst'          THEN 'Bachelor of Computer Science (Data Science)'
                 WHEN 'Data Scientist'        THEN 'Bachelor of Computer Science (Data Science)'
                 ELSE 'Bachelor of Computer Science (Software Development)' END
    END,
    updated_at = CURRENT_TIMESTAMP
FROM users u
WHERE u.user_id = sp.user_id
  AND u.email LIKE '%@synthetic.example.com'
  AND NOT (   (u.course = 'BUSINESS' AND sp.programme LIKE 'Bachelor of Business%')
           OR (u.course = 'ICT'      AND sp.programme LIKE 'Bachelor of Information and Communication Technology%')
           OR (u.course = 'CS'       AND (sp.programme LIKE 'Bachelor of Computer Science%'
                                          OR sp.programme LIKE 'Bachelor of Software Engineering%')));


-- ── Roles per course, Business roles, GPA + CGPA (27 October) ──
-- job_roles.courses: which courses' students may choose the role as target role.
-- CS: all 6 IT roles; ICT: 4 of them; Business: the Business roles below. Like the
-- IT roles they are source = 'seed': their skills come from
-- database/seed_job_role_skills.sql (since 28 October), so they are the same in
-- every database and admins can only switch them on or off. Their learning
-- resources are in database/seed_business_skills.sql.
-- Safe to run more than once.
ALTER TABLE job_roles ADD COLUMN IF NOT EXISTS courses VARCHAR(10)[] NOT NULL DEFAULT ARRAY['CS']::VARCHAR(10)[];
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_job_roles_courses') THEN
        ALTER TABLE job_roles ADD CONSTRAINT chk_job_roles_courses CHECK (
            cardinality(courses) >= 1
            AND courses <@ ARRAY['CS', 'BUSINESS', 'ICT']::VARCHAR(10)[]);
    END IF;
END $$;

UPDATE job_roles SET courses = ARRAY['CS', 'ICT']::VARCHAR(10)[]
WHERE source = 'seed' AND role_code IN ('WEB_DEV', 'DATA_ANALYST', 'CLOUD_ENGINEER', 'CYBER_ANALYST');
UPDATE job_roles SET courses = ARRAY['CS']::VARCHAR(10)[]
WHERE source = 'seed' AND role_code IN ('SOFTWARE_DEV', 'DATA_SCIENTIST');

INSERT INTO job_roles (role_name, role_code, description, industry_level, source, courses) VALUES
('Business Analyst',   'BUSINESS_ANALYST',  'Analyses business processes and data to recommend improvements and support decisions.', 'junior', 'seed',  ARRAY['BUSINESS']::VARCHAR(10)[]),
('Marketing Executive','MARKETING_EXEC',    'Plans and runs marketing campaigns, including digital marketing and market research.',  'junior', 'seed',  ARRAY['BUSINESS']::VARCHAR(10)[]),
('Financial Analyst',  'FINANCIAL_ANALYST', 'Prepares financial reports, budgets and forecasts to support business decisions.',       'junior', 'seed',  ARRAY['BUSINESS']::VARCHAR(10)[]),
('HR Executive',       'HR_EXEC',           'Supports recruitment, employee relations, training and other human-resources work.',    'junior', 'seed',  ARRAY['BUSINESS']::VARCHAR(10)[])
ON CONFLICT (role_code) DO NOTHING;
-- Databases migrated on 27 October added them as source = 'admin'
UPDATE job_roles SET source = 'seed'
WHERE role_code IN ('BUSINESS_ANALYST', 'MARKETING_EXEC', 'FINANCIAL_ANALYST', 'HR_EXEC')
  AND source <> 'seed';

-- Synthetic students: a target role allowed for their course. ICT students who
-- aimed at a CS-only role get the closest ICT role; Business students get a
-- Business role by number (student N -> N mod 4). Only rows that break the rule
-- are changed, so running this again changes nothing.
UPDATE student_profiles sp SET target_role = CASE
        WHEN u.course = 'ICT' THEN CASE sp.target_role WHEN 'Data Scientist' THEN 'Data Analyst' ELSE 'Web Developer' END
        ELSE (ARRAY['Business Analyst', 'Marketing Executive', 'Financial Analyst', 'HR Executive'])
             [(substring(lower(u.email) from '^student([0-9]+)@')::INT % 4) + 1]
    END,
    updated_at = CURRENT_TIMESTAMP
FROM users u
WHERE u.user_id = sp.user_id
  AND u.email ~* '^student[0-9]+@synthetic\.example\.com$'
  AND u.course IN ('ICT', 'BUSINESS')
  AND NOT EXISTS (SELECT 1 FROM job_roles jr
                  WHERE jr.role_name = sp.target_role AND u.course = ANY(jr.courses));

-- GPA = the latest semester's GPA, CGPA = cumulative. Both entered by the student;
-- results_updated_at drives the start-of-semester reminder (backend/routers/students.py).
ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS cgpa DECIMAL(3,2);
ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS results_updated_at TIMESTAMP;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_cgpa') THEN
        ALTER TABLE student_profiles ADD CONSTRAINT chk_profiles_cgpa CHECK (cgpa IS NULL OR cgpa BETWEEN 0 AND 4);
    END IF;
END $$;

-- ── Advisor positions, courses and staff IDs (28 October) ─────
-- Every advisor is a Dean or a Head of Programme (HOP):
--   Dean, Computing  -> CS + ICT        staff ID 10xxx
--   HOP, CS          -> CS              staff ID 11xxx
--   HOP, ICT         -> ICT             staff ID 12xxx
--   Dean, Business   -> BUSINESS        staff ID 20xxx
--   HOP, Business    -> BUSINESS        staff ID 21xxx
-- Advisors only see and add students of their courses (backend/routers/advisor.py).
-- The admin sets all of it when creating the account. Each office has only one
-- (active) Dean. An advisor inserted without a position (tests, scripts, older
-- databases) becomes Dean of Computing, or Head of Programme CS if that Dean exists.
-- Safe to run more than once.
ALTER TABLE users ADD COLUMN IF NOT EXISTS advisor_position VARCHAR(10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS advisor_courses VARCHAR(10)[];
ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_number VARCHAR(5);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_staff_number ON users(staff_number);

-- The two-digit prefix of an advisor's staff ID
CREATE OR REPLACE FUNCTION staff_number_prefix(p_position TEXT, p_courses VARCHAR[]) RETURNS TEXT AS $$
    SELECT CASE
        WHEN p_position = 'dean' AND p_courses = ARRAY['CS', 'ICT']::VARCHAR[] THEN '10'
        WHEN p_position = 'hop'  AND p_courses = ARRAY['CS']::VARCHAR[]        THEN '11'
        WHEN p_position = 'hop'  AND p_courses = ARRAY['ICT']::VARCHAR[]       THEN '12'
        WHEN p_position = 'dean' AND p_courses = ARRAY['BUSINESS']::VARCHAR[]  THEN '20'
        WHEN p_position = 'hop'  AND p_courses = ARRAY['BUSINESS']::VARCHAR[]  THEN '21'
    END
$$ LANGUAGE sql IMMUTABLE;

-- The next free staff ID with that prefix (prefix + 001 upwards)
CREATE OR REPLACE FUNCTION next_staff_number(p_prefix TEXT) RETURNS VARCHAR AS $$
DECLARE
    n INT;
BEGIN
    FOR n IN 1..999 LOOP
        IF NOT EXISTS (SELECT 1 FROM users WHERE staff_number = p_prefix || lpad(n::text, 3, '0')) THEN
            RETURN p_prefix || lpad(n::text, 3, '0');
        END IF;
    END LOOP;
    RAISE EXCEPTION 'No free staff ID left with prefix %', p_prefix;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION users_advisor_defaults() RETURNS trigger AS $$
BEGIN
    IF NEW.role = 'advisor' THEN
        IF NEW.advisor_position IS NULL THEN
            IF EXISTS (SELECT 1 FROM users WHERE role = 'advisor' AND is_active AND advisor_position = 'dean'
                       AND advisor_courses = ARRAY['CS', 'ICT']::VARCHAR(10)[] AND user_id <> NEW.user_id) THEN
                NEW.advisor_position := 'hop';
                NEW.advisor_courses  := ARRAY['CS']::VARCHAR(10)[];
            ELSE
                NEW.advisor_position := 'dean';
                NEW.advisor_courses  := ARRAY['CS', 'ICT']::VARCHAR(10)[];
            END IF;
        END IF;
        IF NEW.staff_number IS NULL THEN
            NEW.staff_number := next_staff_number(staff_number_prefix(NEW.advisor_position, NEW.advisor_courses));
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_advisor_defaults ON users;
CREATE TRIGGER trg_users_advisor_defaults
    BEFORE INSERT OR UPDATE OF role, advisor_position, advisor_courses, staff_number ON users
    FOR EACH ROW EXECUTE FUNCTION users_advisor_defaults();

-- Existing advisors (one at a time, so each gets its own ID)
DO $$
DECLARE
    uid UUID;
BEGIN
    FOR uid IN SELECT user_id FROM users WHERE role = 'advisor' AND (advisor_position IS NULL OR staff_number IS NULL)
               ORDER BY created_at LOOP
        -- No position yet: the trigger picks Dean of Computing or Head of Programme CS
        UPDATE users SET advisor_position = advisor_position, staff_number = staff_number
        WHERE user_id = uid;
    END LOOP;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_users_advisor') THEN
        ALTER TABLE users ADD CONSTRAINT chk_users_advisor CHECK (
            (role = 'advisor'
             AND staff_number ~ '^[0-9]{5}$'
             AND staff_number_prefix(advisor_position, advisor_courses) IS NOT NULL
             AND left(staff_number, 2) = staff_number_prefix(advisor_position, advisor_courses))
            OR (role <> 'advisor' AND advisor_position IS NULL AND advisor_courses IS NULL AND staff_number IS NULL));
    END IF;
END $$;

-- Only one active Dean per office. Extra Deans (older databases) become Head of
-- Programme: CS for Computing, Business for Business, with a matching staff ID.
DO $$
DECLARE
    uid UUID;
BEGIN
    FOR uid IN SELECT u.user_id FROM users u
               WHERE u.role = 'advisor' AND u.is_active AND u.advisor_position = 'dean'
                 AND EXISTS (SELECT 1 FROM users d
                             WHERE d.role = 'advisor' AND d.is_active AND d.advisor_position = 'dean'
                               AND d.advisor_courses = u.advisor_courses
                               AND (d.created_at, d.user_id::text) < (u.created_at, u.user_id::text))
    LOOP
        UPDATE users SET advisor_position = 'hop',
                         advisor_courses  = CASE WHEN advisor_courses = ARRAY['BUSINESS']::VARCHAR(10)[]
                                                 THEN ARRAY['BUSINESS']::VARCHAR(10)[] ELSE ARRAY['CS']::VARCHAR(10)[] END,
                         staff_number     = NULL
        WHERE user_id = uid;
    END LOOP;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_one_dean ON users(advisor_courses)
    WHERE role = 'advisor' AND advisor_position = 'dean' AND is_active;

-- ── Programmes per course, skills per course (28 October) ──────
-- Each course has its programmes (majors). The programme is set with the course
-- when the account is created (new-student list); students cannot change it,
-- admins can (User Management). Safe to run more than once.
CREATE TABLE IF NOT EXISTS programmes (
    programme_id    SERIAL PRIMARY KEY,
    programme_name  VARCHAR(150) NOT NULL UNIQUE,
    course          VARCHAR(10)  NOT NULL CHECK (course IN ('CS', 'BUSINESS', 'ICT')),
    sort_order      SMALLINT     NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE
);
INSERT INTO programmes (programme_name, course, sort_order) VALUES
('Bachelor of Computer Science (Software Development)',                       'CS',       1),
('Bachelor of Computer Science (Data Science)',                               'CS',       2),
('Bachelor of Computer Science (Artificial Intelligence)',                    'CS',       3),
('Bachelor of Computer Science (Cybersecurity)',                              'CS',       4),
('Bachelor of Computer Science (Cloud Computing)',                            'CS',       5),
('Bachelor of Software Engineering',                                          'CS',       6),
('Bachelor of Information and Communication Technology (Software Systems)',   'ICT',      1),
('Bachelor of Information and Communication Technology (Data Management)',    'ICT',      2),
('Bachelor of Information and Communication Technology (Network Security)',   'ICT',      3),
('Bachelor of Information and Communication Technology (Cloud and Networking)', 'ICT',    4),
('Bachelor of Business (Business Analytics)',                                 'BUSINESS', 1),
('Bachelor of Business (Information Systems)',                                'BUSINESS', 2),
('Bachelor of Business (Marketing)',                                          'BUSINESS', 3),
('Bachelor of Business (Digital Marketing)',                                  'BUSINESS', 4),
('Bachelor of Business (Finance)',                                            'BUSINESS', 5),
('Bachelor of Business (Accounting)',                                         'BUSINESS', 6),
('Bachelor of Business (Human Resource Management)',                          'BUSINESS', 7)
ON CONFLICT (programme_name) DO UPDATE SET course = EXCLUDED.course, sort_order = EXCLUDED.sort_order;

ALTER TABLE student_intake_rows ADD COLUMN IF NOT EXISTS programme VARCHAR(150);

-- Synthetic Business students get their programme from the generator
-- (data/generate_synthetic_data.py, by Business role).

-- skills_library.courses: whose students see the skill when adding their skills.
-- Set for the seed skills in seed_business_skills.sql (IT skills: CS + ICT;
-- Business skills: Business; soft skills and tools the Business roles use: all).
-- Skills added by admins are for every course unless the admin changes it.
ALTER TABLE skills_library ADD COLUMN IF NOT EXISTS courses VARCHAR(10)[] NOT NULL
    DEFAULT ARRAY['CS', 'BUSINESS', 'ICT']::VARCHAR(10)[];
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_skills_courses') THEN
        ALTER TABLE skills_library ADD CONSTRAINT chk_skills_courses CHECK (
            cardinality(courses) >= 1
            AND courses <@ ARRAY['CS', 'BUSINESS', 'ICT']::VARCHAR(10)[]);
    END IF;
END $$;


-- Students created before the Programme column (no profile or no valid programme)
-- get a random programme of their course, so every student has one. New students
-- always get theirs from the new-student list. Safe to run more than once.
INSERT INTO student_profiles (user_id)
SELECT u.user_id FROM users u
WHERE u.role = 'student'
  AND NOT EXISTS (SELECT 1 FROM student_profiles sp WHERE sp.user_id = u.user_id);

UPDATE student_profiles sp SET
    programme  = (SELECT p.programme_name FROM programmes p
                  WHERE p.course = u.course AND p.is_active AND sp.profile_id IS NOT NULL
                  ORDER BY random() LIMIT 1),
    updated_at = CURRENT_TIMESTAMP
FROM users u
WHERE u.user_id = sp.user_id AND u.role = 'student'
  AND NOT EXISTS (SELECT 1 FROM programmes p WHERE p.programme_name = sp.programme AND p.course = u.course);

-- Same rule as refresh_profile_complete() in backend/routers/students.py
UPDATE student_profiles sp SET is_complete = (
        COALESCE(TRIM(sp.programme), '')   <> ''
    AND COALESCE(TRIM(sp.university), '') <> ''
    AND sp.year_of_study IS NOT NULL
    AND COALESCE(TRIM(sp.target_role), '') <> ''
    AND EXISTS (SELECT 1 FROM student_skills ss WHERE ss.profile_id = sp.profile_id))
FROM users u
WHERE u.user_id = sp.user_id AND u.email NOT LIKE '%@synthetic.example.com';


COMMIT;
