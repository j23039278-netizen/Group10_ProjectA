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

COMMIT;
