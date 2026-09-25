-- ============================================================
-- SEAGAS — Student Employability Assessment & Gap Analysis System
-- Database Schema (PostgreSQL)
-- Group 10 | COS40005 | Swinburne University
-- Author: Soh Way Miin (Carl) — Backend Developer
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLE 1: users
-- Stores all user accounts (students, advisors, admins)
-- Handles authentication and role-based access
-- ============================================================
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,           -- bcrypt hashed
    role            VARCHAR(20)  NOT NULL             -- 'student' | 'advisor' | 'admin'
                    CHECK (role IN ('student', 'advisor', 'admin')),
    full_name       VARCHAR(255) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast email lookup during login
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role  ON users(role);

-- ============================================================
-- TABLE 2: student_profiles
-- One profile per student user
-- Stores academic background, career interests, experience
-- FR-01: Student Profile Creation
-- ============================================================
CREATE TABLE student_profiles (
    profile_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE
                        REFERENCES users(user_id) ON DELETE CASCADE,

    -- Academic background
    programme           VARCHAR(255),                -- e.g. "Bachelor of Computer Science (Cyber Security)"
    university          VARCHAR(255),
    gpa                 DECIMAL(3,2),                -- e.g. 3.25
    expected_graduation VARCHAR(20),                 -- e.g. "December 2027"
    year_of_study       SMALLINT,                    -- 1 | 2 | 3 | 4

    -- Experience counts (summary fields, detail in separate tables)
    internship_count    SMALLINT     DEFAULT 0,
    project_count       SMALLINT     DEFAULT 0,
    certification_count SMALLINT     DEFAULT 0,

    -- Career interests
    target_role         VARCHAR(100),                -- e.g. "Data Analyst"
    career_interests    TEXT[],                      -- array of interest strings

    -- Profile completeness flag
    is_complete         BOOLEAN      DEFAULT FALSE,

    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_student_profiles_target_role ON student_profiles(target_role);

-- ============================================================
-- TABLE 3: skills_library
-- Pre-built library of ~100–150 IT skills
-- Categorized into 4 types (FR-02)
-- Used for dropdown selection and NLP matching reference
-- ============================================================
CREATE TABLE skills_library (
    skill_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name      VARCHAR(100) NOT NULL UNIQUE,
    category        VARCHAR(30)  NOT NULL
                    CHECK (category IN (
                        'Technical',
                        'AI_Digital',
                        'Analytical',
                        'Soft'
                    )),
    aliases         TEXT[],                          -- e.g. ["JS", "JavaScript ES6"]
    description     TEXT,                            -- brief description for display
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skills_library_category  ON skills_library(category);
CREATE INDEX idx_skills_library_skill_name ON skills_library(skill_name);

-- ============================================================
-- TABLE 4: student_skills
-- Junction table: which skills a student has
-- Students select from skills_library dropdown (FR-02)
-- Proficiency level captures Strong / Developing evidence
-- ============================================================
CREATE TABLE student_skills (
    student_skill_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id          UUID NOT NULL
                        REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    skill_id            UUID NOT NULL
                        REFERENCES skills_library(skill_id) ON DELETE RESTRICT,

    proficiency_level   VARCHAR(20)  NOT NULL DEFAULT 'intermediate'
                        CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced')),

    -- Evidence sources (what supports this skill claim)
    evidence_type       VARCHAR(20)[]    DEFAULT '{}',  -- ['project','certification','coursework','internship']
    evidence_notes      TEXT,                           -- free text description

    added_at            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (profile_id, skill_id)                       -- no duplicate skills per student
);

CREATE INDEX idx_student_skills_profile_id ON student_skills(profile_id);
CREATE INDEX idx_student_skills_skill_id   ON student_skills(skill_id);

-- ============================================================
-- TABLE 5: job_roles
-- Pre-built templates for 6 IT career roles (FR-03 option b)
-- Used when student selects a role without uploading a JD
-- ============================================================
CREATE TABLE job_roles (
    role_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name       VARCHAR(100) NOT NULL UNIQUE,    -- e.g. "Data Analyst"
    role_code       VARCHAR(30)  NOT NULL UNIQUE,    -- e.g. "DATA_ANALYST"
    description     TEXT,
    industry_level  VARCHAR(20)  DEFAULT 'entry'
                    CHECK (industry_level IN ('entry', 'junior', 'mid', 'senior')),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Required skills per job role (many-to-many)
CREATE TABLE job_role_skills (
    role_skill_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id         UUID NOT NULL
                    REFERENCES job_roles(role_id) ON DELETE CASCADE,
    skill_id        UUID NOT NULL
                    REFERENCES skills_library(skill_id) ON DELETE RESTRICT,
    importance      VARCHAR(10)  NOT NULL DEFAULT 'required'
                    CHECK (importance IN ('required', 'preferred', 'bonus')),

    UNIQUE (role_id, skill_id)
);

CREATE INDEX idx_job_role_skills_role_id  ON job_role_skills(role_id);
CREATE INDEX idx_job_role_skills_skill_id ON job_role_skills(skill_id);

-- ============================================================
-- TABLE 6: job_descriptions
-- Raw JD text uploaded/pasted by students (FR-03 option a)
-- Also stores real JDs collected for AI evaluation dataset
-- ============================================================
CREATE TABLE job_descriptions (
    jd_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID                                     -- NULL if admin-uploaded template
                    REFERENCES student_profiles(profile_id) ON DELETE SET NULL,
    role_id         UUID                                     -- linked role if known
                    REFERENCES job_roles(role_id) ON DELETE SET NULL,

    -- JD content
    title           VARCHAR(255),                            -- e.g. "Junior Data Analyst"
    company         VARCHAR(255),
    raw_text        TEXT NOT NULL,                           -- original pasted/uploaded text
    source          VARCHAR(20)  DEFAULT 'student_input'
                    CHECK (source IN ('student_input', 'admin_template', 'scraped')),

    -- NLP processing status
    nlp_status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                    CHECK (nlp_status IN ('pending', 'processing', 'complete', 'failed')),
    nlp_processed_at TIMESTAMP,

    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jd_profile_id  ON job_descriptions(profile_id);
CREATE INDEX idx_jd_role_id     ON job_descriptions(role_id);
CREATE INDEX idx_jd_nlp_status  ON job_descriptions(nlp_status);

-- Skills extracted from a JD by the NLP module (FR-04)
CREATE TABLE jd_extracted_skills (
    extracted_skill_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jd_id               UUID NOT NULL
                        REFERENCES job_descriptions(jd_id) ON DELETE CASCADE,
    skill_id            UUID                                 -- NULL if not in skills_library
                        REFERENCES skills_library(skill_id) ON DELETE SET NULL,

    raw_skill_text      VARCHAR(255) NOT NULL,               -- exactly as extracted from JD text
    extraction_method   VARCHAR(20)  NOT NULL
                        CHECK (extraction_method IN ('spacy_ner', 'keyword', 'semantic')),
    confidence_score    DECIMAL(4,3),                        -- 0.000 to 1.000
    importance          VARCHAR(10)  DEFAULT 'required'
                        CHECK (importance IN ('required', 'preferred', 'bonus')),

    extracted_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jd_extracted_skills_jd_id   ON jd_extracted_skills(jd_id);
CREATE INDEX idx_jd_extracted_skills_skill_id ON jd_extracted_skills(skill_id);

-- ============================================================
-- TABLE 7: assessments
-- One assessment record per (student, job) analysis run
-- Stores overall scores + 7-dimension breakdown (FR-07, FR-08)
-- ============================================================
CREATE TABLE assessments (
    assessment_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id          UUID NOT NULL
                        REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    jd_id               UUID                                     -- NULL if using role template
                        REFERENCES job_descriptions(jd_id) ON DELETE SET NULL,
    role_id             UUID                                     -- which role was assessed against
                        REFERENCES job_roles(role_id) ON DELETE SET NULL,

    -- Matching method used (FR-05, FR-06)
    matching_method     VARCHAR(20)  NOT NULL DEFAULT 'semantic'
                        CHECK (matching_method IN ('keyword', 'semantic', 'hybrid')),

    -- Overall score (FR-07)
    readiness_score     DECIMAL(5,2) NOT NULL                   -- 0.00 to 100.00 %

                        CHECK (readiness_score BETWEEN 0 AND 100),

    -- 7-dimension breakdown (FR-08)
    score_technical     DECIMAL(5,2) CHECK (score_technical     BETWEEN 0 AND 100),
    score_ai_digital    DECIMAL(5,2) CHECK (score_ai_digital    BETWEEN 0 AND 100),
    score_analytical    DECIMAL(5,2) CHECK (score_analytical    BETWEEN 0 AND 100),
    score_communication DECIMAL(5,2) CHECK (score_communication BETWEEN 0 AND 100),
    score_industry_exp  DECIMAL(5,2) CHECK (score_industry_exp  BETWEEN 0 AND 100),
    score_project_exp   DECIMAL(5,2) CHECK (score_project_exp   BETWEEN 0 AND 100),
    score_certification DECIMAL(5,2) CHECK (score_certification BETWEEN 0 AND 100),

    -- Metadata
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessments_profile_id ON assessments(profile_id);
CREATE INDEX idx_assessments_role_id    ON assessments(role_id);
CREATE INDEX idx_assessments_created_at ON assessments(created_at DESC);

-- Per-skill match result for each assessment (FR-09)
CREATE TABLE skill_match_results (
    match_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID NOT NULL
                        REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    skill_id            UUID NOT NULL
                        REFERENCES skills_library(skill_id) ON DELETE RESTRICT,

    -- Matching detail
    match_status        VARCHAR(15)  NOT NULL
                        CHECK (match_status IN ('strong', 'developing', 'gap')),
    similarity_score    DECIMAL(4,3),                           -- cosine similarity 0.000–1.000
    matching_method     VARCHAR(20)  NOT NULL
                        CHECK (matching_method IN ('keyword', 'semantic', 'hybrid')),
    matched_student_skill VARCHAR(255),                         -- which student skill triggered the match

    UNIQUE (assessment_id, skill_id)
);

CREATE INDEX idx_skill_match_results_assessment_id ON skill_match_results(assessment_id);
CREATE INDEX idx_skill_match_results_match_status  ON skill_match_results(match_status);

-- ============================================================
-- TABLE 8: recommendations_library
-- Curated resource library mapped to skills (FR-10, Aaron)
-- Rule engine queries this table
-- ============================================================
CREATE TABLE recommendations_library (
    resource_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id        UUID NOT NULL
                    REFERENCES skills_library(skill_id) ON DELETE CASCADE,

    -- Resource details
    resource_title  VARCHAR(255) NOT NULL,
    resource_type   VARCHAR(20)  NOT NULL
                    CHECK (resource_type IN (
                        'course', 'certification', 'project',
                        'workshop', 'competition', 'internship'
                    )),
    provider        VARCHAR(255),                               -- e.g. "Microsoft Learn", "Coursera"
    url             TEXT,
    duration_hours  SMALLINT,                                   -- estimated hours to complete
    cost            VARCHAR(50)  DEFAULT 'Free',                -- "Free" | "$100 USD" etc.
    difficulty      VARCHAR(15)  DEFAULT 'beginner'
                    CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    description     TEXT,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_library_skill_id      ON recommendations_library(skill_id);
CREATE INDEX idx_recommendations_library_resource_type ON recommendations_library(resource_type);

-- ============================================================
-- TABLE 9: student_recommendations
-- Which recommendations were shown to a student per assessment
-- Development tracking (FR-11)
-- ============================================================
CREATE TABLE student_recommendations (
    student_rec_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id   UUID NOT NULL
                    REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    profile_id      UUID NOT NULL
                    REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    resource_id     UUID NOT NULL
                    REFERENCES recommendations_library(resource_id) ON DELETE RESTRICT,

    -- Tracking status (FR-11)
    status          VARCHAR(15)  NOT NULL DEFAULT 'not_started'
                    CHECK (status IN ('not_started', 'in_progress', 'completed')),
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    notes           TEXT,                                       -- student's own notes

    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (assessment_id, resource_id)
);

CREATE INDEX idx_student_recommendations_profile_id   ON student_recommendations(profile_id);
CREATE INDEX idx_student_recommendations_assessment_id ON student_recommendations(assessment_id);
CREATE INDEX idx_student_recommendations_status       ON student_recommendations(status);

-- ============================================================
-- TABLE 10: student_projects
-- Projects listed in student profile (FR-01)
-- ============================================================
CREATE TABLE student_projects (
    project_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID NOT NULL
                    REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    project_title   VARCHAR(255) NOT NULL,
    description     TEXT,
    technologies    TEXT[],                                     -- e.g. ["React", "Python", "PostgreSQL"]
    project_type    VARCHAR(20)  DEFAULT 'academic'
                    CHECK (project_type IN ('academic', 'personal', 'internship', 'competition')),
    year_completed  SMALLINT,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_student_projects_profile_id ON student_projects(profile_id);

-- ============================================================
-- TABLE 11: student_certifications
-- Certifications listed in student profile (FR-01)
-- ============================================================
CREATE TABLE student_certifications (
    cert_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID NOT NULL
                    REFERENCES student_profiles(profile_id) ON DELETE CASCADE,
    cert_name       VARCHAR(255) NOT NULL,                      -- e.g. "AWS Cloud Practitioner"
    issuer          VARCHAR(255),                               -- e.g. "Amazon Web Services"
    issue_date      DATE,
    expiry_date     DATE,
    credential_url  TEXT,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_student_certifications_profile_id ON student_certifications(profile_id);

-- ============================================================
-- SEED DATA: 6 IT Job Roles
-- ============================================================
INSERT INTO job_roles (role_name, role_code, description, industry_level) VALUES
('Data Analyst',         'DATA_ANALYST',      'Analyses data to provide business insights using tools like Python, SQL, and Power BI.', 'junior'),
('Data Scientist',       'DATA_SCIENTIST',    'Builds machine learning models and performs advanced statistical analysis.', 'mid'),
('Software Developer',   'SOFTWARE_DEV',      'Designs and builds software applications using programming languages and frameworks.', 'junior'),
('Cybersecurity Analyst','CYBER_ANALYST',     'Monitors and protects systems from security threats and vulnerabilities.', 'junior'),
('Cloud Engineer',       'CLOUD_ENGINEER',    'Designs and manages cloud infrastructure on platforms such as AWS and Azure.', 'junior'),
('Web Developer',        'WEB_DEV',           'Develops and maintains websites and web applications using frontend and backend technologies.', 'junior');

-- ============================================================
-- SEED DATA: Skills Library Sample (subset — full 100–150 to be populated by Yong Hin)
-- ============================================================
INSERT INTO skills_library (skill_name, category, aliases, description) VALUES
-- Technical
('Python',              'Technical',  ARRAY['Python 3', 'Python programming'], 'General-purpose programming language widely used in data science and backend development.'),
('SQL',                 'Technical',  ARRAY['MySQL', 'PostgreSQL', 'SQLite', 'Structured Query Language'], 'Database query language for relational databases.'),
('JavaScript',          'Technical',  ARRAY['JS', 'ES6', 'ECMAScript'], 'Core web programming language for frontend and backend (Node.js) development.'),
('React',               'Technical',  ARRAY['React.js', 'ReactJS'], 'JavaScript library for building user interfaces.'),
('Java',                'Technical',  ARRAY['Java SE', 'Java EE'], 'Object-oriented programming language used in enterprise applications.'),
('C++',                 'Technical',  ARRAY['CPP', 'C Plus Plus'], 'Systems programming language used in performance-critical applications.'),
('R',                   'Technical',  ARRAY['R programming', 'R language'], 'Statistical programming language used in data analysis.'),
('Power BI',            'Technical',  ARRAY['PowerBI', 'Microsoft Power BI'], 'Business intelligence and data visualisation tool by Microsoft.'),
('Tableau',             'Technical',  ARRAY['Tableau Desktop', 'Tableau Public'], 'Data visualisation platform for creating interactive dashboards.'),
('Excel',               'Technical',  ARRAY['Microsoft Excel', 'MS Excel', 'Spreadsheet'], 'Spreadsheet tool used for data analysis and reporting.'),
('FastAPI',             'Technical',  ARRAY['Fast API'], 'Modern Python web framework for building APIs.'),
('Flask',               'Technical',  ARRAY['Flask Python'], 'Lightweight Python web framework.'),
('Node.js',             'Technical',  ARRAY['NodeJS', 'Node'], 'JavaScript runtime for backend development.'),
('Docker',              'Technical',  ARRAY['Docker container', 'Containerisation'], 'Platform for building and running containerised applications.'),
('Git',                 'Technical',  ARRAY['GitHub', 'GitLab', 'Version control'], 'Version control system for tracking code changes.'),
('Linux',               'Technical',  ARRAY['Ubuntu', 'Bash', 'Shell scripting'], 'Operating system widely used in server and cloud environments.'),
-- AI / Digital
('Machine Learning',    'AI_Digital', ARRAY['ML', 'Supervised learning', 'Unsupervised learning'], 'Building models that learn patterns from data.'),
('Deep Learning',       'AI_Digital', ARRAY['DL', 'Neural networks', 'CNN', 'RNN'], 'Subset of machine learning using multi-layer neural networks.'),
('Natural Language Processing', 'AI_Digital', ARRAY['NLP', 'Text processing', 'Text mining'], 'AI techniques for processing and understanding human language.'),
('Data Visualisation',  'AI_Digital', ARRAY['Data viz', 'Dashboard creation', 'Creating interactive dashboards', 'Charts and graphs'], 'Representing data visually through charts, graphs, and dashboards.'),
('Cloud Computing',     'AI_Digital', ARRAY['AWS', 'Azure', 'GCP', 'Cloud platforms', 'Cloud infrastructure'], 'Delivering computing services over the internet.'),
('AWS',                 'AI_Digital', ARRAY['Amazon Web Services', 'AWS Cloud', 'Amazon Cloud'], 'Amazon cloud computing platform.'),
('Azure',               'AI_Digital', ARRAY['Microsoft Azure', 'Azure Cloud'], 'Microsoft cloud computing platform.'),
('AI Literacy',         'AI_Digital', ARRAY['Artificial Intelligence', 'AI concepts', 'AI fundamentals'], 'Understanding of AI concepts, applications, and ethical considerations.'),
-- Analytical
('Statistical Analysis','Analytical', ARRAY['Statistics', 'Statistical modelling', 'Quantitative analysis'], 'Applying statistical methods to interpret data.'),
('Data Analysis',       'Analytical', ARRAY['Data analytics', 'Exploratory data analysis', 'EDA'], 'Inspecting and modelling data to discover insights.'),
('Problem Solving',     'Analytical', ARRAY['Critical thinking', 'Analytical problem solving'], 'Identifying and resolving complex challenges systematically.'),
('Research Skills',     'Analytical', ARRAY['Literature review', 'Academic research'], 'Ability to investigate, evaluate, and synthesise information.'),
-- Soft
('Communication',       'Soft',       ARRAY['Verbal communication', 'Written communication', 'Presentation skills'], 'Conveying information clearly to technical and non-technical audiences.'),
('Teamwork',            'Soft',       ARRAY['Collaboration', 'Team player', 'Cooperative work'], 'Working effectively with others toward shared goals.'),
('Time Management',     'Soft',       ARRAY['Organisation', 'Prioritisation', 'Meeting deadlines'], 'Managing tasks and deadlines efficiently.'),
('Leadership',          'Soft',       ARRAY['Team leadership', 'Project leadership'], 'Guiding and motivating a team toward objectives.');

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- View: student assessment summary (used by Advisor Dashboard — FR-13)
CREATE VIEW v_student_assessment_summary AS
SELECT
    u.user_id,
    u.full_name,
    sp.programme,
    sp.target_role,
    a.assessment_id,
    a.readiness_score,
    a.matching_method,
    a.created_at AS assessed_at,
    jr.role_name  AS assessed_role
FROM users u
JOIN student_profiles sp   ON sp.user_id       = u.user_id
LEFT JOIN assessments a    ON a.profile_id     = sp.profile_id
LEFT JOIN job_roles jr     ON jr.role_id       = a.role_id
WHERE u.role = 'student'
ORDER BY a.created_at DESC;

-- View: cohort skill gap summary (used by Advisor Dashboard cohort bar chart)
CREATE VIEW v_cohort_skill_gaps AS
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
JOIN skills_library sl ON sl.skill_id = smr.skill_id
GROUP BY sl.skill_id, sl.skill_name, sl.category
ORDER BY gap_percentage DESC;

-- View: student development progress
CREATE VIEW v_student_progress AS
SELECT
    sp.user_id,
    u.full_name,
    COUNT(*) FILTER (WHERE sr.status = 'completed')   AS completed_tasks,
    COUNT(*) FILTER (WHERE sr.status = 'in_progress') AS in_progress_tasks,
    COUNT(*) FILTER (WHERE sr.status = 'not_started') AS pending_tasks,
    COUNT(*)                                           AS total_tasks
FROM student_recommendations sr
JOIN student_profiles sp ON sp.profile_id = sr.profile_id
JOIN users u             ON u.user_id     = sp.user_id
GROUP BY sp.user_id, u.full_name;

-- ============================================================
-- END OF SCHEMA
-- ============================================================
