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

COMMIT;
