-- ============================================================
-- SEAGAS — Seed data: Business skills, Business role skills, Business resources
-- Author: Soh Way Miin (Carl)
--
-- The Business course has 4 target roles (Business Analyst, Marketing
-- Executive, Financial Analyst, HR Executive). This file adds:
--   1. Business skills to skills_library (source 'v3'). They use the existing
--      categories so the 7 readiness dimensions stay the same: domain skills
--      (finance, marketing, HR, business analysis) count as Technical, with the
--      area in subcategory.
--   2. The skills each Business role needs (job_role_skills), same format and
--      importance levels as seed_job_role_skills.sql. The 4 roles become seed
--      roles (source 'seed'): edit them here, not in the Admin page.
--   3. Learning resources for the new skills (recommendations_library), checked
--      to open on 28 October 2026, with Malaysian sources where they matter
--      (MFRS, Employment Act, EPF / SOCSO / PCB, HRD Corp, Bursa Malaysia).
--   4. skills_library.courses: Business students only see the skills that fit
--      Business (and CS / ICT students do not see the Business-only skills).
-- ICT roles are IT roles shared with Computer Science, so their skills and
-- resources are already in the other seed files.
--
-- Run AFTER seed_skills_library_v2.sql, seed_job_role_skills.sql and
-- seed_recommendations_library_final.sql (start_backend.bat does this).
-- Safe to run more than once.
-- ============================================================

\set ON_ERROR_STOP on
BEGIN;

-- ── 1. Skills ───────────────────────────────────────────────
INSERT INTO skills_library (skill_name, category, subcategory, aliases, description, source) VALUES
('Financial Modelling', 'Technical', 'Finance & Accounting', ARRAY['Financial modeling', 'Three-statement model', 'Excel financial model']::TEXT[], 'Building spreadsheet models of a business to forecast results and support decisions.', 'v3'),
('Accounting Principles', 'Technical', 'Finance & Accounting', ARRAY['Accounting', 'Bookkeeping', 'Double-entry bookkeeping']::TEXT[], 'Recording transactions and preparing accounts with double-entry bookkeeping.', 'v3'),
('Financial Reporting', 'Technical', 'Finance & Accounting', ARRAY['Financial statements', 'MFRS', 'IFRS', 'Management reporting']::TEXT[], 'Preparing and explaining financial statements under MFRS / IFRS.', 'v3'),
('Budgeting & Forecasting', 'Technical', 'Finance & Accounting', ARRAY['Budget planning', 'Financial forecasting', 'Variance analysis']::TEXT[], 'Planning budgets, forecasting results and explaining variances.', 'v3'),
('Corporate Finance', 'Technical', 'Finance & Accounting', ARRAY['Capital budgeting', 'Valuation', 'Discounted cash flow', 'DCF']::TEXT[], 'Valuation, investment and financing decisions of a company.', 'v3'),
('Accounting Software', 'Technical', 'Finance & Accounting', ARRAY['Xero', 'QuickBooks', 'SAP FICO']::TEXT[], 'Using accounting systems such as Xero or QuickBooks for day-to-day bookkeeping.', 'v3'),
('Digital Marketing', 'Technical', 'Marketing', ARRAY['Online marketing', 'Internet marketing', 'Digital marketing strategy']::TEXT[], 'Planning and running marketing across online channels.', 'v3'),
('Social Media Marketing', 'Technical', 'Marketing', ARRAY['SMM', 'Social media management', 'Instagram marketing', 'TikTok marketing']::TEXT[], 'Creating content and campaigns for social media platforms and measuring the results.', 'v3'),
('Search Engine Optimisation', 'Technical', 'Marketing', ARRAY['SEO', 'Search engine optimization', 'Keyword research']::TEXT[], 'Making web pages rank well in search engines.', 'v3'),
('Content Marketing', 'Technical', 'Marketing', ARRAY['Content strategy', 'Content creation', 'Blogging']::TEXT[], 'Planning and creating useful content that attracts and keeps customers.', 'v3'),
('Copywriting', 'Technical', 'Marketing', ARRAY['Copy writing', 'Marketing copy', 'Ad copy']::TEXT[], 'Writing persuasive text for adverts, websites and campaigns.', 'v3'),
('Market Research', 'Technical', 'Marketing', ARRAY['Marketing research', 'Consumer research', 'Survey design', 'Focus groups']::TEXT[], 'Collecting and analysing information about customers, competitors and markets.', 'v3'),
('Branding', 'Technical', 'Marketing', ARRAY['Brand management', 'Brand strategy', 'Brand identity']::TEXT[], 'Building and managing a consistent brand.', 'v3'),
('Marketing Analytics', 'Technical', 'Marketing', ARRAY['Campaign analytics', 'Marketing metrics', 'Campaign ROI']::TEXT[], 'Measuring marketing performance and using data to improve campaigns.', 'v3'),
('Customer Relationship Management', 'Technical', 'Marketing', ARRAY['CRM', 'Salesforce', 'HubSpot CRM', 'CRM systems']::TEXT[], 'Managing customer data and relationships, often in a CRM system.', 'v3'),
('Paid Advertising', 'Technical', 'Marketing', ARRAY['Google Ads', 'Meta Ads', 'Facebook Ads', 'PPC', 'SEM', 'Pay-per-click']::TEXT[], 'Planning, running and optimising paid online advertising campaigns.', 'v3'),
('Business Process Modelling', 'Technical', 'Business Analysis', ARRAY['BPMN', 'Process mapping', 'Process modelling', 'Process modeling']::TEXT[], 'Drawing and analysing business processes, e.g. with BPMN.', 'v3'),
('Process Improvement', 'Analytical', 'Business Analysis', ARRAY['Lean management', 'Six Sigma', 'Continuous improvement', 'Kaizen']::TEXT[], 'Finding and removing waste and errors in business processes.', 'v3'),
('KPI Reporting', 'Analytical', 'Business Analysis', ARRAY['KPI tracking', 'KPI dashboards', 'Business reporting', 'Performance reporting']::TEXT[], 'Choosing key performance indicators and reporting them to decision makers.', 'v3'),
('Recruitment & Selection', 'Technical', 'Human Resources', ARRAY['Recruitment and selection', 'Talent acquisition', 'Candidate screening']::TEXT[], 'Attracting, interviewing and selecting job candidates.', 'v3'),
('Employee Relations', 'Technical', 'Human Resources', ARRAY['Industrial relations', 'Grievance handling', 'Disciplinary process']::TEXT[], 'Managing the relationship between employer and employees, including grievances and discipline.', 'v3'),
('Employment Law', 'Technical', 'Human Resources', ARRAY['Employment Act 1955', 'Labour law', 'Malaysian employment law', 'Industrial Relations Act']::TEXT[], 'Malaysian employment legislation such as the Employment Act 1955.', 'v3'),
('Payroll Administration', 'Technical', 'Human Resources', ARRAY['Payroll', 'EPF and SOCSO', 'Payroll processing', 'Monthly tax deduction']::TEXT[], 'Running payroll, including EPF, SOCSO, EIS and monthly tax deductions (PCB).', 'v3'),
('Training & Development', 'Technical', 'Human Resources', ARRAY['Learning and development', 'L&D', 'Training needs analysis']::TEXT[], 'Planning, running and evaluating staff training.', 'v3'),
('Performance Management', 'Technical', 'Human Resources', ARRAY['Performance appraisal', 'Performance review', 'Goal setting']::TEXT[], 'Setting goals, reviewing performance and giving feedback.', 'v3'),
('HR Information Systems', 'Technical', 'Human Resources', ARRAY['HRIS', 'HRMS', 'SAP SuccessFactors', 'People analytics']::TEXT[], 'Using HR systems and HR data to manage staff records and decisions.', 'v3'),
('Compensation & Benefits', 'Technical', 'Human Resources', ARRAY['C&B', 'Compensation and benefits', 'Rewards management', 'Salary benchmarking']::TEXT[], 'Designing and running pay, incentives and benefits.', 'v3'),
('Negotiation', 'Soft', 'Soft', ARRAY['Negotiation skills', 'Negotiating']::TEXT[], 'Reaching agreements that work for both sides.', 'v3'),
('Business Writing', 'Soft', 'Soft', ARRAY['Professional writing', 'Business correspondence']::TEXT[], 'Writing clear emails, reports and proposals for business readers.', 'v3')
ON CONFLICT (skill_name) DO UPDATE SET
    category    = EXCLUDED.category,
    subcategory = EXCLUDED.subcategory,
    aliases     = EXCLUDED.aliases,
    description = EXCLUDED.description,
    source      = EXCLUDED.source;

-- ── 2. Business roles and their skills ──────────────────────
INSERT INTO job_roles (role_name, role_code, description, industry_level, source, courses) VALUES
('Business Analyst',   'BUSINESS_ANALYST',  'Analyses business processes and data to recommend improvements and support decisions.', 'junior', 'seed', ARRAY['BUSINESS']::VARCHAR(10)[]),
('Marketing Executive','MARKETING_EXEC',    'Plans and runs marketing campaigns, including digital marketing and market research.',  'junior', 'seed', ARRAY['BUSINESS']::VARCHAR(10)[]),
('Financial Analyst',  'FINANCIAL_ANALYST', 'Prepares financial reports, budgets and forecasts to support business decisions.',       'junior', 'seed', ARRAY['BUSINESS']::VARCHAR(10)[]),
('HR Executive',       'HR_EXEC',           'Supports recruitment, employee relations, training and other human-resources work.',    'junior', 'seed', ARRAY['BUSINESS']::VARCHAR(10)[])
ON CONFLICT (role_code) DO UPDATE SET source = 'seed', courses = EXCLUDED.courses;

CREATE TEMP TABLE seed_business_role_skills (
    role_code  VARCHAR(50),
    skill_name VARCHAR(100),
    importance VARCHAR(20)
) ON COMMIT DROP;

INSERT INTO seed_business_role_skills (role_code, skill_name, importance) VALUES
    ('BUSINESS_ANALYST',   'Business Analysis',                 'required'),
    ('BUSINESS_ANALYST',   'Requirements Analysis',             'required'),
    ('BUSINESS_ANALYST',   'Business Process Modelling',        'required'),
    ('BUSINESS_ANALYST',   'Data Analysis',                     'required'),
    ('BUSINESS_ANALYST',   'Excel',                             'required'),
    ('BUSINESS_ANALYST',   'SQL',                               'required'),
    ('BUSINESS_ANALYST',   'Stakeholder Communication',         'required'),
    ('BUSINESS_ANALYST',   'Documentation',                     'required'),
    ('BUSINESS_ANALYST',   'Problem Solving',                   'required'),
    ('BUSINESS_ANALYST',   'Communication',                     'required'),
    ('BUSINESS_ANALYST',   'Power BI',                          'preferred'),
    ('BUSINESS_ANALYST',   'KPI Reporting',                     'preferred'),
    ('BUSINESS_ANALYST',   'Process Improvement',               'preferred'),
    ('BUSINESS_ANALYST',   'Agile / Scrum',                     'preferred'),
    ('BUSINESS_ANALYST',   'Presentation Skills',               'preferred'),
    ('BUSINESS_ANALYST',   'Critical Thinking',                 'preferred'),
    ('BUSINESS_ANALYST',   'Project Management',                'preferred'),
    ('BUSINESS_ANALYST',   'Data Visualisation',                'preferred'),
    ('BUSINESS_ANALYST',   'Tableau',                           'bonus'),
    ('BUSINESS_ANALYST',   'Financial Analysis',                'bonus'),
    ('BUSINESS_ANALYST',   'Customer Relationship Management',  'bonus'),
    ('BUSINESS_ANALYST',   'Systems Thinking',                  'bonus'),
    ('BUSINESS_ANALYST',   'Business Writing',                  'bonus'),
    ('MARKETING_EXEC',     'Digital Marketing',                 'required'),
    ('MARKETING_EXEC',     'Social Media Marketing',            'required'),
    ('MARKETING_EXEC',     'Content Marketing',                 'required'),
    ('MARKETING_EXEC',     'Market Research',                   'required'),
    ('MARKETING_EXEC',     'Copywriting',                       'required'),
    ('MARKETING_EXEC',     'Marketing Analytics',               'required'),
    ('MARKETING_EXEC',     'Communication',                     'required'),
    ('MARKETING_EXEC',     'Customer Focus',                    'required'),
    ('MARKETING_EXEC',     'Teamwork',                          'required'),
    ('MARKETING_EXEC',     'Search Engine Optimisation',        'preferred'),
    ('MARKETING_EXEC',     'Paid Advertising',                  'preferred'),
    ('MARKETING_EXEC',     'Google Analytics',                  'preferred'),
    ('MARKETING_EXEC',     'Branding',                          'preferred'),
    ('MARKETING_EXEC',     'Customer Relationship Management',  'preferred'),
    ('MARKETING_EXEC',     'Presentation Skills',               'preferred'),
    ('MARKETING_EXEC',     'Excel',                             'preferred'),
    ('MARKETING_EXEC',     'Time Management',                   'preferred'),
    ('MARKETING_EXEC',     'Figma',                             'bonus'),
    ('MARKETING_EXEC',     'Generative AI',                     'bonus'),
    ('MARKETING_EXEC',     'A/B Testing',                       'bonus'),
    ('MARKETING_EXEC',     'Data Visualisation',                'bonus'),
    ('MARKETING_EXEC',     'Negotiation',                       'bonus'),
    ('FINANCIAL_ANALYST',  'Financial Analysis',                'required'),
    ('FINANCIAL_ANALYST',  'Financial Modelling',               'required'),
    ('FINANCIAL_ANALYST',  'Accounting Principles',             'required'),
    ('FINANCIAL_ANALYST',  'Financial Reporting',               'required'),
    ('FINANCIAL_ANALYST',  'Budgeting & Forecasting',           'required'),
    ('FINANCIAL_ANALYST',  'Excel',                             'required'),
    ('FINANCIAL_ANALYST',  'Risk Analysis',                     'required'),
    ('FINANCIAL_ANALYST',  'Attention to Detail',               'required'),
    ('FINANCIAL_ANALYST',  'Communication',                     'required'),
    ('FINANCIAL_ANALYST',  'Corporate Finance',                 'preferred'),
    ('FINANCIAL_ANALYST',  'Power BI',                          'preferred'),
    ('FINANCIAL_ANALYST',  'SQL',                               'preferred'),
    ('FINANCIAL_ANALYST',  'KPI Reporting',                     'preferred'),
    ('FINANCIAL_ANALYST',  'Data Analysis',                     'preferred'),
    ('FINANCIAL_ANALYST',  'Presentation Skills',               'preferred'),
    ('FINANCIAL_ANALYST',  'Business Writing',                  'preferred'),
    ('FINANCIAL_ANALYST',  'Decision Making',                   'preferred'),
    ('FINANCIAL_ANALYST',  'Accounting Software',               'bonus'),
    ('FINANCIAL_ANALYST',  'Python',                            'bonus'),
    ('FINANCIAL_ANALYST',  'Tableau',                           'bonus'),
    ('FINANCIAL_ANALYST',  'Statistical Analysis',              'bonus'),
    ('FINANCIAL_ANALYST',  'Process Improvement',               'bonus'),
    ('HR_EXEC',            'Recruitment & Selection',           'required'),
    ('HR_EXEC',            'Employee Relations',                'required'),
    ('HR_EXEC',            'Employment Law',                    'required'),
    ('HR_EXEC',            'Payroll Administration',            'required'),
    ('HR_EXEC',            'Training & Development',            'required'),
    ('HR_EXEC',            'Performance Management',            'required'),
    ('HR_EXEC',            'Communication',                     'required'),
    ('HR_EXEC',            'Interpersonal Skills',              'required'),
    ('HR_EXEC',            'Attention to Detail',               'required'),
    ('HR_EXEC',            'HR Information Systems',            'preferred'),
    ('HR_EXEC',            'Compensation & Benefits',           'preferred'),
    ('HR_EXEC',            'Excel',                             'preferred'),
    ('HR_EXEC',            'Negotiation',                       'preferred'),
    ('HR_EXEC',            'Business Writing',                  'preferred'),
    ('HR_EXEC',            'Time Management',                   'preferred'),
    ('HR_EXEC',            'Stakeholder Communication',         'preferred'),
    ('HR_EXEC',            'Problem Solving',                   'preferred'),
    ('HR_EXEC',            'Data Analysis',                     'bonus'),
    ('HR_EXEC',            'Power BI',                          'bonus'),
    ('HR_EXEC',            'Leadership',                        'bonus'),
    ('HR_EXEC',            'Presentation Skills',               'bonus'),
    ('HR_EXEC',            'Adaptability',                      'bonus');

-- Fail loudly if a role_code or skill_name is misspelled or missing
DO $$
DECLARE missing TEXT;
BEGIN
    SELECT string_agg(s.role_code || ' / ' || s.skill_name, ', ') INTO missing
    FROM seed_business_role_skills s
    LEFT JOIN job_roles      jr ON jr.role_code  = s.role_code
    LEFT JOIN skills_library sl ON sl.skill_name = s.skill_name
    WHERE jr.role_id IS NULL OR sl.skill_id IS NULL;
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'Unknown role or skill in seed: %', missing;
    END IF;
END $$;

DELETE FROM job_role_skills jrs
USING job_roles jr
WHERE jrs.role_id = jr.role_id
  AND jr.role_code IN (SELECT DISTINCT role_code FROM seed_business_role_skills)
  AND NOT EXISTS (
        SELECT 1
        FROM seed_business_role_skills s
        JOIN skills_library sl ON sl.skill_name = s.skill_name
        WHERE s.role_code = jr.role_code
          AND sl.skill_id = jrs.skill_id);

INSERT INTO job_role_skills (role_id, skill_id, importance)
SELECT jr.role_id, sl.skill_id, s.importance
FROM seed_business_role_skills s
JOIN job_roles      jr ON jr.role_code  = s.role_code
JOIN skills_library sl ON sl.skill_name = s.skill_name
ON CONFLICT (role_id, skill_id) DO UPDATE SET importance = EXCLUDED.importance;

-- ── 3. Learning resources ───────────────────────────────────
INSERT INTO recommendations_library
    (skill_id, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
SELECT sl.skill_id, r.resource_title, r.resource_type, r.provider, r.url, r.duration_hours, r.cost, r.difficulty, r.description
FROM skills_library sl
JOIN (VALUES
('Financial Modelling', 'Business and Financial Modeling Specialization', 'course', 'Coursera / Wharton', 'https://www.coursera.org/specializations/wharton-business-financial-modeling', 60, 'Free to audit', 'intermediate', 'Build spreadsheet models to forecast, value and make business decisions.'),
('Financial Modelling', 'Build a Three-Statement Financial Model', 'project', 'Self-directed', 'https://www.khanacademy.org/economics-finance-domain/core-finance', 15, 'Free', 'intermediate', 'Model a real listed company''s income statement, balance sheet and cash flow in Excel and present the forecast.'),
('Accounting Principles', 'Introduction to Financial Accounting', 'course', 'Coursera / Wharton', 'https://www.coursera.org/learn/wharton-accounting', 20, 'Free to audit', 'beginner', 'Read and prepare the three main financial statements and record business transactions.'),
('Accounting Principles', 'Financial Accounting Fundamentals', 'course', 'Coursera / University of Virginia Darden', 'https://www.coursera.org/learn/uva-darden-financial-accounting', 20, 'Free to audit', 'beginner', 'Accounting language, double-entry and the basic financial statements.'),
('Financial Reporting', 'Malaysian Financial Reporting Standards (MFRS)', 'course', 'Malaysian Accounting Standards Board', 'https://www.masb.org.my/', 8, 'Free', 'intermediate', 'Read the MFRS framework that Malaysian companies use to prepare their financial statements.'),
('Financial Reporting', 'Financial Statement Analysis Project', 'project', 'Self-directed / Bursa Malaysia', 'https://www.bursamalaysia.com/', 12, 'Free', 'intermediate', 'Download the annual report of a Bursa Malaysia company and write a short analysis of its financial statements.'),
('Budgeting & Forecasting', 'Managerial Accounting Fundamentals', 'course', 'Coursera / University of Virginia Darden', 'https://www.coursera.org/learn/uva-darden-managerial-accounting', 20, 'Free to audit', 'intermediate', 'Cost behaviour, budgeting and variance analysis for planning and control.'),
('Budgeting & Forecasting', 'Plan a Department Budget', 'project', 'Self-directed', 'https://www.khanacademy.org/college-careers-more/personal-finance', 8, 'Free', 'beginner', 'Prepare a 12-month budget and forecast for a student club or small business and explain the variances.'),
('Corporate Finance', 'Introduction to Corporate Finance', 'course', 'Coursera / Wharton', 'https://www.coursera.org/learn/wharton-finance', 15, 'Free to audit', 'beginner', 'Time value of money, discounted cash flow, NPV and capital budgeting decisions.'),
('Corporate Finance', 'Finance Theory I', 'course', 'MIT OpenCourseWare', 'https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/', 40, 'Free', 'advanced', 'University-level lectures on valuation, risk and corporate financial decisions.'),
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
('Copywriting', 'Good with Words: Writing and Editing Specialization', 'course', 'Coursera / University of Michigan', 'https://www.coursera.org/specializations/good-with-words', 40, 'Free to audit', 'beginner', 'Clear, persuasive writing and editing for professional audiences.'),
('Copywriting', 'Write Copy for a Product Launch', 'project', 'Self-directed', 'https://copyblogger.com/', 6, 'Free', 'beginner', 'Write a landing page, three social posts and an email for a real or imagined product.'),
('Market Research', 'Market Research Specialization', 'course', 'Coursera / UC Davis', 'https://www.coursera.org/specializations/market-research', 50, 'Free to audit', 'beginner', 'Plan research, design surveys, analyse results and present recommendations.'),
('Market Research', 'Survey and Customer Interview Project', 'project', 'Self-directed', 'https://www.qualtrics.com/articles/strategy-research/survey-basics/', 12, 'Free', 'beginner', 'Survey 30 people about a product idea and present the findings and recommendations.'),
('Branding', 'Brand Management: Aligning Business, Brand and Behaviour', 'course', 'Coursera / London Business School', 'https://www.coursera.org/learn/brand', 15, 'Free to audit', 'beginner', 'How brands create value and how to manage them inside an organisation.'),
('Marketing Analytics', 'Meta Marketing Analytics Professional Certificate', 'certification', 'Coursera / Meta', 'https://www.coursera.org/professional-certificates/facebook-marketing-analytics', 100, 'Free to audit', 'intermediate', 'Measure campaigns, run A/B tests and present marketing data.'),
('Marketing Analytics', 'Google Analytics Certification', 'certification', 'Google Skillshop', 'https://skillshop.withgoogle.com/', 6, 'Free', 'beginner', 'Free certificate on measuring websites and campaigns with Google Analytics 4.'),
('Customer Relationship Management', 'Salesforce Trailhead', 'course', 'Salesforce', 'https://trailhead.salesforce.com/', 20, 'Free', 'beginner', 'Hands-on modules on CRM, sales and service processes in Salesforce.'),
('Customer Relationship Management', 'HubSpot CRM Courses', 'course', 'HubSpot Academy', 'https://academy.hubspot.com/courses', 6, 'Free', 'beginner', 'Manage contacts, deals and pipelines in HubSpot CRM.'),
('Paid Advertising', 'Google Ads Certifications', 'certification', 'Google Skillshop', 'https://skillshop.withgoogle.com/', 10, 'Free', 'intermediate', 'Free Google Ads certificates for search, display and video campaigns.'),
('Paid Advertising', 'Run a Small Paid Ad Test', 'project', 'Self-directed', 'https://skillshop.withgoogle.com/', 6, 'Free', 'intermediate', 'Plan two ad versions for the same audience, compare cost per click and conversions, and recommend one.'),
('Business Process Modelling', 'BPMN Tutorial', 'course', 'Camunda', 'https://camunda.com/bpmn/', 4, 'Free', 'beginner', 'Learn the BPMN 2.0 notation for drawing business processes.'),
('Business Process Modelling', 'Map and Improve a Real Process', 'project', 'Self-directed', 'https://www.drawio.com/', 10, 'Free', 'intermediate', 'Draw the as-is and to-be BPMN diagrams of a campus process (e.g. course registration) and propose improvements.'),
('Process Improvement', 'Six Sigma Yellow Belt', 'certification', 'Coursera', 'https://www.coursera.org/specializations/six-sigma-fundamentals', 40, 'Free to audit', 'beginner', 'Lean and Six Sigma tools (DMAIC) for improving business processes.'),
('KPI Reporting', 'Microsoft Power BI Data Analyst', 'course', 'Microsoft Learn', 'https://learn.microsoft.com/en-us/training/career-paths/data-analyst', 30, 'Free', 'intermediate', 'Model data and build KPI dashboards and reports in Power BI.'),
('KPI Reporting', 'Build a KPI Dashboard', 'project', 'Self-directed', 'https://www.kaggle.com/datasets', 12, 'Free', 'intermediate', 'Pick a business dataset, choose five KPIs and build a dashboard with a one-page summary.'),
('Business Analysis', 'Entry Certificate in Business Analysis (ECBA)', 'certification', 'IIBA', 'https://www.iiba.org/business-analysis-certifications/ecba/', 21, '$250 USD', 'beginner', 'Entry-level business analysis certificate based on the BABOK Guide.'),
('Recruitment & Selection', 'Recruiting, Hiring, and Onboarding Employees', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/learn/recruiting-hiring-onboarding-employees', 15, 'Free to audit', 'beginner', 'Plan recruitment, interview candidates and onboard new hires.'),
('Recruitment & Selection', 'Human Resource Management: HR for People Managers Specialization', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/specializations/human-resource-management', 60, 'Free to audit', 'beginner', 'The main HR functions: hiring, performance, compensation and employee development.'),
('Employee Relations', 'Employee Relations', 'course', 'Coursera', 'https://www.coursera.org/learn/employee-relations', 15, 'Free to audit', 'intermediate', 'Handle grievances, discipline and workplace relationships fairly.'),
('Employment Law', 'Employment Act 1955 and Labour Guidelines', 'course', 'Department of Labour Peninsular Malaysia (JTKSM)', 'https://jtksm.mohr.gov.my/', 6, 'Free', 'beginner', 'Official guides to working hours, leave, termination and other rights under Malaysian labour law.'),
('Payroll Administration', 'Employer Guide to EPF Contributions', 'course', 'KWSP (EPF)', 'https://www.kwsp.gov.my/', 3, 'Free', 'beginner', 'Employer contribution rates and how to submit EPF contributions.'),
('Payroll Administration', 'Employer Guide to SOCSO', 'course', 'PERKESO (SOCSO)', 'https://www.perkeso.gov.my/', 3, 'Free', 'beginner', 'Employer obligations for SOCSO and EIS contributions.'),
('Payroll Administration', 'Monthly Tax Deduction (PCB) for Employers', 'course', 'LHDN (Inland Revenue Board)', 'https://www.hasil.gov.my/', 3, 'Free', 'intermediate', 'How employers calculate and pay monthly tax deductions for employees.'),
('Training & Development', 'HRD Corp Training Programmes', 'course', 'HRD Corp Malaysia', 'https://hrdcorp.gov.my/', 5, 'Free', 'beginner', 'How Malaysian employers plan training and claim it under HRD Corp.'),
('Training & Development', 'Design a Training Workshop', 'project', 'Self-directed', 'https://www.coursera.org/specializations/human-resource-management', 10, 'Free', 'intermediate', 'Run a training needs analysis for a club or team, design a one-hour workshop and collect feedback.'),
('Performance Management', 'Managing Employee Performance', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/learn/managing-employee-performance', 12, 'Free to audit', 'beginner', 'Set goals, give feedback and run performance reviews.'),
('Compensation & Benefits', 'Managing Employee Compensation', 'course', 'Coursera / University of Minnesota', 'https://www.coursera.org/learn/compensation-management', 12, 'Free to audit', 'intermediate', 'Design pay structures, incentives and benefits.'),
('HR Information Systems', 'People Analytics', 'course', 'Coursera / Wharton', 'https://www.coursera.org/learn/wharton-people-analytics', 10, 'Free to audit', 'intermediate', 'Use HR data for hiring, performance and retention decisions.'),
('HR Information Systems', 'SHRM Certified Professional (SHRM-CP)', 'certification', 'SHRM', 'https://www.shrm.org/credentials', 80, '$400 USD', 'advanced', 'Internationally recognised HR professional certification.'),
('Negotiation', 'Successful Negotiation: Essential Strategies and Skills', 'course', 'Coursera / University of Michigan', 'https://www.coursera.org/learn/negotiation-skills', 10, 'Free to audit', 'beginner', 'Prepare for negotiations, find agreements and avoid common mistakes.'),
('Business Writing', 'Business Writing', 'course', 'Coursera / University of Colorado Boulder', 'https://www.coursera.org/learn/writing-for-business', 10, 'Free to audit', 'beginner', 'Write clear emails, reports and proposals for business readers.'),
('Business Writing', 'Writing Professional Email and Memos', 'project', 'Coursera', 'https://www.coursera.org/learn/professional-emails', 8, 'Free to audit', 'beginner', 'Short course on clear professional emails and memos.')
) AS r(skill_name, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
    ON sl.skill_name = r.skill_name
ON CONFLICT (skill_id, resource_title) DO NOTHING;

-- Every resource above must have found its skill
DO $$
DECLARE missing INT;
BEGIN
    SELECT count(*) INTO missing FROM skills_library sl
    WHERE sl.source = 'v3' AND NOT EXISTS (SELECT 1 FROM recommendations_library r WHERE r.skill_id = sl.skill_id);
    IF missing > 0 THEN
        RAISE EXCEPTION '% Business skills have no learning resource', missing;
    END IF;
END $$;

-- ── 4. Which courses' students see each seed skill ──────────
-- Soft skills: everyone. Business skills: Business. IT skills: CS and ICT, plus
-- Business when a Business role needs them (Excel, SQL, Power BI ...).
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
