-- ============================================================
-- SEAGAS — Seed data: Business learning resources, skills per course
-- Author: Soh Way Miin (Carl)
--
-- The Business skills (source 'v3') and the 4 Business role templates are in
-- seed_skills_library_v2.sql and seed_job_role_skills.sql (Ng Yong Hin). This
-- file adds:
--   1. Learning resources for the Business skills (recommendations_library):
--      links checked on 28 October 2026, mostly free, with Malaysian sources
--      where they matter (MFRS, Employment Act, EPF / SOCSO / PCB, LHDN,
--      HRD Corp, Bursa Malaysia). Every v3 skill must have at least one.
--   2. skills_library.courses: which courses' students see each skill when they
--      add their skills. Business students only see skills that fit Business,
--      and CS / ICT students do not see the Business-only skills.
-- ICT roles are IT roles shared with Computer Science, so their skills and
-- resources are already in the other seed files.
--
-- Run AFTER seed_skills_library_v2.sql, seed_job_role_skills.sql and
-- seed_recommendations_library_final.sql (start_backend.bat does this).
-- Safe to run more than once.
-- ============================================================

\set ON_ERROR_STOP on
BEGIN;

-- ── 1. Learning resources ───────────────────────────────────
-- Fail loudly if a skill name below is not in the library
DO $$
DECLARE missing TEXT;
BEGIN
    SELECT string_agg(DISTINCT n, ', ') INTO missing
    FROM unnest(ARRAY['Accounting', 'Accounting Software', 'Auditing', 'Brand Management', 'Budgeting & Forecasting', 'Business Analysis', 'Business Process Improvement', 'CRM Software', 'Communication', 'Content Marketing', 'Creativity', 'Data Visualisation', 'Digital Marketing', 'Email Marketing', 'Employee Relations', 'Employment Law', 'Financial Analysis', 'Financial Modelling', 'Financial Reporting', 'Google Analytics', 'HRIS', 'Market Research', 'Negotiation', 'Payroll', 'Performance Management', 'Process Mapping', 'Recruitment', 'Search Engine Marketing', 'Search Engine Optimisation', 'Social Media Marketing', 'Taxation', 'Training & Development', 'User Acceptance Testing']) AS n
    WHERE NOT EXISTS (SELECT 1 FROM skills_library sl WHERE sl.skill_name = n);
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'Unknown skill in seed_business_skills.sql: %', missing;
    END IF;
END $$;

INSERT INTO recommendations_library
    (skill_id, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
SELECT sl.skill_id, r.resource_title, r.resource_type, r.provider, r.url, r.duration_hours, r.cost, r.difficulty, r.description
FROM skills_library sl
JOIN (VALUES
('Financial Modelling', 'Business and Financial Modeling Specialization', 'course', 'Coursera / Wharton', 'https://www.coursera.org/specializations/wharton-business-financial-modeling', 60, 'Free to audit', 'intermediate', 'Build spreadsheet models to forecast, value and make business decisions.'),
('Financial Modelling', 'Build a Three-Statement Financial Model', 'project', 'Self-directed', 'https://www.khanacademy.org/economics-finance-domain/core-finance', 15, 'Free', 'intermediate', 'Model a real listed company''s income statement, balance sheet and cash flow in Excel and present the forecast.'),
('Accounting', 'Introduction to Financial Accounting', 'course', 'Coursera / Wharton', 'https://www.coursera.org/learn/wharton-accounting', 20, 'Free to audit', 'beginner', 'Read and prepare the three main financial statements and record business transactions.'),
('Accounting', 'Financial Accounting Fundamentals', 'course', 'Coursera / University of Virginia Darden', 'https://www.coursera.org/learn/uva-darden-financial-accounting', 20, 'Free to audit', 'beginner', 'Accounting language, double-entry and the basic financial statements.'),
('Financial Reporting', 'Malaysian Financial Reporting Standards (MFRS)', 'course', 'Malaysian Accounting Standards Board', 'https://www.masb.org.my/', 8, 'Free', 'intermediate', 'Read the MFRS framework that Malaysian companies use to prepare their financial statements.'),
('Financial Reporting', 'Financial Statement Analysis Project', 'project', 'Self-directed / Bursa Malaysia', 'https://www.bursamalaysia.com/', 12, 'Free', 'intermediate', 'Download the annual report of a Bursa Malaysia company and write a short analysis of its financial statements.'),
('Budgeting & Forecasting', 'Managerial Accounting Fundamentals', 'course', 'Coursera / University of Virginia Darden', 'https://www.coursera.org/learn/uva-darden-managerial-accounting', 20, 'Free to audit', 'intermediate', 'Cost behaviour, budgeting and variance analysis for planning and control.'),
('Budgeting & Forecasting', 'Plan a Department Budget', 'project', 'Self-directed', 'https://www.khanacademy.org/college-careers-more/personal-finance', 8, 'Free', 'beginner', 'Prepare a 12-month budget and forecast for a student club or small business and explain the variances.'),
('Financial Analysis', 'Introduction to Corporate Finance', 'course', 'Coursera / Wharton', 'https://www.coursera.org/learn/wharton-finance', 15, 'Free to audit', 'beginner', 'Time value of money, discounted cash flow, NPV and capital budgeting decisions.'),
('Financial Analysis', 'Finance Theory I', 'course', 'MIT OpenCourseWare', 'https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/', 40, 'Free', 'advanced', 'University-level lectures on valuation, risk and corporate financial decisions.'),
('Accounting Software', 'Xero Learning Centre', 'course', 'Xero', 'https://www.xero.com/my/training/', 10, 'Free', 'beginner', 'Learn bank reconciliation, invoicing and reporting in Xero cloud accounting.'),
('Accounting Software', 'Record a Month of Transactions in Xero', 'project', 'Self-directed / Xero', 'https://www.xero.com/my/training/', 8, 'Free', 'beginner', 'Use the Xero demo company to record a month of sales, purchases and payroll, then produce the reports.'),
('Financial Analysis', 'Financial Statement Analysis with Malaysian Companies', 'project', 'Self-directed / Bursa Malaysia', 'https://www.bursamalaysia.com/', 12, 'Free', 'intermediate', 'Compare the ratios of two listed companies in the same industry and present an investment view.'),
('Digital Marketing', 'Google Digital Marketing & E-commerce Professional Certificate', 'certification', 'Coursera / Google', 'https://www.coursera.org/professional-certificates/google-digital-marketing-ecommerce', 190, 'Free to audit', 'beginner', 'Seven courses on digital marketing, email, social media, e-commerce and analytics.'),
('Digital Marketing', 'Digital Marketing Certification', 'certification', 'HubSpot Academy', 'https://academy.hubspot.com/courses/digital-marketing', 7, 'Free', 'beginner', 'Free certificate covering the main channels and planning of a digital marketing strategy.'),
('Social Media Marketing', 'Social Media Marketing Certification', 'certification', 'HubSpot Academy', 'https://academy.hubspot.com/courses/social-media', 5, 'Free', 'beginner', 'Plan, publish and measure social media content; free certificate.'),
('Social Media Marketing', 'Meta Social Media Marketing Professional Certificate', 'certification', 'Coursera / Meta', 'https://www.coursera.org/professional-certificates/facebook-social-media-marketing', 120, 'Free to audit', 'beginner', 'Build a social media presence and run advertising campaigns on Meta platforms.'),
('Social Media Marketing', 'Run a Social Media Campaign for a Student Club', 'project', 'Self-directed', 'https://academy.hubspot.com/courses/social-media', 15, 'Free', 'beginner', 'Plan a four-week content calendar, post it, and report reach and engagement.'),
('Search Engine Optimisation', 'SEO Starter Guide', 'course', 'Google Search Central', 'https://developers.google.com/search/docs/fundamentals/seo-starter-guide', 3, 'Free', 'beginner', 'Google''s own guide to how search works and how to make pages easy to find.'),
('Search Engine Optimisation', 'Google SEO Fundamentals', 'course', 'Coursera', 'https://www.coursera.org/learn/seo-fundamentals', 25, 'Free to audit', 'beginner', 'Keyword research, on-page SEO and how search engines rank pages.'),
('Search Engine Optimisation', 'Semrush Academy SEO Courses', 'course', 'Semrush Academy', 'https://www.semrush.com/academy/', 10, 'Free', 'intermediate', 'Free courses on technical SEO, content and keyword research.'),
('Content Marketing', 'Content Marketing Certification', 'certification', 'HubSpot Academy', 'https://academy.hubspot.com/courses/content-marketing', 6, 'Free', 'beginner', 'Plan, create and repurpose content that attracts customers; free certificate.'),
('Content Marketing', 'Start a Blog or Content Series', 'project', 'Self-directed', 'https://academy.hubspot.com/', 15, 'Free', 'beginner', 'Publish six pieces of content for a target audience and track views and engagement.'),
('Content Marketing', 'Good with Words: Writing and Editing Specialization', 'course', 'Coursera / University of Michigan', 'https://www.coursera.org/specializations/good-with-words', 40, 'Free to audit', 'beginner', 'Clear, persuasive writing and editing for professional audiences.'),
('Content Marketing', 'Write Copy for a Product Launch', 'project', 'Self-directed', 'https://copyblogger.com/', 6, 'Free', 'beginner', 'Write a landing page, three social posts and an email for a real or imagined product.'),
('Market Research', 'Market Research Specialization', 'course', 'Coursera / UC Davis', 'https://www.coursera.org/specializations/market-research', 50, 'Free to audit', 'beginner', 'Plan research, design surveys, analyse results and present recommendations.'),
('Market Research', 'Survey and Customer Interview Project', 'project', 'Self-directed', 'https://www.qualtrics.com/articles/strategy-research/survey-basics/', 12, 'Free', 'beginner', 'Survey 30 people about a product idea and present the findings and recommendations.'),
('Brand Management', 'Brand Management: Aligning Business, Brand and Behaviour', 'course', 'Coursera / London Business School', 'https://www.coursera.org/learn/brand', 15, 'Free to audit', 'beginner', 'How brands create value and how to manage them inside an organisation.'),
('Digital Marketing', 'Meta Marketing Analytics Professional Certificate', 'certification', 'Coursera / Meta', 'https://www.coursera.org/professional-certificates/facebook-marketing-analytics', 100, 'Free to audit', 'intermediate', 'Measure campaigns, run A/B tests and present marketing data.'),
('Google Analytics', 'Google Analytics Certification', 'certification', 'Google Skillshop', 'https://skillshop.withgoogle.com/', 6, 'Free', 'beginner', 'Free certificate on measuring websites and campaigns with Google Analytics 4.'),
('CRM Software', 'Salesforce Trailhead', 'course', 'Salesforce', 'https://trailhead.salesforce.com/', 20, 'Free', 'beginner', 'Hands-on modules on CRM, sales and service processes in Salesforce.'),
('CRM Software', 'HubSpot CRM Courses', 'course', 'HubSpot Academy', 'https://academy.hubspot.com/courses', 6, 'Free', 'beginner', 'Manage contacts, deals and pipelines in HubSpot CRM.'),
('Search Engine Marketing', 'Google Ads Certifications', 'certification', 'Google Skillshop', 'https://skillshop.withgoogle.com/', 10, 'Free', 'intermediate', 'Free Google Ads certificates for search, display and video campaigns.'),
('Search Engine Marketing', 'Run a Small Paid Ad Test', 'project', 'Self-directed', 'https://skillshop.withgoogle.com/', 6, 'Free', 'intermediate', 'Plan two ad versions for the same audience, compare cost per click and conversions, and recommend one.'),
('Process Mapping', 'BPMN Tutorial', 'course', 'Camunda', 'https://camunda.com/bpmn/', 4, 'Free', 'beginner', 'Learn the BPMN 2.0 notation for drawing business processes.'),
('Process Mapping', 'Map and Improve a Real Process', 'project', 'Self-directed', 'https://www.drawio.com/', 10, 'Free', 'intermediate', 'Draw the as-is and to-be BPMN diagrams of a campus process (e.g. course registration) and propose improvements.'),
('Business Process Improvement', 'Six Sigma Yellow Belt', 'certification', 'Coursera', 'https://www.coursera.org/specializations/six-sigma-fundamentals', 40, 'Free to audit', 'beginner', 'Lean and Six Sigma tools (DMAIC) for improving business processes.'),
('Data Visualisation', 'Build a KPI Dashboard', 'project', 'Self-directed', 'https://www.kaggle.com/datasets', 12, 'Free', 'intermediate', 'Pick a business dataset, choose five KPIs and build a dashboard with a one-page summary.'),
('Business Analysis', 'Entry Certificate in Business Analysis (ECBA)', 'certification', 'IIBA', 'https://www.iiba.org/business-analysis-certifications/ecba/', 21, '$250 USD', 'beginner', 'Entry-level business analysis certificate based on the BABOK Guide.'),
('Recruitment', 'Recruiting, Hiring, and Onboarding Employees', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/learn/recruiting-hiring-onboarding-employees', 15, 'Free to audit', 'beginner', 'Plan recruitment, interview candidates and onboard new hires.'),
('Recruitment', 'Human Resource Management: HR for People Managers Specialization', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/specializations/human-resource-management', 60, 'Free to audit', 'beginner', 'The main HR functions: hiring, performance, compensation and employee development.'),
('Employee Relations', 'Employee Relations', 'course', 'Coursera', 'https://www.coursera.org/learn/employee-relations', 15, 'Free to audit', 'intermediate', 'Handle grievances, discipline and workplace relationships fairly.'),
('Employment Law', 'Employment Act 1955 and Labour Guidelines', 'course', 'Department of Labour Peninsular Malaysia (JTKSM)', 'https://jtksm.mohr.gov.my/', 6, 'Free', 'beginner', 'Official guides to working hours, leave, termination and other rights under Malaysian labour law.'),
('Payroll', 'Employer Guide to EPF Contributions', 'course', 'KWSP (EPF)', 'https://www.kwsp.gov.my/', 3, 'Free', 'beginner', 'Employer contribution rates and how to submit EPF contributions.'),
('Payroll', 'Employer Guide to SOCSO', 'course', 'PERKESO (SOCSO)', 'https://www.perkeso.gov.my/', 3, 'Free', 'beginner', 'Employer obligations for SOCSO and EIS contributions.'),
('Payroll', 'Monthly Tax Deduction (PCB) for Employers', 'course', 'LHDN (Inland Revenue Board)', 'https://www.hasil.gov.my/', 3, 'Free', 'intermediate', 'How employers calculate and pay monthly tax deductions for employees.'),
('Training & Development', 'HRD Corp Training Programmes', 'course', 'HRD Corp Malaysia', 'https://hrdcorp.gov.my/', 5, 'Free', 'beginner', 'How Malaysian employers plan training and claim it under HRD Corp.'),
('Training & Development', 'Design a Training Workshop', 'project', 'Self-directed', 'https://www.coursera.org/specializations/human-resource-management', 10, 'Free', 'intermediate', 'Run a training needs analysis for a club or team, design a one-hour workshop and collect feedback.'),
('Performance Management', 'Managing Employee Performance', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/learn/managing-employee-performance', 12, 'Free to audit', 'beginner', 'Set goals, give feedback and run performance reviews.'),
('Payroll', 'Managing Employee Compensation', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/learn/compensation-management', 12, 'Free to audit', 'intermediate', 'Design pay structures, incentives and benefits.'),
('HRIS', 'People Analytics', 'course', 'Coursera / Wharton', 'https://www.coursera.org/learn/wharton-people-analytics', 10, 'Free to audit', 'intermediate', 'Use HR data for hiring, performance and retention decisions.'),
('HRIS', 'SHRM Certified Professional (SHRM-CP)', 'certification', 'SHRM', 'https://www.shrm.org/credentials', 80, '$400 USD', 'advanced', 'Internationally recognised HR professional certification.'),
('Negotiation', 'Successful Negotiation: Essential Strategies and Skills', 'course', 'Coursera / University of Michigan', 'https://www.coursera.org/learn/negotiation-skills', 10, 'Free to audit', 'beginner', 'Prepare for negotiations, find agreements and avoid common mistakes.'),
('Communication', 'Business Writing', 'course', 'Coursera / University of Colorado Boulder', 'https://www.coursera.org/learn/writing-for-business', 10, 'Free to audit', 'beginner', 'Write clear emails, reports and proposals for business readers.'),
('Communication', 'Writing Professional Email and Memos', 'project', 'Coursera', 'https://www.coursera.org/learn/professional-emails', 8, 'Free to audit', 'beginner', 'Short course on clear professional emails and memos.'),
('Email Marketing', 'Email Marketing Certification', 'certification', 'HubSpot Academy', 'https://academy.hubspot.com/courses/email-marketing-certification-en', 4, 'Free', 'beginner', 'Plan, write and measure email campaigns; free certificate.'),
('Email Marketing', 'Mailchimp Marketing Resources', 'course', 'Mailchimp', 'https://www.mailchimp.com/resources/', 5, 'Free', 'beginner', 'Guides on building an email list, segmenting it and testing campaigns.'),
('Taxation', 'Malaysian Income Tax for Individuals and Companies', 'course', 'LHDN (Inland Revenue Board)', 'https://www.hasil.gov.my/', 6, 'Free', 'intermediate', 'Official guides to personal and company income tax, filing and deadlines in Malaysia.'),
('Auditing', 'Auditing I: Conceptual Foundations of Auditing', 'course', 'Coursera / University of Illinois', 'https://www.coursera.org/learn/auditing-part1-conceptual-foundations', 15, 'Free to audit', 'intermediate', 'Audit planning, risk, evidence and the auditor''s report.'),
('User Acceptance Testing', 'Introduction to Software Testing', 'course', 'Coursera', 'https://www.coursera.org/learn/introduction-software-testing', 15, 'Free to audit', 'beginner', 'Test plans, test cases and how to check that software meets its requirements.'),
('User Acceptance Testing', 'ISTQB Certified Tester Foundation Level', 'certification', 'ISTQB', 'https://www.istqb.org/', 30, '$250 USD', 'intermediate', 'Internationally recognised entry certificate in software testing.'),
('User Acceptance Testing', 'Write and Run a UAT Plan', 'project', 'Self-directed', 'https://www.drawio.com/', 8, 'Free', 'intermediate', 'Write acceptance criteria and test cases for a small system, run them with two users and report the results.'),
('Creativity', 'Creative Thinking: Techniques and Tools for Success', 'course', 'Coursera / Imperial College London', 'https://www.coursera.org/learn/creative-thinking-techniques-and-tools-for-success', 10, 'Free to audit', 'beginner', 'Practical techniques for generating and developing ideas.'),
('Creativity', 'Creativity, Innovation and Transformation', 'course', 'Coursera', 'https://www.coursera.org/learn/creativity-innovation', 12, 'Free to audit', 'beginner', 'Build creative habits and apply them to problems at work.')
) AS r(skill_name, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
    ON sl.skill_name = r.skill_name
ON CONFLICT (skill_id, resource_title) DO NOTHING;

-- Every Business skill has at least one learning resource
DO $$
DECLARE missing TEXT;
BEGIN
    SELECT string_agg(sl.skill_name, ', ') INTO missing FROM skills_library sl
    WHERE sl.source = 'v3' AND NOT EXISTS (SELECT 1 FROM recommendations_library r WHERE r.skill_id = sl.skill_id);
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'Business skills without a learning resource: %', missing;
    END IF;
END $$;

-- ── 2. Which courses' students see each seed skill ──────────
-- Soft skills: everyone. Business skills (v3): Business. IT skills: CS and ICT,
-- plus Business when a Business role needs them (Excel, SQL, Power BI ...).
-- Skills added by admins (source 'admin') keep the courses the admin chose.
UPDATE skills_library sl SET courses = CASE
        WHEN sl.category = 'Soft' THEN ARRAY['CS', 'BUSINESS', 'ICT']::VARCHAR(10)[]
        WHEN sl.source = 'v3'     THEN ARRAY['BUSINESS']::VARCHAR(10)[]
        WHEN EXISTS (SELECT 1 FROM job_role_skills jrs JOIN job_roles jr USING (role_id)
                     WHERE jrs.skill_id = sl.skill_id AND 'BUSINESS' = ANY(jr.courses))
                                  THEN ARRAY['CS', 'BUSINESS', 'ICT']::VARCHAR(10)[]
        ELSE ARRAY['CS', 'ICT']::VARCHAR(10)[] END
WHERE sl.source IS DISTINCT FROM 'admin';

COMMIT;
