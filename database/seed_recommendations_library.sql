-- ============================================================
-- SEAGAS — Recommendations Library Seed Data
-- Maps skill gaps to specific learning resources
-- Author: Tan Jun Xiong (Aaron) — Recommendation Engine
-- Run: psql -U postgres -d seagas_db -f database/seed_recommendations_library.sql
-- Safe to run multiple times (ON CONFLICT DO NOTHING)
-- ============================================================

INSERT INTO recommendations_library
    (skill_id, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)

SELECT sl.skill_id, r.resource_title, r.resource_type, r.provider, r.url, r.duration_hours, r.cost, r.difficulty, r.description
FROM skills_library sl
JOIN (VALUES

-- ── PYTHON ───────────────────────────────────────────────────
('Python', 'Python for Everybody Specialization',           'course',        'Coursera / University of Michigan', 'https://www.coursera.org/specializations/python',              40,  'Free to audit',  'beginner',      'Comprehensive Python course covering basics to data structures and web access.'),
('Python', 'Automate the Boring Stuff with Python',         'course',        'Udemy',                             'https://www.udemy.com/course/automate/',                       10,  'Free',           'beginner',      'Practical Python programming for automating real-world tasks.'),
('Python', 'Build a Python Portfolio Project',              'project',       'Self-directed',                     'https://realpython.com/tutorials/projects/',                    20,  'Free',           'intermediate',  'Build a data processing or automation project to demonstrate Python proficiency.'),

-- ── SQL ──────────────────────────────────────────────────────
('SQL',    'SQL for Data Science',                          'course',        'Coursera / UC Davis',               'https://www.coursera.org/learn/sql-for-data-science',          20,  'Free to audit',  'beginner',      'Learn SQL fundamentals for querying and analysing data.'),
('SQL',    'Mode SQL Tutorial',                             'course',        'Mode Analytics',                    'https://mode.com/sql-tutorial/',                               10,  'Free',           'beginner',      'Interactive SQL tutorial covering basic to advanced queries.'),
('SQL',    'Build a SQL Database Project',                  'project',       'Self-directed',                     'https://www.w3schools.com/sql/',                               15,  'Free',           'intermediate',  'Design and query a relational database for a mini project.'),

-- ── JAVASCRIPT ───────────────────────────────────────────────
('JavaScript', 'JavaScript Algorithms and Data Structures', 'certification', 'freeCodeCamp',                      'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 300, 'Free', 'intermediate', 'Comprehensive JavaScript certification covering ES6, algorithms and data structures.'),
('JavaScript', 'The Complete JavaScript Course 2026',       'course',        'Udemy / Jonas Schmedtmann',         'https://www.udemy.com/course/the-complete-javascript-course/', 69,  'Paid ~$15',      'beginner',      'Complete JavaScript from scratch to advanced topics.'),

-- ── REACT ────────────────────────────────────────────────────
('React',  'React — The Complete Guide',                    'course',        'Udemy / Maximilian Schwarzmüller',  'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', 48, 'Paid ~$15',  'intermediate',  'Comprehensive React course including hooks, Redux, and React Router.'),
('React',  'Build a React Dashboard Project',               'project',       'Self-directed',                     'https://react.dev/learn',                                      25,  'Free',           'intermediate',  'Build a data dashboard using React and a public API.'),

-- ── POWER BI ─────────────────────────────────────────────────
('Power BI', 'Microsoft Power BI Data Analyst (PL-300)',    'certification', 'Microsoft',                         'https://learn.microsoft.com/en-us/certifications/power-bi-data-analyst-associate/', 40, '$165 USD', 'intermediate', 'Official Microsoft certification for Power BI data analysis.'),
('Power BI', 'Microsoft Power BI Fundamentals',             'course',        'Microsoft Learn',                   'https://learn.microsoft.com/en-us/training/paths/create-use-analytics-reports-power-bi/', 8, 'Free', 'beginner', 'Free Microsoft learning path for Power BI fundamentals.'),
('Power BI', 'Build a Power BI Sales Dashboard',            'project',       'Self-directed',                     'https://learn.microsoft.com/en-us/power-bi/create-reports/sample-datasets', 10, 'Free', 'beginner', 'Use Microsoft sample datasets to build an interactive sales dashboard.'),

-- ── TABLEAU ──────────────────────────────────────────────────
('Tableau', 'Tableau Desktop Specialist Certification',     'certification', 'Tableau',                           'https://www.tableau.com/learn/certification/desktop-specialist', 20, '$250 USD', 'beginner',     'Entry-level Tableau certification for data visualisation.'),
('Tableau', 'Tableau Public Free Training Videos',          'course',        'Tableau',                           'https://www.tableau.com/learn/training',                       12,  'Free',           'beginner',      'Official free Tableau training videos for beginners.'),

-- ── EXCEL ────────────────────────────────────────────────────
('Excel',  'Excel Skills for Business Specialization',      'certification', 'Coursera / Macquarie University',   'https://www.coursera.org/specializations/excel',               36,  'Free to audit',  'beginner',      'Four-course Excel specialization from beginner to advanced.'),
('Excel',  'Microsoft Excel — Data Analysis with Excel Pivot Tables', 'course', 'Udemy',                         'https://www.udemy.com/course/data-analysis-with-excel-pivot-tables/', 6, 'Paid ~$15', 'intermediate', 'Learn pivot tables and data analysis techniques in Excel.'),

-- ── DATA VISUALISATION ───────────────────────────────────────
('Data Visualisation', 'Data Visualization with Python',    'course',        'Coursera / IBM',                    'https://www.coursera.org/learn/python-for-data-visualization', 12,  'Free to audit',  'intermediate',  'Learn Matplotlib, Seaborn, and Folium for data visualisation.'),
('Data Visualisation', 'Build a Python Data Visualisation Portfolio', 'project', 'Self-directed',                 'https://matplotlib.org/stable/tutorials/index.html',          15,  'Free',           'beginner',      'Create a portfolio of 3 data visualisation projects using Matplotlib/Seaborn.'),

-- ── MACHINE LEARNING ─────────────────────────────────────────
('Machine Learning', 'Machine Learning Specialization',     'certification', 'Coursera / Andrew Ng',              'https://www.coursera.org/specializations/machine-learning-introduction', 90, 'Free to audit', 'intermediate', 'Three-course ML specialization by Andrew Ng covering supervised, unsupervised learning and best practices.'),
('Machine Learning', 'Hands-On Machine Learning with Scikit-Learn', 'course', 'OReilly / Géron',                  'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/', 40, 'Paid', 'intermediate', 'Practical ML with scikit-learn and TensorFlow.'),
('Machine Learning', 'Build an ML Classification Model Project', 'project',  'Self-directed',                     'https://scikit-learn.org/stable/tutorial/index.html',          20,  'Free',           'intermediate',  'Build and evaluate a classification model using a real dataset from Kaggle.'),

-- ── DEEP LEARNING ────────────────────────────────────────────
('Deep Learning', 'Deep Learning Specialization',           'certification', 'Coursera / deeplearning.ai',        'https://www.coursera.org/specializations/deep-learning',       120, 'Free to audit',  'advanced',      'Five-course deep learning specialization by Andrew Ng.'),
('Deep Learning', 'Fast.ai Practical Deep Learning',        'course',        'fast.ai',                           'https://course.fast.ai/',                                      30,  'Free',           'intermediate',  'Practical deep learning for coders using PyTorch.'),

-- ── NLP ──────────────────────────────────────────────────────
('Natural Language Processing', 'Natural Language Processing Specialization', 'certification', 'Coursera / deeplearning.ai', 'https://www.coursera.org/specializations/natural-language-processing', 80, 'Free to audit', 'advanced', 'Four-course NLP specialization covering attention models and transformers.'),
('Natural Language Processing', 'Build an NLP Text Classifier Project', 'project', 'Self-directed',               'https://huggingface.co/learn/nlp-course/',                     20,  'Free',           'intermediate',  'Build a sentiment analysis or text classification model using Hugging Face.'),

-- ── CLOUD COMPUTING ──────────────────────────────────────────
('Cloud Computing', 'AWS Cloud Practitioner Certification (CLF-C02)', 'certification', 'AWS',                     'https://aws.amazon.com/certification/certified-cloud-practitioner/', 40, '$100 USD',  'beginner',      'Entry-level AWS certification covering core cloud concepts and services.'),
('Cloud Computing', 'Google Cloud Digital Leader Certification', 'certification', 'Google Cloud',                 'https://cloud.google.com/certification/cloud-digital-leader',   20,  '$200 USD',       'beginner',      'Google Cloud entry-level certification for business and technical roles.'),
('Cloud Computing', 'Cloud Computing Foundations',           'course',        'Coursera / Duke University',        'https://www.coursera.org/learn/cloud-computing-foundations-duke', 12, 'Free to audit', 'beginner',     'Fundamentals of cloud computing including IaaS, PaaS, and SaaS.'),

-- ── AWS ──────────────────────────────────────────────────────
('AWS',    'AWS Certified Solutions Architect — Associate (SAA-C03)', 'certification', 'AWS',                     'https://aws.amazon.com/certification/certified-solutions-architect-associate/', 80, '$150 USD', 'intermediate', 'Most popular AWS certification for designing cloud architectures.'),
('AWS',    'AWS Skill Builder — Cloud Practitioner Learning Plan', 'course',   'AWS Skill Builder',               'https://explore.skillbuilder.aws/learn/lp/82/cloud-essentials-learning-plan', 20, 'Free', 'beginner',    'Official AWS free training for Cloud Practitioner certification.'),
('AWS',    'Deploy a Simple App on AWS EC2',                 'project',       'Self-directed',                     'https://aws.amazon.com/getting-started/hands-on/',              10,  'Free tier',      'beginner',      'Deploy a simple web application on AWS EC2 using the free tier.'),

-- ── AZURE ────────────────────────────────────────────────────
('Azure',  'Microsoft Azure Fundamentals (AZ-900)',          'certification', 'Microsoft',                         'https://learn.microsoft.com/en-us/certifications/azure-fundamentals/', 32, '$165 USD',  'beginner',      'Entry-level Azure certification covering core cloud concepts.'),
('Azure',  'Microsoft Azure Fundamentals Learning Path',     'course',        'Microsoft Learn',                   'https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/', 10, 'Free',      'beginner',      'Free Microsoft learning path for Azure Fundamentals (AZ-900).'),

-- ── GCP ──────────────────────────────────────────────────────
('GCP',    'Associate Cloud Engineer Certification',         'certification', 'Google Cloud',                      'https://cloud.google.com/certification/cloud-engineer',         30,  '$200 USD',       'intermediate',  'Google Cloud certification for deploying and managing applications.'),
('GCP',    'Google Cloud Skills Boost',                      'course',        'Google Cloud',                      'https://www.cloudskillsboost.google/',                         20,  'Free credits',   'beginner',      'Hands-on labs and learning paths for Google Cloud.'),

-- ── DOCKER ───────────────────────────────────────────────────
('Docker', 'Docker and Kubernetes: The Complete Guide',      'course',        'Udemy / Stephen Grider',            'https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/', 22, 'Paid ~$15', 'intermediate', 'Complete guide to Docker containers and Kubernetes orchestration.'),
('Docker', 'Docker Official Get Started Tutorial',           'course',        'Docker',                            'https://docs.docker.com/get-started/',                         5,   'Free',           'beginner',      'Official Docker tutorial for containerising and deploying applications.'),
('Docker', 'Containerise a Python App Project',             'project',       'Self-directed',                     'https://docs.docker.com/language/python/',                     8,   'Free',           'beginner',      'Containerise the SEAGAS backend or a personal project using Docker.'),

-- ── KUBERNETES ───────────────────────────────────────────────
('Kubernetes', 'Certified Kubernetes Administrator (CKA)',   'certification', 'CNCF',                              'https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/', 40, '$395 USD', 'advanced', 'Industry-standard Kubernetes administrator certification.'),
('Kubernetes', 'Kubernetes for the Absolute Beginners',      'course',        'Udemy / KodeKloud',                 'https://www.udemy.com/course/learn-kubernetes/',               8,   'Paid ~$15',      'beginner',      'Hands-on Kubernetes course for beginners with labs.'),

-- ── GIT ──────────────────────────────────────────────────────
('Git',    'Git and GitHub — The Complete Git Guide',        'course',        'Udemy',                             'https://www.udemy.com/course/git-and-github-bootcamp/',        17,  'Paid ~$15',      'beginner',      'Complete Git version control and GitHub collaboration guide.'),
('Git',    'GitHub Skills Interactive Courses',              'course',        'GitHub',                            'https://skills.github.com/',                                   6,   'Free',           'beginner',      'Official interactive GitHub courses for version control basics.'),

-- ── LINUX ────────────────────────────────────────────────────
('Linux',  'Linux Foundation Certified System Administrator (LFCS)', 'certification', 'Linux Foundation',          'https://training.linuxfoundation.org/certification/linux-foundation-certified-sysadmin-lfcs/', 40, '$395 USD', 'intermediate', 'Professional Linux system administration certification.'),
('Linux',  'The Linux Command Line Bootcamp',                'course',        'Udemy / Colt Steele',               'https://www.udemy.com/course/the-linux-command-line-bootcamp/', 16, 'Paid ~$15',     'beginner',      'Comprehensive Linux command line course from beginner to advanced.'),
('Linux',  'Linux Journey Interactive Tutorial',             'course',        'Linux Journey',                     'https://linuxjourney.com/',                                    10,  'Free',           'beginner',      'Free interactive Linux tutorial covering commands, processes, and networking.'),

-- ── PANDAS ───────────────────────────────────────────────────
('Pandas', 'Data Analysis with Pandas and Python',           'course',        'Udemy / Boris Paskhaver',           'https://www.udemy.com/course/data-analysis-with-pandas/',      20,  'Paid ~$15',      'intermediate',  'Complete Pandas course for data manipulation and analysis.'),
('Pandas', 'Kaggle Pandas Course',                           'course',        'Kaggle',                            'https://www.kaggle.com/learn/pandas',                          4,   'Free',           'beginner',      'Free hands-on Pandas course with exercises and immediate feedback.'),
('Pandas', 'Exploratory Data Analysis Project',              'project',       'Self-directed',                     'https://www.kaggle.com/datasets',                              15,  'Free',           'intermediate',  'Perform an end-to-end EDA on a Kaggle dataset using Pandas, NumPy and Matplotlib.'),

-- ── STATISTICAL ANALYSIS ─────────────────────────────────────
('Statistical Analysis', 'Statistics with Python Specialization', 'certification', 'Coursera / University of Michigan', 'https://www.coursera.org/specializations/statistics-with-python', 48, 'Free to audit', 'intermediate', 'Three-course specialization covering statistical inference and modelling.'),
('Statistical Analysis', 'Khan Academy Statistics and Probability', 'course',   'Khan Academy',                    'https://www.khanacademy.org/math/statistics-probability',      20,  'Free',           'beginner',      'Free statistics course covering probability, distributions and hypothesis testing.'),

-- ── CYBERSECURITY ────────────────────────────────────────────
('Cybersecurity', 'CompTIA Security+ Certification (SY0-701)', 'certification', 'CompTIA',                         'https://www.comptia.org/certifications/security',              40,  '$392 USD',       'intermediate',  'Most popular entry-level cybersecurity certification covering security fundamentals.'),
('Cybersecurity', 'Google Cybersecurity Certificate',         'certification', 'Coursera / Google',                 'https://www.coursera.org/professional-certificates/google-cybersecurity', 180, 'Free to audit', 'beginner', 'Six-month Google cybersecurity professional certificate.'),
('Cybersecurity', 'TryHackMe — Pre-Security Learning Path',   'course',        'TryHackMe',                         'https://tryhackme.com/path/outline/presecurity',               40,  'Free / $14/mo',  'beginner',      'Hands-on cybersecurity learning platform with guided rooms and labs.'),

-- ── ETHICAL HACKING ──────────────────────────────────────────
('Ethical Hacking', 'Certified Ethical Hacker (CEH)',         'certification', 'EC-Council',                        'https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/', 40, '$950 USD',   'advanced',      'Industry-standard ethical hacking certification.'),
('Ethical Hacking', 'Practical Ethical Hacking — TCM Security', 'course',      'TCM Security',                      'https://academy.tcm-sec.com/p/practical-ethical-hacking-the-complete-course', 25, 'Paid ~$30', 'intermediate', 'Hands-on ethical hacking course covering network and web exploitation.'),
('Ethical Hacking', 'HackTheBox Academy Labs',                'project',       'HackTheBox',                        'https://academy.hackthebox.com/',                              30,  'Free / Paid',    'intermediate',  'Complete hands-on cybersecurity labs to build penetration testing skills.'),

-- ── NETWORK SECURITY ─────────────────────────────────────────
('Network Security', 'CompTIA Network+ Certification (N10-009)', 'certification', 'CompTIA',                        'https://www.comptia.org/certifications/network',               40,  '$338 USD',       'intermediate',  'Network security and administration certification.'),
('Network Security', 'Cisco CCNA Certification (200-301)',     'certification', 'Cisco',                             'https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html', 80, '$330 USD', 'intermediate', 'Industry-standard networking certification covering routing, switching and security.'),
('Network Security', 'Cybrary Network Security Fundamentals',  'course',        'Cybrary',                           'https://www.cybrary.it/course/network-security-fundamentals/', 10,  'Free',           'beginner',      'Free network security fundamentals course on Cybrary.'),

-- ── WIRESHARK ────────────────────────────────────────────────
('Wireshark', 'Wireshark for Beginners: Capture Packets',    'course',        'Udemy',                             'https://www.udemy.com/course/wireshark-for-beginners-capture-packets/', 3, 'Free',       'beginner',      'Learn network packet analysis with Wireshark from scratch.'),
('Wireshark', 'Analyse a Network Capture Project',           'project',       'Self-directed',                     'https://www.wireshark.org/docs/wsug_html_chunked/',            8,   'Free',           'beginner',      'Capture and analyse network traffic for a home or lab network using Wireshark.'),

-- ── TENSORFLOW ───────────────────────────────────────────────
('TensorFlow', 'TensorFlow Developer Certificate',            'certification', 'Google / TensorFlow',               'https://www.tensorflow.org/certificate',                       40,  '$100 USD',       'intermediate',  'Official Google TensorFlow developer certification.'),
('TensorFlow', 'TensorFlow for Beginners',                    'course',        'Coursera / deeplearning.ai',        'https://www.coursera.org/learn/introduction-tensorflow',       16,  'Free to audit',  'beginner',      'Introduction to TensorFlow for deep learning.'),

-- ── PYTORCH ──────────────────────────────────────────────────
('PyTorch', 'PyTorch for Deep Learning Bootcamp',             'course',        'Udemy / Jose Portilla',             'https://www.udemy.com/course/pytorch-for-deep-learning-bootcamp/', 17, 'Paid ~$15',  'intermediate',  'Complete PyTorch bootcamp from basics to advanced deep learning.'),
('PyTorch', 'Build an Image Classification Model with PyTorch', 'project',     'Self-directed',                     'https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html', 12, 'Free',     'intermediate',  'Train a convolutional neural network for image classification.'),

-- ── COMMUNICATION ────────────────────────────────────────────
('Communication', 'Improving Communication Skills',           'course',        'Coursera / University of Pennsylvania', 'https://www.coursera.org/learn/wharton-communication-skills', 10, 'Free to audit', 'beginner', 'Practical communication skills for professional settings.'),
('Communication', 'Join a Toastmasters Club',                 'workshop',      'Toastmasters International',        'https://www.toastmasters.org/find-a-club',                     12,  'Low cost',       'beginner',      'Join a Toastmasters club to practise public speaking and presentation skills.'),
('Communication', 'Technical Writing Fundamentals',           'course',        'Coursera / Google',                 'https://www.coursera.org/learn/technical-writing-101',         10,  'Free to audit',  'beginner',      'Learn to write clear technical documentation and reports.'),

-- ── PROJECT MANAGEMENT ───────────────────────────────────────
('Project Management', 'Google Project Management Certificate', 'certification', 'Coursera / Google',               'https://www.coursera.org/professional-certificates/google-project-management', 180, 'Free to audit', 'beginner', 'Six-month Google project management professional certificate.'),
('Project Management', 'Agile with Atlassian Jira',           'course',        'Coursera / Atlassian',              'https://www.coursera.org/learn/agile-atlassian-jira',          8,   'Free to audit',  'beginner',      'Learn agile project management using Jira.'),

-- ── CRITICAL THINKING ────────────────────────────────────────
('Critical Thinking', 'Critical Thinking and Problem Solving', 'course',       'Coursera / Rochester Institute',    'https://www.coursera.org/learn/critical-thinking-problem-solving', 16, 'Free to audit', 'beginner', 'Develop critical thinking and analytical problem solving skills.'),

-- ── DATA ANALYSIS ────────────────────────────────────────────
('Data Analysis', 'Google Data Analytics Certificate',        'certification', 'Coursera / Google',                 'https://www.coursera.org/professional-certificates/google-data-analytics', 240, 'Free to audit', 'beginner', 'Comprehensive six-month Google data analytics certificate covering SQL, R, Tableau and more.'),
('Data Analysis', 'IBM Data Analyst Professional Certificate', 'certification', 'Coursera / IBM',                   'https://www.coursera.org/professional-certificates/ibm-data-analyst', 200, 'Free to audit', 'beginner', 'IBM data analyst certificate covering Python, SQL, and data visualisation.'),
('Data Analysis', 'Kaggle Data Analysis Competition',         'competition',   'Kaggle',                            'https://www.kaggle.com/competitions',                          20,  'Free',           'intermediate',  'Participate in a Kaggle competition to demonstrate real-world data analysis skills.'),

-- ── MLOPS ────────────────────────────────────────────────────
('MLOps', 'MLOps Specialization',                             'certification', 'Coursera / deeplearning.ai',        'https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops', 64, 'Free to audit', 'advanced', 'Four-course MLOps specialization covering deploying and monitoring ML models.'),
('MLOps', 'Deploy a Machine Learning Model with FastAPI',     'project',       'Self-directed',                     'https://fastapi.tiangolo.com/tutorial/',                       15,  'Free',           'intermediate',  'Package and deploy an ML model as a REST API using FastAPI and Docker.'),

-- ── VULNERABILITY ASSESSMENT ─────────────────────────────────
('Vulnerability Assessment', 'CompTIA PenTest+ Certification', 'certification', 'CompTIA',                          'https://www.comptia.org/certifications/pentest',               40,  '$392 USD',       'intermediate',  'Penetration testing and vulnerability assessment certification.'),
('Vulnerability Assessment', 'OWASP Web Security Testing Guide', 'course',      'OWASP',                             'https://owasp.org/www-project-web-security-testing-guide/',    20,  'Free',           'intermediate',  'Learn web application vulnerability testing using the OWASP framework.'),
('Vulnerability Assessment', 'Perform a Vulnerability Scan Project', 'project', 'Self-directed',                    'https://www.tenable.com/products/nessus/nessus-essentials',    10,  'Free',           'beginner',      'Use Nessus Essentials (free) to scan a lab environment and document findings.'),

-- ── INCIDENT RESPONSE ────────────────────────────────────────
('Incident Response', 'CompTIA CySA+ Cybersecurity Analyst',  'certification', 'CompTIA',                           'https://www.comptia.org/certifications/cybersecurity-analyst', 40,  '$392 USD',       'intermediate',  'Cybersecurity analyst certification covering incident detection and response.'),
('Incident Response', 'TryHackMe SOC Level 1 Path',           'course',        'TryHackMe',                         'https://tryhackme.com/path/outline/soclevel1',                 60,  'Free / $14/mo',  'beginner',      'Hands-on SOC analyst training covering SIEM, log analysis and incident response.'),

-- ── TEAMWORK ─────────────────────────────────────────────────
('Teamwork', 'Collaborate on a GitHub Open Source Project',   'project',       'GitHub',                            'https://github.com/explore',                                   15,  'Free',           'beginner',      'Contribute to an open source project on GitHub to demonstrate collaboration skills.'),
('Teamwork', 'Everyday Leadership',                           'course',        'Coursera / Duke University',        'https://www.coursera.org/learn/everyday-leadership-new',       6,   'Free to audit',  'beginner',      'Develop teamwork and everyday leadership skills.'),

-- ── DOCUMENTATION ────────────────────────────────────────────
('Documentation', 'Technical Writing for Developers',         'course',        'Udemy',                             'https://www.udemy.com/course/technical-writing-for-developers/', 6,  'Paid ~$15',      'beginner',      'Learn to write technical documentation, README files and API docs.'),
('Documentation', 'Write a Complete Project README',          'project',       'Self-directed',                     'https://www.makeareadme.com/',                                  5,   'Free',           'beginner',      'Write a professional README for a GitHub project including setup, usage and contribution guides.')

) AS r(skill_name, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
ON sl.skill_name = r.skill_name
WHERE sl.is_active = TRUE

ON CONFLICT DO NOTHING;

-- ── VERIFY ───────────────────────────────────────────────────
SELECT
    sl.skill_name,
    COUNT(rl.resource_id) AS resource_count
FROM skills_library sl
LEFT JOIN recommendations_library rl ON rl.skill_id = sl.skill_id
GROUP BY sl.skill_name
HAVING COUNT(rl.resource_id) > 0
ORDER BY resource_count DESC, sl.skill_name;

SELECT COUNT(*) AS total_resources FROM recommendations_library;
