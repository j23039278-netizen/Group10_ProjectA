-- ============================================================
-- SEAGAS â€" Recommendations Library (Final â€" All Skills)
-- Merged from v1 + v2 + v3, duplicates removed
-- Author: Tan Jun Xiong (Aaron) â€" Recommendation Engine
-- Run: psql -U postgres -d seagas_db -f database/seed_recommendations_library_final.sql
-- Safe to run multiple times (ON CONFLICT DO NOTHING)
-- ============================================================

INSERT INTO recommendations_library
    (skill_id, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)

SELECT sl.skill_id, r.resource_title, r.resource_type, r.provider, r.url, r.duration_hours, r.cost, r.difficulty, r.description
FROM skills_library sl
JOIN (VALUES

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- SECTION 1 â€" CORE TECHNICAL SKILLS (from v1)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

-- â"€â"€ PYTHON â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Python', 'Python for Everybody Specialization',           'course',        'Coursera / University of Michigan', 'https://www.coursera.org/specializations/python',              40,  'Free to audit',  'beginner',      'Comprehensive Python course covering basics to data structures and web access.'),
('Python', 'Automate the Boring Stuff with Python',         'course',        'Udemy',                             'https://www.udemy.com/course/automate/',                       10,  'Free',           'beginner',      'Practical Python programming for automating real-world tasks.'),
('Python', 'Build a Python Portfolio Project',              'project',       'Self-directed',                     'https://realpython.com/tutorials/projects/',                    20,  'Free',           'intermediate',  'Build a data processing or automation project to demonstrate Python proficiency.'),

-- â"€â"€ SQL â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('SQL',    'SQL for Data Science',                          'course',        'Coursera / UC Davis',               'https://www.coursera.org/learn/sql-for-data-science',          20,  'Free to audit',  'beginner',      'Learn SQL fundamentals for querying and analysing data.'),
('SQL',    'Mode SQL Tutorial',                             'course',        'Mode Analytics',                    'https://mode.com/sql-tutorial/',                               10,  'Free',           'beginner',      'Interactive SQL tutorial covering basic to advanced queries.'),
('SQL',    'Build a SQL Database Project',                  'project',       'Self-directed',                     'https://www.w3schools.com/sql/',                               15,  'Free',           'intermediate',  'Design and query a relational database for a mini project.'),

-- â"€â"€ JAVASCRIPT â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('JavaScript', 'JavaScript Algorithms and Data Structures', 'certification', 'freeCodeCamp',                      'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 300, 'Free', 'intermediate', 'Comprehensive JavaScript certification covering ES6, algorithms and data structures.'),
('JavaScript', 'The Complete JavaScript Course 2026',       'course',        'Udemy / Jonas Schmedtmann',         'https://www.udemy.com/course/the-complete-javascript-course/', 69,  'Paid ~$15',      'beginner',      'Complete JavaScript from scratch to advanced topics.'),

-- â"€â"€ REACT â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('React',  'React â€" The Complete Guide',                    'course',        'Udemy / Maximilian Schwarzmuller',  'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', 48, 'Paid ~$15',  'intermediate',  'Comprehensive React course including hooks, Redux, and React Router.'),
('React',  'Build a React Dashboard Project',               'project',       'Self-directed',                     'https://react.dev/learn',                                      25,  'Free',           'intermediate',  'Build a data dashboard using React and a public API.'),

-- â"€â"€ POWER BI â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Power BI', 'Microsoft Power BI Data Analyst (PL-300)',    'certification', 'Microsoft',                         'https://learn.microsoft.com/en-us/certifications/power-bi-data-analyst-associate/', 40, '$165 USD', 'intermediate', 'Official Microsoft certification for Power BI data analysis.'),
('Power BI', 'Microsoft Power BI Fundamentals',             'course',        'Microsoft Learn',                   'https://learn.microsoft.com/en-us/training/paths/create-use-analytics-reports-power-bi/', 8, 'Free', 'beginner', 'Free Microsoft learning path for Power BI fundamentals.'),
('Power BI', 'Build a Power BI Sales Dashboard',            'project',       'Self-directed',                     'https://learn.microsoft.com/en-us/power-bi/create-reports/sample-datasets', 10, 'Free', 'beginner', 'Use Microsoft sample datasets to build an interactive sales dashboard.'),

-- â"€â"€ TABLEAU â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Tableau', 'Tableau Desktop Specialist Certification',     'certification', 'Tableau',                           'https://www.tableau.com/learn/certification/desktop-specialist', 20, '$250 USD', 'beginner',     'Entry-level Tableau certification for data visualisation.'),
('Tableau', 'Tableau Public Free Training Videos',          'course',        'Tableau',                           'https://www.tableau.com/learn/training',                       12,  'Free',           'beginner',      'Official free Tableau training videos for beginners.'),

-- â"€â"€ EXCEL â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Excel',  'Excel Skills for Business Specialization',      'certification', 'Coursera / Macquarie University',   'https://www.coursera.org/specializations/excel',               36,  'Free to audit',  'beginner',      'Four-course Excel specialization from beginner to advanced.'),
('Excel',  'Microsoft Excel â€" Data Analysis with Excel Pivot Tables', 'course', 'Udemy',                         'https://www.udemy.com/course/data-analysis-with-excel-pivot-tables/', 6, 'Paid ~$15', 'intermediate', 'Learn pivot tables and data analysis techniques in Excel.'),

-- â"€â"€ DATA VISUALISATION â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Data Visualisation', 'Data Visualization with Python',    'course',        'Coursera / IBM',                    'https://www.coursera.org/learn/python-for-data-visualization', 12,  'Free to audit',  'intermediate',  'Learn Matplotlib, Seaborn, and Folium for data visualisation.'),
('Data Visualisation', 'Build a Python Data Visualisation Portfolio', 'project', 'Self-directed',                 'https://matplotlib.org/stable/tutorials/index.html',          15,  'Free',           'beginner',      'Create a portfolio of 3 data visualisation projects using Matplotlib/Seaborn.'),

-- â"€â"€ MACHINE LEARNING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Machine Learning', 'Machine Learning Specialization',     'certification', 'Coursera / Andrew Ng',              'https://www.coursera.org/specializations/machine-learning-introduction', 90, 'Free to audit', 'intermediate', 'Three-course ML specialization by Andrew Ng covering supervised, unsupervised learning and best practices.'),
('Machine Learning', 'Hands-On Machine Learning with Scikit-Learn', 'course', 'OReilly / Geron',                  'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/', 40, 'Paid', 'intermediate', 'Practical ML with scikit-learn and TensorFlow.'),
('Machine Learning', 'Build an ML Classification Model Project', 'project',  'Self-directed',                     'https://scikit-learn.org/stable/tutorial/index.html',          20,  'Free',           'intermediate',  'Build and evaluate a classification model using a real dataset from Kaggle.'),

-- â"€â"€ DEEP LEARNING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Deep Learning', 'Deep Learning Specialization',           'certification', 'Coursera / deeplearning.ai',        'https://www.coursera.org/specializations/deep-learning',       120, 'Free to audit',  'advanced',      'Five-course deep learning specialization by Andrew Ng.'),
('Deep Learning', 'Fast.ai Practical Deep Learning',        'course',        'fast.ai',                           'https://course.fast.ai/',                                      30,  'Free',           'intermediate',  'Practical deep learning for coders using PyTorch.'),

-- â"€â"€ NLP â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Natural Language Processing', 'Natural Language Processing Specialization', 'certification', 'Coursera / deeplearning.ai', 'https://www.coursera.org/specializations/natural-language-processing', 80, 'Free to audit', 'advanced', 'Four-course NLP specialization covering attention models and transformers.'),
('Natural Language Processing', 'Build an NLP Text Classifier Project', 'project', 'Self-directed',               'https://huggingface.co/learn/nlp-course/',                     20,  'Free',           'intermediate',  'Build a sentiment analysis or text classification model using Hugging Face.'),

-- â"€â"€ CLOUD COMPUTING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Cloud Computing', 'AWS Cloud Practitioner Certification (CLF-C02)', 'certification', 'AWS',                     'https://aws.amazon.com/certification/certified-cloud-practitioner/', 40, '$100 USD',  'beginner',      'Entry-level AWS certification covering core cloud concepts and services.'),
('Cloud Computing', 'Google Cloud Digital Leader Certification', 'certification', 'Google Cloud',                 'https://cloud.google.com/certification/cloud-digital-leader',   20,  '$200 USD',       'beginner',      'Google Cloud entry-level certification for business and technical roles.'),
('Cloud Computing', 'Cloud Computing Foundations',           'course',        'Coursera / Duke University',        'https://www.coursera.org/learn/cloud-computing-foundations-duke', 12, 'Free to audit', 'beginner',     'Fundamentals of cloud computing including IaaS, PaaS, and SaaS.'),

-- â"€â"€ AWS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('AWS',    'AWS Certified Solutions Architect â€" Associate (SAA-C03)', 'certification', 'AWS',                     'https://aws.amazon.com/certification/certified-solutions-architect-associate/', 80, '$150 USD', 'intermediate', 'Most popular AWS certification for designing cloud architectures.'),
('AWS',    'AWS Skill Builder â€" Cloud Practitioner Learning Plan', 'course',   'AWS Skill Builder',               'https://explore.skillbuilder.aws/learn/lp/82/cloud-essentials-learning-plan', 20, 'Free', 'beginner',    'Official AWS free training for Cloud Practitioner certification.'),
('AWS',    'Deploy a Simple App on AWS EC2',                 'project',       'Self-directed',                     'https://aws.amazon.com/getting-started/hands-on/',              10,  'Free tier',      'beginner',      'Deploy a simple web application on AWS EC2 using the free tier.'),

-- â"€â"€ AZURE â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Azure',  'Microsoft Azure Fundamentals (AZ-900)',          'certification', 'Microsoft',                         'https://learn.microsoft.com/en-us/certifications/azure-fundamentals/', 32, '$165 USD',  'beginner',      'Entry-level Azure certification covering core cloud concepts.'),
('Azure',  'Microsoft Azure Fundamentals Learning Path',     'course',        'Microsoft Learn',                   'https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/', 10, 'Free',      'beginner',      'Free Microsoft learning path for Azure Fundamentals (AZ-900).'),

-- â"€â"€ GCP â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('GCP',    'Associate Cloud Engineer Certification',         'certification', 'Google Cloud',                      'https://cloud.google.com/certification/cloud-engineer',         30,  '$200 USD',       'intermediate',  'Google Cloud certification for deploying and managing applications.'),
('GCP',    'Google Cloud Skills Boost',                      'course',        'Google Cloud',                      'https://www.cloudskillsboost.google/',                         20,  'Free credits',   'beginner',      'Hands-on labs and learning paths for Google Cloud.'),

-- â"€â"€ DOCKER â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Docker', 'Docker and Kubernetes: The Complete Guide',      'course',        'Udemy / Stephen Grider',            'https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/', 22, 'Paid ~$15', 'intermediate', 'Complete guide to Docker containers and Kubernetes orchestration.'),
('Docker', 'Docker Official Get Started Tutorial',           'course',        'Docker',                            'https://docs.docker.com/get-started/',                         5,   'Free',           'beginner',      'Official Docker tutorial for containerising and deploying applications.'),
('Docker', 'Containerise a Python App Project',              'project',       'Self-directed',                     'https://docs.docker.com/language/python/',                     8,   'Free',           'beginner',      'Containerise the SEAGAS backend or a personal project using Docker.'),

-- â"€â"€ KUBERNETES â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Kubernetes', 'Certified Kubernetes Administrator (CKA)',   'certification', 'CNCF',                              'https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/', 40, '$395 USD', 'advanced', 'Industry-standard Kubernetes administrator certification.'),
('Kubernetes', 'Kubernetes for the Absolute Beginners',      'course',        'Udemy / KodeKloud',                 'https://www.udemy.com/course/learn-kubernetes/',               8,   'Paid ~$15',      'beginner',      'Hands-on Kubernetes course for beginners with labs.'),

-- â"€â"€ GIT â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Git',    'Git and GitHub â€" The Complete Git Guide',        'course',        'Udemy',                             'https://www.udemy.com/course/git-and-github-bootcamp/',        17,  'Paid ~$15',      'beginner',      'Complete Git version control and GitHub collaboration guide.'),
('Git',    'GitHub Skills Interactive Courses',              'course',        'GitHub',                            'https://skills.github.com/',                                   6,   'Free',           'beginner',      'Official interactive GitHub courses for version control basics.'),

-- â"€â"€ LINUX â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Linux',  'Linux Foundation Certified System Administrator (LFCS)', 'certification', 'Linux Foundation',          'https://training.linuxfoundation.org/certification/linux-foundation-certified-sysadmin-lfcs/', 40, '$395 USD', 'intermediate', 'Professional Linux system administration certification.'),
('Linux',  'The Linux Command Line Bootcamp',                'course',        'Udemy / Colt Steele',               'https://www.udemy.com/course/the-linux-command-line-bootcamp/', 16, 'Paid ~$15',     'beginner',      'Comprehensive Linux command line course from beginner to advanced.'),
('Linux',  'Linux Journey Interactive Tutorial',             'course',        'Linux Journey',                     'https://linuxjourney.com/',                                    10,  'Free',           'beginner',      'Free interactive Linux tutorial covering commands, processes, and networking.'),

-- â"€â"€ PANDAS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Pandas', 'Data Analysis with Pandas and Python',           'course',        'Udemy / Boris Paskhaver',           'https://www.udemy.com/course/data-analysis-with-pandas/',      20,  'Paid ~$15',      'intermediate',  'Complete Pandas course for data manipulation and analysis.'),
('Pandas', 'Kaggle Pandas Course',                           'course',        'Kaggle',                            'https://www.kaggle.com/learn/pandas',                          4,   'Free',           'beginner',      'Free hands-on Pandas course with exercises and immediate feedback.'),
('Pandas', 'Exploratory Data Analysis Project',              'project',       'Self-directed',                     'https://www.kaggle.com/datasets',                              15,  'Free',           'intermediate',  'Perform an end-to-end EDA on a Kaggle dataset using Pandas, NumPy and Matplotlib.'),

-- â"€â"€ STATISTICAL ANALYSIS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Statistical Analysis', 'Statistics with Python Specialization', 'certification', 'Coursera / University of Michigan', 'https://www.coursera.org/specializations/statistics-with-python', 48, 'Free to audit', 'intermediate', 'Three-course specialization covering statistical inference and modelling.'),
('Statistical Analysis', 'Khan Academy Statistics and Probability', 'course',   'Khan Academy',                    'https://www.khanacademy.org/math/statistics-probability',      20,  'Free',           'beginner',      'Free statistics course covering probability, distributions and hypothesis testing.'),

-- â"€â"€ CYBERSECURITY â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Cybersecurity', 'CompTIA Security+ Certification (SY0-701)', 'certification', 'CompTIA',                         'https://www.comptia.org/certifications/security',              40,  '$392 USD',       'intermediate',  'Most popular entry-level cybersecurity certification covering security fundamentals.'),
('Cybersecurity', 'Google Cybersecurity Certificate',         'certification', 'Coursera / Google',                 'https://www.coursera.org/professional-certificates/google-cybersecurity', 180, 'Free to audit', 'beginner', 'Six-month Google cybersecurity professional certificate.'),
('Cybersecurity', 'TryHackMe â€" Pre-Security Learning Path',   'course',        'TryHackMe',                         'https://tryhackme.com/path/outline/presecurity',               40,  'Free / $14/mo',  'beginner',      'Hands-on cybersecurity learning platform with guided rooms and labs.'),

-- â"€â"€ ETHICAL HACKING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Ethical Hacking', 'Certified Ethical Hacker (CEH)',         'certification', 'EC-Council',                        'https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/', 40, '$950 USD',   'advanced',      'Industry-standard ethical hacking certification.'),
('Ethical Hacking', 'Practical Ethical Hacking â€" TCM Security', 'course',      'TCM Security',                      'https://academy.tcm-sec.com/p/practical-ethical-hacking-the-complete-course', 25, 'Paid ~$30', 'intermediate', 'Hands-on ethical hacking course covering network and web exploitation.'),
('Ethical Hacking', 'HackTheBox Academy Labs',                'project',       'HackTheBox',                        'https://academy.hackthebox.com/',                              30,  'Free / Paid',    'intermediate',  'Complete hands-on cybersecurity labs to build penetration testing skills.'),

-- â"€â"€ NETWORK SECURITY â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Network Security', 'CompTIA Network+ Certification (N10-009)', 'certification', 'CompTIA',                        'https://www.comptia.org/certifications/network',               40,  '$338 USD',       'intermediate',  'Network security and administration certification.'),
('Network Security', 'Cisco CCNA Certification (200-301)',     'certification', 'Cisco',                             'https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html', 80, '$330 USD', 'intermediate', 'Industry-standard networking certification covering routing, switching and security.'),
('Network Security', 'Cybrary Network Security Fundamentals',  'course',        'Cybrary',                           'https://www.cybrary.it/course/network-security-fundamentals/', 10,  'Free',           'beginner',      'Free network security fundamentals course on Cybrary.'),

-- â"€â"€ WIRESHARK â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Wireshark', 'Wireshark for Beginners: Capture Packets',    'course',        'Udemy',                             'https://www.udemy.com/course/wireshark-for-beginners-capture-packets/', 3, 'Free',       'beginner',      'Learn network packet analysis with Wireshark from scratch.'),
('Wireshark', 'Analyse a Network Capture Project',           'project',       'Self-directed',                     'https://www.wireshark.org/docs/wsug_html_chunked/',            8,   'Free',           'beginner',      'Capture and analyse network traffic for a home or lab network using Wireshark.'),

-- â"€â"€ TENSORFLOW â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('TensorFlow', 'TensorFlow Developer Certificate',            'certification', 'Google / TensorFlow',               'https://www.tensorflow.org/certificate',                       40,  '$100 USD',       'intermediate',  'Official Google TensorFlow developer certification.'),
('TensorFlow', 'TensorFlow for Beginners',                    'course',        'Coursera / deeplearning.ai',        'https://www.coursera.org/learn/introduction-tensorflow',       16,  'Free to audit',  'beginner',      'Introduction to TensorFlow for deep learning.'),

-- â"€â"€ PYTORCH â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('PyTorch', 'PyTorch for Deep Learning Bootcamp',             'course',        'Udemy / Jose Portilla',             'https://www.udemy.com/course/pytorch-for-deep-learning-bootcamp/', 17, 'Paid ~$15',  'intermediate',  'Complete PyTorch bootcamp from basics to advanced deep learning.'),
('PyTorch', 'Build an Image Classification Model with PyTorch', 'project',     'Self-directed',                     'https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html', 12, 'Free',     'intermediate',  'Train a convolutional neural network for image classification.'),

-- â"€â"€ COMMUNICATION â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Communication', 'Improving Communication Skills',           'course',        'Coursera / University of Pennsylvania', 'https://www.coursera.org/learn/wharton-communication-skills', 10, 'Free to audit', 'beginner', 'Practical communication skills for professional settings.'),
('Communication', 'Join a Toastmasters Club',                 'workshop',      'Toastmasters International',        'https://www.toastmasters.org/find-a-club',                     12,  'Low cost',       'beginner',      'Join a Toastmasters club to practise public speaking and presentation skills.'),
('Communication', 'Technical Writing Fundamentals',           'course',        'Coursera / Google',                 'https://www.coursera.org/learn/technical-writing-101',         10,  'Free to audit',  'beginner',      'Learn to write clear technical documentation and reports.'),

-- â"€â"€ PROJECT MANAGEMENT â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Project Management', 'Google Project Management Certificate', 'certification', 'Coursera / Google',               'https://www.coursera.org/professional-certificates/google-project-management', 180, 'Free to audit', 'beginner', 'Six-month Google project management professional certificate.'),
('Project Management', 'Agile with Atlassian Jira',           'course',        'Coursera / Atlassian',              'https://www.coursera.org/learn/agile-atlassian-jira',          8,   'Free to audit',  'beginner',      'Learn agile project management using Jira.'),

-- â"€â"€ CRITICAL THINKING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Critical Thinking', 'Critical Thinking and Problem Solving', 'course',       'Coursera / Rochester Institute',    'https://www.coursera.org/learn/critical-thinking-problem-solving', 16, 'Free to audit', 'beginner', 'Develop critical thinking and analytical problem solving skills.'),

-- â"€â"€ DATA ANALYSIS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Data Analysis', 'Google Data Analytics Certificate',        'certification', 'Coursera / Google',                 'https://www.coursera.org/professional-certificates/google-data-analytics', 240, 'Free to audit', 'beginner', 'Comprehensive six-month Google data analytics certificate covering SQL, R, Tableau and more.'),
('Data Analysis', 'IBM Data Analyst Professional Certificate', 'certification', 'Coursera / IBM',                   'https://www.coursera.org/professional-certificates/ibm-data-analyst', 200, 'Free to audit', 'beginner', 'IBM data analyst certificate covering Python, SQL, and data visualisation.'),
('Data Analysis', 'Kaggle Data Analysis Competition',         'competition',   'Kaggle',                            'https://www.kaggle.com/competitions',                          20,  'Free',           'intermediate',  'Participate in a Kaggle competition to demonstrate real-world data analysis skills.'),

-- â"€â"€ MLOPS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('MLOps', 'MLOps Specialization',                             'certification', 'Coursera / deeplearning.ai',        'https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops', 64, 'Free to audit', 'advanced', 'Four-course MLOps specialization covering deploying and monitoring ML models.'),
('MLOps', 'Deploy a Machine Learning Model with FastAPI',     'project',       'Self-directed',                     'https://fastapi.tiangolo.com/tutorial/',                       15,  'Free',           'intermediate',  'Package and deploy an ML model as a REST API using FastAPI and Docker.'),

-- â"€â"€ VULNERABILITY ASSESSMENT â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Vulnerability Assessment', 'CompTIA PenTest+ Certification', 'certification', 'CompTIA',                          'https://www.comptia.org/certifications/pentest',               40,  '$392 USD',       'intermediate',  'Penetration testing and vulnerability assessment certification.'),
('Vulnerability Assessment', 'OWASP Web Security Testing Guide', 'course',      'OWASP',                             'https://owasp.org/www-project-web-security-testing-guide/',    20,  'Free',           'intermediate',  'Learn web application vulnerability testing using the OWASP framework.'),
('Vulnerability Assessment', 'Perform a Vulnerability Scan Project', 'project', 'Self-directed',                    'https://www.tenable.com/products/nessus/nessus-essentials',    10,  'Free',           'beginner',      'Use Nessus Essentials (free) to scan a lab environment and document findings.'),

-- â"€â"€ INCIDENT RESPONSE â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Incident Response', 'CompTIA CySA+ Cybersecurity Analyst',  'certification', 'CompTIA',                           'https://www.comptia.org/certifications/cybersecurity-analyst', 40,  '$392 USD',       'intermediate',  'Cybersecurity analyst certification covering incident detection and response.'),
('Incident Response', 'TryHackMe SOC Level 1 Path',           'course',        'TryHackMe',                         'https://tryhackme.com/path/outline/soclevel1',                 60,  'Free / $14/mo',  'beginner',      'Hands-on SOC analyst training covering SIEM, log analysis and incident response.'),

-- â"€â"€ TEAMWORK â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Teamwork', 'Collaborate on a GitHub Open Source Project',   'project',       'GitHub',                            'https://github.com/explore',                                   15,  'Free',           'beginner',      'Contribute to an open source project on GitHub to demonstrate collaboration skills.'),
('Teamwork', 'Everyday Leadership',                           'course',        'Coursera / Duke University',        'https://www.coursera.org/learn/everyday-leadership-new',       6,   'Free to audit',  'beginner',      'Develop teamwork and everyday leadership skills.'),

-- â"€â"€ DOCUMENTATION â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Documentation', 'Technical Writing for Developers',         'course',        'Udemy',                             'https://www.udemy.com/course/technical-writing-for-developers/', 6,  'Paid ~$15',      'beginner',      'Learn to write technical documentation, README files and API docs.'),
('Documentation', 'Write a Complete Project README',          'project',       'Self-directed',                     'https://www.makeareadme.com/',                                  5,   'Free',           'beginner',      'Write a professional README for a GitHub project including setup, usage and contribution guides.'),

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- SECTION 2 â€" WEB DEVELOPER SKILLS (from v2)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

-- â"€â"€ HTML / CSS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('HTML',         'Responsive Web Design Certification',           'certification', 'freeCodeCamp',              'https://www.freecodecamp.org/learn/2022/responsive-web-design/',       300, 'Free',          'beginner',      'Full HTML and CSS certification including flexbox, grid and responsive design.'),
('HTML',         'HTML and CSS for Beginners',                    'course',        'Udemy',                     'https://www.udemy.com/course/html-and-css-for-beginners-crash-course-learn-fast-easy/', 5, 'Free', 'beginner', 'Quick and practical HTML and CSS crash course for beginners.'),
('HTML',         'Build a Personal Portfolio Website',            'project',       'Self-directed',             'https://www.freecodecamp.org/learn',                                   10,  'Free',          'beginner',      'Build a personal portfolio website using HTML and CSS to showcase your projects.'),

('CSS',          'CSS Grid and Flexbox for Responsive Layouts',   'course',        'Udemy',                     'https://www.udemy.com/course/css-flexbox-and-grid/',                   6,   'Paid ~$15',     'intermediate',  'Master modern CSS layout techniques including flexbox and grid.'),
('CSS',          'CSS â€" The Complete Guide',                      'course',        'Udemy / Maximilian',        'https://www.udemy.com/course/css-the-complete-guide-incl-flexbox-grid-sass/', 22, 'Paid ~$15', 'beginner',  'Comprehensive CSS course from basics to animations and SASS.'),
('CSS',          'Style a React Dashboard Project',               'project',       'Self-directed',             'https://tailwindcss.com/docs/installation',                            8,   'Free',          'intermediate',  'Apply a consistent CSS framework (Tailwind or Bootstrap) to a React project.'),

-- â"€â"€ TYPESCRIPT â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('TypeScript',   'Understanding TypeScript',                      'course',        'Udemy / Maximilian',        'https://www.udemy.com/course/understanding-typescript/',               22,  'Paid ~$15',     'intermediate',  'Complete TypeScript course covering types, generics, decorators and React integration.'),
('TypeScript',   'TypeScript Official Handbook',                  'course',        'Microsoft',                 'https://www.typescriptlang.org/docs/handbook/intro.html',             10,  'Free',          'beginner',      'Official TypeScript documentation and learning guide.'),
('TypeScript',   'Convert a JavaScript Project to TypeScript',    'project',       'Self-directed',             'https://www.typescriptlang.org/docs/handbook/migrating-from-javascript.html', 8, 'Free', 'intermediate', 'Migrate an existing JavaScript project to TypeScript as a portfolio exercise.'),

-- â"€â"€ MONGODB â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('MongoDB',      'MongoDB Atlas Developer Certification',         'certification', 'MongoDB',                   'https://learn.mongodb.com/pages/mongodb-associate-developer-exam', 20,   '$150 USD',      'intermediate',  'Official MongoDB developer certification for CRUD operations and schema design.'),
('MongoDB',      'MongoDB University Free Courses',               'course',        'MongoDB',                   'https://learn.mongodb.com/',                                          10,  'Free',          'beginner',      'Free official MongoDB courses covering basics, aggregation and indexing.'),
('MongoDB',      'Build a REST API with Node.js and MongoDB',     'project',       'Self-directed',             'https://www.mongodb.com/developer/languages/javascript/',             15,  'Free',          'intermediate',  'Build a full CRUD REST API using Node.js, Express and MongoDB Atlas.'),

-- â"€â"€ VUE.JS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Vue.js',       'Vue â€" The Complete Guide',                      'course',        'Udemy / Maximilian',        'https://www.udemy.com/course/vuejs-2-the-complete-guide/',            32,  'Paid ~$15',     'intermediate',  'Complete Vue.js course covering Vue 3, Vuex, Vue Router and Composition API.'),
('Vue.js',       'Vue.js Official Documentation',                 'course',        'Vue.js',                    'https://vuejs.org/guide/introduction.html',                           10,  'Free',          'beginner',      'Official Vue.js guide and documentation for building reactive web applications.'),
('Vue.js',       'Build a Task Management App with Vue',          'project',       'Self-directed',             'https://vuejs.org/tutorial/',                                         12,  'Free',          'intermediate',  'Build a task management or to-do application using Vue 3 and Pinia.'),

-- â"€â"€ NODE.JS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Node.js',      'The Complete Node.js Developer Course',         'course',        'Udemy / Andrew Mead',       'https://www.udemy.com/course/the-complete-nodejs-developer-course-2/', 35, 'Paid ~$15',    'intermediate',  'Complete Node.js course covering Express, MongoDB, REST APIs and authentication.'),
('Node.js',      'Node.js Official Documentation',                'course',        'Node.js',                   'https://nodejs.org/en/learn/getting-started/introduction-to-nodejs', 8,   'Free',         'beginner',      'Official Node.js documentation and getting started guide.'),
('Node.js',      'Build a REST API with Node.js and Express',     'project',       'Self-directed',             'https://expressjs.com/en/starter/hello-world.html',                   12,  'Free',          'intermediate',  'Build and document a RESTful API using Node.js, Express and a database.'),

-- â"€â"€ EXPRESS.JS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Express.js',   'Node.js and Express.js â€" Full Course',          'course',        'freeCodeCamp / YouTube',    'https://www.youtube.com/watch?v=Oe421EPjeBE',                         8,   'Free',          'beginner',      'Free 8-hour Node.js and Express.js full course on YouTube by freeCodeCamp.'),
('Express.js',   'Build a JWT Authentication API',                'project',       'Self-directed',             'https://expressjs.com/en/guide/routing.html',                         10,  'Free',          'intermediate',  'Build a complete authentication system using Express.js and JWT tokens.'),

-- â"€â"€ PHP â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('PHP',          'PHP for Beginners',                             'course',        'Laracasts',                 'https://laracasts.com/series/php-for-beginners-2023-edition',         10,  'Free',          'beginner',      'Free beginner PHP series on Laracasts covering modern PHP development.'),
('PHP',          'Build a PHP CRUD Application',                  'project',       'Self-directed',             'https://www.php.net/manual/en/tutorial.php',                          10,  'Free',          'beginner',      'Build a simple CRUD web application using PHP and MySQL.'),

-- â"€â"€ GRAPHQL â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('GraphQL',      'GraphQL with React: The Complete Developers Guide', 'course',    'Udemy / Stephen Grider',    'https://www.udemy.com/course/graphql-with-react-course/',             13,  'Paid ~$15',     'intermediate',  'Learn GraphQL by building real-world React applications.'),
('GraphQL',      'GraphQL Official Documentation',                'course',        'GraphQL',                   'https://graphql.org/learn/',                                           6,   'Free',          'beginner',      'Official GraphQL learning guide and documentation.'),

-- â"€â"€ REST API â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('REST API',     'REST API Design Best Practices',                'course',        'Udemy',                     'https://www.udemy.com/course/rest-api/',                              4,   'Paid ~$15',     'intermediate',  'Learn REST API design principles and best practices.'),
('REST API',     'Build and Document a REST API',                 'project',       'Self-directed',             'https://swagger.io/docs/specification/basic-structure/',              10,  'Free',          'intermediate',  'Build a REST API and document it with Swagger/OpenAPI specification.'),

-- â"€â"€ UI/UX DESIGN â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('UI/UX Design', 'Google UX Design Certificate',                  'certification', 'Coursera / Google',         'https://www.coursera.org/professional-certificates/google-ux-design', 240, 'Free to audit', 'beginner',    'Six-month Google UX design professional certificate covering the full design process.'),
('UI/UX Design', 'UI / UX Design Bootcamp',                       'course',        'Udemy',                     'https://www.udemy.com/course/ui-ux-design-bootcamp/',                20,  'Paid ~$15',     'beginner',      'Complete UI/UX design bootcamp covering Figma, wireframing and prototyping.'),
('UI/UX Design', 'Design a Mobile App in Figma',                  'project',       'Self-directed',             'https://www.figma.com/resources/learn-design/',                       12,  'Free',          'beginner',      'Design a complete mobile app UI in Figma including wireframes and prototype.'),

-- â"€â"€ UNIT TESTING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Unit Testing',  'JavaScript Unit Testing â€" The Practical Guide', 'course',       'Udemy / Maximilian',        'https://www.udemy.com/course/javascript-unit-testing-the-practical-guide/', 8, 'Paid ~$15', 'intermediate', 'Learn unit and integration testing with Jest and Vitest.'),
('Unit Testing',  'Write Unit Tests for a React App',              'project',       'Self-directed',             'https://jestjs.io/docs/getting-started',                              8,   'Free',          'intermediate',  'Write unit and integration tests for an existing React application using Jest.'),

-- â"€â"€ AGILE / SCRUM â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Agile / Scrum', 'Professional Scrum Master I (PSM I)',           'certification', 'Scrum.org',                 'https://www.scrum.org/assessments/professional-scrum-master-i-certification', 10, '$150 USD', 'intermediate', 'Entry-level Scrum Master certification from Scrum.org.'),
('Agile / Scrum', 'Agile Crash Course: Agile Project Management',  'course',        'Udemy',                     'https://www.udemy.com/course/agile-crash-course/',                    3,   'Free',          'beginner',      'Quick introduction to agile and Scrum methodology.'),

-- â"€â"€ PROBLEM SOLVING â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Problem Solving', 'LeetCode Problem Solving Practice',           'course',        'LeetCode',                  'https://leetcode.com/study-plan/leetcode-75/',                        30,  'Free / Paid',   'intermediate',  'Structured LeetCode 75 study plan covering essential data structures and algorithms.'),
('Problem Solving', 'Solve 30 LeetCode Easy Problems',             'project',       'Self-directed',             'https://leetcode.com/problemset/?difficulty=EASY',                    20,  'Free',          'beginner',      'Complete 30 easy LeetCode problems to build problem solving confidence and skills.'),

-- â"€â"€ FIGMA â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Figma',        'Figma UI UX Design Essentials',                  'course',        'Udemy',                     'https://www.udemy.com/course/figma-ux-ui-design-user-experience-tutorial-course/', 12, 'Paid ~$15', 'beginner', 'Learn Figma from scratch for UI/UX design and prototyping.'),
('Figma',        'Figma for Beginners Tutorial',                   'course',        'Figma',                     'https://www.youtube.com/playlist?list=PLXDU_eVOJTx7QHLShNqIXL1Cgbxj7HlN4', 5, 'Free', 'beginner', 'Official Figma beginner tutorial series on YouTube.'),
('Figma',        'Design a Website Prototype in Figma',            'project',       'Self-directed',             'https://www.figma.com/templates/',                                    10,  'Free',          'beginner',      'Design a complete website prototype with responsive layouts in Figma.'),

-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
-- SECTION 3 â€" REMAINING 87 SKILLS (from v3)
-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

-- â"€â"€ AI_Digital â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('AI Literacy',          'AI for Everyone',                                    'course',        'Coursera / Andrew Ng',        'https://www.coursera.org/learn/ai-for-everyone',                        6,   'Free to audit',  'beginner',      'Non-technical introduction to AI concepts, capabilities and limitations.'),
('AI Literacy',          'Elements of AI',                                     'course',        'University of Helsinki',      'https://www.elementsofai.com/',                                         6,   'Free',           'beginner',      'Free online course covering AI basics for everyone.'),

('Computer Vision',      'Deep Learning Specialization â€" CNN Course',          'course',        'Coursera / deeplearning.ai',  'https://www.coursera.org/learn/convolutional-neural-networks',          35,  'Free to audit',  'advanced',      'Learn convolutional neural networks for computer vision tasks.'),
('Computer Vision',      'Build an Image Classifier Project',                  'project',       'Self-directed',               'https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html',    15,  'Free',           'intermediate',  'Train a CNN to classify images using PyTorch and a public dataset.'),

('Feature Engineering',  'Feature Engineering for Machine Learning',           'course',        'Coursera / University of Washington', 'https://www.coursera.org/learn/feature-engineering',             20,  'Free to audit',  'intermediate',  'Learn how to create and select features for machine learning models.'),
('Feature Engineering',  'Kaggle Feature Engineering Course',                  'course',        'Kaggle',                      'https://www.kaggle.com/learn/feature-engineering',                       4,   'Free',           'intermediate',  'Free hands-on feature engineering course with practical exercises.'),

('Generative AI',        'Generative AI with Large Language Models',           'course',        'Coursera / AWS & deeplearning.ai', 'https://www.coursera.org/learn/generative-ai-with-llms',            16,  'Free to audit',  'intermediate',  'Learn how LLMs work and how to deploy generative AI applications.'),
('Generative AI',        'Build a Generative AI App with an LLM API',         'project',       'Self-directed',               'https://platform.openai.com/docs/quickstart',                            10,  'Free tier',      'intermediate',  'Build a simple chatbot or text generation app using an LLM API.'),

('Hugging Face',         'Hugging Face NLP Course',                            'course',        'Hugging Face',                'https://huggingface.co/learn/nlp-course/',                               20,  'Free',           'intermediate',  'Official Hugging Face course covering Transformers, datasets and fine-tuning.'),
('Hugging Face',         'Fine-tune a Text Classification Model',              'project',       'Self-directed',               'https://huggingface.co/docs/transformers/training',                      12,  'Free',           'intermediate',  'Fine-tune a pre-trained BERT model for a custom text classification task.'),

('Model Evaluation',     'Machine Learning Specialization â€" Model Evaluation', 'course',        'Coursera / Andrew Ng',        'https://www.coursera.org/specializations/machine-learning-introduction', 20,  'Free to audit',  'intermediate',  'Learn to evaluate and improve ML models using precision, recall and F1-score.'),
('Model Evaluation',     'Evaluate and Compare ML Models Project',             'project',       'Self-directed',               'https://scikit-learn.org/stable/modules/model_evaluation.html',          10,  'Free',           'intermediate',  'Compare multiple ML models on a dataset using scikit-learn evaluation metrics.'),

('Prompt Engineering',   'ChatGPT Prompt Engineering for Developers',          'course',        'deeplearning.ai / OpenAI',    'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/', 2, 'Free', 'beginner', 'Free short course on prompt engineering for developers by Andrew Ng and OpenAI.'),
('Prompt Engineering',   'Build a Prompt-based AI App',                        'project',       'Self-directed',               'https://platform.openai.com/docs/guides/prompt-engineering',             8,   'Free tier',      'beginner',      'Build a practical AI application using prompt engineering techniques.'),

('Responsible AI',       'AI Ethics',                                          'course',        'Coursera / University of Helsinki', 'https://ethics-of-ai.mooc.fi/',                                   6,   'Free',           'beginner',      'Free course covering the ethics, fairness and transparency of AI systems.'),
('Responsible AI',       'Responsible AI Practices',                           'course',        'Google',                      'https://ai.google/responsibility/responsible-ai-practices/',              4,   'Free',           'beginner',      'Google guidelines and resources for building responsible AI systems.'),

('Scikit-learn',         'Machine Learning with Python and Scikit-learn',      'course',        'Udemy',                       'https://www.udemy.com/course/machine-learning-with-python-and-scikit-learn/', 12, 'Paid ~$15',  'beginner',      'Hands-on ML course using scikit-learn for classification, regression and clustering.'),
('Scikit-learn',         'Scikit-learn Official Tutorials',                    'course',        'Scikit-learn',                'https://scikit-learn.org/stable/tutorial/index.html',                    8,   'Free',           'beginner',      'Official scikit-learn documentation and step-by-step tutorials.'),

('Serverless',           'AWS Lambda and Serverless Architecture Bootcamp',    'course',        'Udemy',                       'https://www.udemy.com/course/aws-lambda-serverless/',                    10,  'Paid ~$15',      'intermediate',  'Learn serverless architecture using AWS Lambda and API Gateway.'),
('Serverless',           'Deploy a Serverless API Project',                    'project',       'Self-directed',               'https://aws.amazon.com/getting-started/hands-on/run-serverless-code/',   8,   'Free tier',      'beginner',      'Build and deploy a serverless REST API using AWS Lambda and API Gateway.'),

-- â"€â"€ Analytical â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('A/B Testing',          'A/B Testing by Google',                              'course',        'Udacity / Google',            'https://www.udacity.com/course/ab-testing--ud257',                       12,  'Free',           'intermediate',  'Free course on A/B testing design, analysis and statistical significance.'),
('A/B Testing',          'Design and Analyse an A/B Test',                    'project',       'Self-directed',               'https://www.kaggle.com/datasets?search=ab+test',                         8,   'Free',           'intermediate',  'Design and analyse an A/B test using a real or simulated dataset.'),

('Business Analysis',    'Business Analysis Fundamentals',                     'course',        'Udemy',                       'https://www.udemy.com/course/business-analysis-ba/',                     9,   'Paid ~$15',      'beginner',      'Introduction to business analysis techniques and requirements gathering.'),
('Business Analysis',    'IIBA Entry Certificate in Business Analysis (ECBA)', 'certification', 'IIBA',                        'https://www.iiba.org/certification/entry-certificate-in-business-analysis/', 21, '$125 USD',    'beginner',      'Entry-level business analysis certification from IIBA.'),

('Data Cleaning',        'Data Cleaning with Python',                          'course',        'Kaggle',                      'https://www.kaggle.com/learn/data-cleaning',                             4,   'Free',           'beginner',      'Free hands-on course for cleaning messy data using Python and Pandas.'),
('Data Cleaning',        'Clean and Prepare a Real Dataset',                   'project',       'Self-directed',               'https://www.kaggle.com/datasets',                                        8,   'Free',           'beginner',      'Download a messy Kaggle dataset and clean it using Pandas best practices.'),

('Data Mining',          'Data Mining Specialization',                         'course',        'Coursera / UIUC',             'https://www.coursera.org/specializations/data-mining',                   60,  'Free to audit',  'intermediate',  'Five-course data mining specialization covering pattern discovery and clustering.'),
('Data Mining',          'Data Mining with Python',                            'course',        'Udemy',                       'https://www.udemy.com/course/data-mining-with-python/',                  6,   'Paid ~$15',      'intermediate',  'Practical data mining techniques using Python and scikit-learn.'),

('Data Modelling',       'Database Design and SQL for Beginners',              'course',        'Udemy',                       'https://www.udemy.com/course/database-design-and-sql-for-beginners/',    7,   'Paid ~$15',      'beginner',      'Learn relational database design, ER diagrams and SQL from scratch.'),
('Data Modelling',       'Design a Database Schema Project',                   'project',       'Self-directed',               'https://dbdiagram.io/',                                                   6,   'Free',           'beginner',      'Design a normalised database schema for a real-world application using dbdiagram.io.'),

('Decision Making',      'Decision Making and Scenarios',                      'course',        'Coursera / University of Pennsylvania', 'https://www.coursera.org/learn/wharton-decision-making',        8,   'Free to audit',  'beginner',      'Learn structured decision making frameworks from the Wharton School.'),
('Decision Making',      'Critical Thinking and Decision Making',              'course',        'LinkedIn Learning',           'https://www.linkedin.com/learning/topics/decision-making',               4,   'Free trial',     'beginner',      'Short courses on decision-making frameworks and critical thinking.'),

('Financial Analysis',   'Financial Modeling and Valuation Analyst (FMVA)',    'certification', 'CFI',                         'https://corporatefinanceinstitute.com/certifications/financial-modeling-valuation-analyst-fmva-program/', 200, '$497 USD', 'intermediate', 'Professional financial modelling certification from CFI.'),
('Financial Analysis',   'Introduction to Financial Analysis',                 'course',        'Coursera / Wharton',          'https://www.coursera.org/learn/financial-analysis',                      12,  'Free to audit',  'beginner',      'Learn fundamentals of financial analysis and valuation.'),

('Requirements Analysis','Business Analysis â€" Requirements Gathering',         'course',        'Udemy',                       'https://www.udemy.com/course/requirements-gathering-and-the-business-analyst/', 6, 'Paid ~$15', 'beginner',   'Learn requirements elicitation and documentation for software projects.'),
('Requirements Analysis','Write a Software Requirements Specification',        'project',       'Self-directed',               'https://www.ieee.org/publications/software-standards.html',              6,   'Free',           'intermediate',  'Write an SRS document for a personal or team project following IEEE standards.'),

('Research Skills',      'How to Write and Publish a Research Paper',          'course',        'Coursera / UC San Diego',     'https://www.coursera.org/learn/how-to-write-a-research-paper',           8,   'Free to audit',  'beginner',      'Learn academic research skills including literature review and paper writing.'),
('Research Skills',      'Conduct a Literature Review Project',                'project',       'Self-directed',               'https://www.zotero.org/',                                                 8,   'Free',           'beginner',      'Conduct a literature review on an IT topic using Zotero for reference management.'),

('Risk Analysis',        'Risk Management Professional (PMI-RMP)',             'certification', 'PMI',                         'https://www.pmi.org/certifications/risk-management-rmp',                40,  '$520 USD',       'advanced',      'PMI risk management professional certification.'),
('Risk Analysis',        'Introduction to Risk Management',                    'course',        'Coursera / UC Irvine',        'https://www.coursera.org/learn/risk-management-project',                 10,  'Free to audit',  'beginner',      'Introduction to risk identification, assessment and mitigation strategies.'),

('Systems Thinking',     'Systems Thinking and Complexity',                    'course',        'Coursera / University of Bergen', 'https://www.coursera.org/learn/systems-thinking',                    8,   'Free to audit',  'beginner',      'Learn systems thinking tools and methods for solving complex problems.'),
('Systems Thinking',     'Model a Complex System Project',                     'project',       'Self-directed',               'https://ncase.me/loopy/',                                                 5,   'Free',           'beginner',      'Map a complex system using a systems thinking tool like Loopy or Kumu.'),

-- â"€â"€ Soft â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Adaptability',         'Developing Adaptability as a Manager',               'course',        'Coursera / University of Queensland', 'https://www.coursera.org/learn/adaptability',                   6,   'Free to audit',  'beginner',      'Build adaptability and resilience in dynamic work environments.'),
('Adaptability',         'Contribute to an Open Source Project',               'project',       'GitHub',                      'https://github.com/explore',                                              10,  'Free',           'beginner',      'Contribute to an open source project to practise adapting to an existing codebase and team.'),

('Attention to Detail',  'Improve Attention to Detail',                        'course',        'LinkedIn Learning',           'https://www.linkedin.com/learning/improving-your-attention-to-detail',   2,   'Free trial',     'beginner',      'Techniques for improving accuracy and attention to detail in technical work.'),
('Attention to Detail',  'Code Review Practice Project',                       'project',       'Self-directed',               'https://github.com/features/code-review',                                5,   'Free',           'beginner',      'Practise reviewing pull requests to develop attention to detail and code quality awareness.'),

('Customer Focus',       'Customer Service Fundamentals',                       'course',        'Coursera / IBM',              'https://www.coursera.org/learn/customer-service-fundamentals',           10,  'Free to audit',  'beginner',      'Learn customer service principles applicable to technical and IT roles.'),
('Customer Focus',       'User Research Methods',                               'course',        'Coursera / University of Michigan', 'https://www.coursera.org/learn/user-research',                    8,   'Free to audit',  'beginner',      'Learn user research methods to understand and address customer needs.'),

('Interpersonal Skills', 'Inspiring and Motivating Individuals',               'course',        'Coursera / University of Michigan', 'https://www.coursera.org/learn/inspire-motivate',                  6,   'Free to audit',  'beginner',      'Build interpersonal communication and motivation skills for team environments.'),
('Interpersonal Skills', 'Participate in a Hackathon',                         'project',       'Devpost',                     'https://devpost.com/hackathons',                                          16,  'Free',           'beginner',      'Join a hackathon to develop collaboration and interpersonal skills under time pressure.'),

('Leadership',           'Leadership and Emotional Intelligence',               'course',        'Coursera / Indian School of Business', 'https://www.coursera.org/learn/leadership',                    16,  'Free to audit',  'beginner',      'Develop leadership skills and emotional intelligence for team environments.'),
('Leadership',           'Lead a Team Project',                                 'project',       'Self-directed',               'https://www.atlassian.com/agile/scrum',                                   10,  'Free',           'beginner',      'Take a leadership role in a group project or open source contribution.'),

('Presentation Skills',  'Dynamic Public Speaking Specialization',              'certification', 'Coursera / University of Washington', 'https://www.coursera.org/specializations/public-speaking',       24,  'Free to audit',  'beginner',      'Four-course public speaking and presentation specialization.'),
('Presentation Skills',  'Give a Technical Presentation',                      'project',       'Self-directed',               'https://www.toastmasters.org/',                                           5,   'Free',           'beginner',      'Prepare and deliver a 10-minute technical presentation to peers or at a Toastmasters meeting.'),

('Self-Motivation',      'Learning How to Learn',                              'course',        'Coursera / UC San Diego',     'https://www.coursera.org/learn/learning-how-to-learn',                   15,  'Free to audit',  'beginner',      'Science-based techniques for learning more effectively and maintaining self-motivation.'),
('Self-Motivation',      'Complete a 30-Day Coding Challenge',                 'project',       'Self-directed',               'https://leetcode.com/',                                                   20,  'Free',           'beginner',      'Complete a structured 30-day coding or learning challenge to build discipline and self-motivation.'),

('Stakeholder Communication', 'Stakeholder Management',                        'course',        'Coursera / University of Queensland', 'https://www.coursera.org/learn/stakeholder-management',          8,   'Free to audit',  'beginner',      'Learn to identify, engage and communicate with project stakeholders effectively.'),
('Stakeholder Communication', 'Write a Project Status Report',                 'project',       'Self-directed',               'https://www.pmi.org/learning/library/status-reports-best-practices',    4,   'Free',           'beginner',      'Write a professional project status report for a real or simulated project.'),

('Time Management',      'Work Smarter Not Harder: Time Management',           'course',        'Coursera / UC Irvine',        'https://www.coursera.org/learn/work-smarter-not-harder',                 4,   'Free to audit',  'beginner',      'Practical time management techniques for students and professionals.'),
('Time Management',      'Use a Personal Productivity System for One Month',   'project',       'Self-directed',               'https://todoist.com/',                                                    4,   'Free',           'beginner',      'Implement a time management system (GTD, Pomodoro or similar) for one month and reflect on results.'),

-- â"€â"€ Technical (v3) â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
('Angular',              'Angular â€" The Complete Guide',                        'course',        'Udemy / Maximilian',          'https://www.udemy.com/course/the-complete-guide-to-angular-2/',          36,  'Paid ~$15',      'intermediate',  'Complete Angular course from basics to advanced components, services and routing.'),
('Angular',              'Build an Angular Dashboard App',                     'project',       'Self-directed',               'https://angular.io/tutorial',                                             15,  'Free',           'intermediate',  'Build a data dashboard using Angular following the official tutorial.'),

('Ansible',              'Ansible for the Absolute Beginner',                  'course',        'Udemy / KodeKloud',           'https://www.udemy.com/course/learn-ansible/',                             4,   'Paid ~$15',      'beginner',      'Hands-on Ansible automation course for beginners.'),
('Ansible',              'Automate a Server Setup with Ansible',               'project',       'Self-directed',               'https://docs.ansible.com/ansible/latest/getting_started/',               6,   'Free',           'beginner',      'Write an Ansible playbook to automate server provisioning and configuration.'),

('Apache Spark',         'Apache Spark with Python â€" Big Data with PySpark',   'course',        'Udemy',                       'https://www.udemy.com/course/apache-spark-with-python-big-data/',        14,  'Paid ~$15',      'intermediate',  'Learn big data processing with Apache Spark and PySpark.'),
('Apache Spark',         'Databricks Certified Associate Developer for Apache Spark', 'certification', 'Databricks',           'https://www.databricks.com/learn/certification/apache-spark-developer-associate', 20, '$200 USD', 'intermediate', 'Official Apache Spark developer certification from Databricks.'),

('Bash',                 'Linux Shell Scripting: A Project-Based Approach',    'course',        'Udemy',                       'https://www.udemy.com/course/linux-shell-scripting-projects/',           8,   'Paid ~$15',      'beginner',      'Learn Bash scripting through hands-on projects for automation.'),
('Bash',                 'Write a Bash Automation Script',                     'project',       'Self-directed',               'https://www.shellscript.sh/',                                             6,   'Free',           'beginner',      'Write a Bash script to automate a repetitive task such as backup or log monitoring.'),

('Burp Suite',           'Web Application Ethical Hacking â€" Burp Suite',       'course',        'Udemy',                       'https://www.udemy.com/course/web-application-ethical-hacking/',          7,   'Paid ~$15',      'intermediate',  'Learn web application penetration testing using Burp Suite.'),
('Burp Suite',           'Complete a Burp Suite Web Penetration Test Lab',     'project',       'PortSwigger',                 'https://portswigger.net/web-security',                                    15,  'Free',           'intermediate',  'Complete PortSwigger Web Security Academy labs using Burp Suite Community Edition.'),

('C#',                   'C# Basics for Beginners',                            'course',        'Udemy / Mosh Hamedani',       'https://www.udemy.com/course/csharp-tutorial-for-beginners/',            5,   'Paid ~$15',      'beginner',      'Learn C# fundamentals including OOP, arrays and error handling.'),
('C#',                   'Build a C# Console Application',                     'project',       'Self-directed',               'https://learn.microsoft.com/en-us/dotnet/csharp/tutorials/',              10,  'Free',           'beginner',      'Build a C# console application following Microsoft tutorials.'),

('C++',                  'Beginning C++ Programming â€" From Beginner to Beyond', 'course',       'Udemy',                       'https://www.udemy.com/course/beginning-c-plus-plus-programming/',        46,  'Paid ~$15',      'beginner',      'Comprehensive C++ course covering OOP, templates, STL and modern C++.'),
('C++',                  'Build a Data Structures Project in C++',             'project',       'Self-directed',               'https://www.learncpp.com/',                                               15,  'Free',           'intermediate',  'Implement common data structures (linked list, stack, queue) in C++.'),

('CI/CD',                'GitHub Actions â€" The Complete Guide',                'course',        'Udemy',                       'https://www.udemy.com/course/github-actions-the-complete-guide/',         8,   'Paid ~$15',      'intermediate',  'Learn CI/CD pipelines using GitHub Actions from scratch to advanced workflows.'),
('CI/CD',                'Set Up a CI/CD Pipeline for a Project',              'project',       'Self-directed',               'https://docs.github.com/en/actions/quickstart',                           6,   'Free',           'intermediate',  'Set up a GitHub Actions CI/CD pipeline for an existing project with automated tests.'),

('Cryptography',         'Cryptography I',                                     'course',        'Coursera / Stanford',         'https://www.coursera.org/learn/crypto',                                   23,  'Free to audit',  'advanced',      'Rigorous introduction to cryptography from Stanford University.'),
('Cryptography',         'Applied Cryptography Fundamentals',                  'course',        'Udemy',                       'https://www.udemy.com/course/applied-cryptography-fundamentals/',         5,   'Paid ~$15',      'intermediate',  'Practical cryptography concepts including encryption, hashing and PKI.'),

('Data Structures & Algorithms', 'Data Structures and Algorithms Specialization', 'certification', 'Coursera / UC San Diego', 'https://www.coursera.org/specializations/data-structures-algorithms',    80,  'Free to audit',  'intermediate',  'Six-course DSA specialization covering sorting, graphs and dynamic programming.'),
('Data Structures & Algorithms', 'Solve 50 LeetCode Problems',                'project',       'LeetCode',                    'https://leetcode.com/study-plan/leetcode-75/',                            30,  'Free',           'intermediate',  'Complete the LeetCode 75 study plan covering core data structures and algorithms.'),

('Data Warehousing',     'Data Warehousing for Business Intelligence Specialization', 'certification', 'Coursera / UC Colorado', 'https://www.coursera.org/specializations/data-warehousing',          60,  'Free to audit',  'intermediate',  'Four-course specialization on data warehouse design and business intelligence.'),
('Data Warehousing',     'Design a Simple Data Warehouse',                    'project',       'Self-directed',               'https://aws.amazon.com/redshift/getting-started/',                        10,  'Free tier',      'intermediate',  'Design and implement a star schema data warehouse using a cloud service.'),

('Digital Forensics',    'Computer Hacking Forensic Investigator (CHFI)',      'certification', 'EC-Council',                  'https://www.eccouncil.org/programs/computer-hacking-forensic-investigator-chfi/', 40, '$950 USD', 'advanced', 'Industry-standard digital forensics certification from EC-Council.'),
('Digital Forensics',    'Digital Forensics with Autopsy',                    'course',        'TryHackMe',                   'https://tryhackme.com/module/digital-forensics-and-incident-response',   20,  'Free / $14/mo',  'intermediate',  'Learn digital forensics and incident response using Autopsy and other tools.'),

('Django',               'Django for Everybody Specialization',               'certification', 'Coursera / University of Michigan', 'https://www.coursera.org/specializations/django',                   32,  'Free to audit',  'intermediate',  'Four-course Django specialization covering web development and databases.'),
('Django',               'Build a Django REST API',                           'project',       'Self-directed',               'https://www.django-rest-framework.org/tutorial/quickstart/',             12,  'Free',           'intermediate',  'Build a REST API using Django and Django REST Framework.'),

('ETL',                  'ETL and Data Pipelines with Shell, Airflow and Kafka', 'course',      'Coursera / IBM',              'https://www.coursera.org/learn/etl-and-data-pipelines-shell-airflow-kafka', 12, 'Free to audit', 'intermediate', 'Learn ETL pipeline design using Apache Airflow and Kafka.'),
('ETL',                  'Build an ETL Pipeline Project',                     'project',       'Self-directed',               'https://airflow.apache.org/docs/apache-airflow/stable/tutorial/',        10,  'Free',           'intermediate',  'Build a simple ETL pipeline using Python and Apache Airflow.'),

('FastAPI',              'FastAPI â€" The Complete Course',                      'course',        'Udemy',                       'https://www.udemy.com/course/fastapi-the-complete-course/',              12,  'Paid ~$15',      'intermediate',  'Complete FastAPI course covering REST APIs, authentication and database integration.'),
('FastAPI',              'FastAPI Official Documentation Tutorial',            'course',        'FastAPI',                     'https://fastapi.tiangolo.com/tutorial/',                                   6,   'Free',           'beginner',      'Official FastAPI tutorial covering all core features.'),

('Firewall Management',  'Network Security: Firewalls and VPNs',              'course',        'Coursera',                    'https://www.coursera.org/learn/network-security-firewalls-vpns',          8,   'Free to audit',  'intermediate',  'Learn firewall configuration and VPN setup for network security.'),
('Firewall Management',  'Configure a Firewall Lab',                          'project',       'Self-directed',               'https://www.pfsense.org/getting-started/',                                8,   'Free',           'intermediate',  'Set up and configure pfSense firewall in a virtual lab environment.'),

('Flask',                'REST APIs with Flask and Python',                   'course',        'Udemy / Jose Salvatierra',    'https://www.udemy.com/course/rest-api-flask-and-python/',                17,  'Paid ~$15',      'intermediate',  'Build REST APIs using Flask, SQLAlchemy and JWT authentication.'),
('Flask',                'Build a Flask Web Application',                     'project',       'Self-directed',               'https://flask.palletsprojects.com/en/latest/tutorial/',                   8,   'Free',           'beginner',      'Follow the official Flask tutorial to build a blog web application.'),

('Go',                   'Learn Go Programming â€" Golang Tutorial',            'course',        'freeCodeCamp / YouTube',      'https://www.youtube.com/watch?v=YS4e4q9oBaU',                            7,   'Free',           'beginner',      'Free 7-hour Go programming tutorial for beginners on YouTube.'),
('Go',                   'Build a REST API with Go',                          'project',       'Self-directed',               'https://go.dev/doc/tutorial/web-service-gin',                             8,   'Free',           'intermediate',  'Build a REST API using Go and the Gin web framework.'),

('Google Analytics',     'Google Analytics Certification (GA4)',              'certification', 'Google',                      'https://skillshop.withgoogle.com/googleanalytics',                        4,   'Free',           'beginner',      'Free official Google Analytics certification covering GA4.'),
('Google Analytics',     'Google Analytics for Beginners',                    'course',        'Google Skillshop',            'https://skillshop.withgoogle.com/',                                       4,   'Free',           'beginner',      'Free official Google Analytics course covering setup, reports and dashboards.'),

('Hadoop',               'Big Data Hadoop and Spark Developer',               'course',        'Udemy',                       'https://www.udemy.com/course/big-data-hadoop-spark-developer/',          14,  'Paid ~$15',      'intermediate',  'Learn Hadoop ecosystem including HDFS, MapReduce, Hive and Spark.'),
('Hadoop',               'Hadoop Administration Fundamentals',                'course',        'Coursera',                    'https://www.coursera.org/learn/hadoop',                                   6,   'Free to audit',  'intermediate',  'Introduction to Hadoop distributed storage and processing.'),

('Identity & Access Management', 'IAM and Security in the Cloud',            'course',        'Coursera / Google Cloud',     'https://www.coursera.org/learn/google-cloud-iam',                         8,   'Free to audit',  'intermediate',  'Learn identity and access management concepts using Google Cloud IAM.'),
('Identity & Access Management', 'AWS IAM Hands-on Lab',                    'project',       'AWS',                         'https://aws.amazon.com/iam/getting-started/',                             5,   'Free tier',      'beginner',      'Set up IAM users, groups, roles and policies in an AWS account.'),

('Java',                 'Java Programming Masterclass for Software Developers', 'course',     'Udemy / Tim Buchalka',        'https://www.udemy.com/course/java-the-complete-java-developer-course/',  80,  'Paid ~$15',      'beginner',      'Comprehensive Java course covering OOP, data structures and multi-threading.'),
('Java',                 'Build a Java Spring Boot REST API',                 'project',       'Self-directed',               'https://spring.io/guides/gs/rest-service/',                               12,  'Free',           'intermediate',  'Build a REST API using Java and Spring Boot following the official guide.'),

('Jupyter',              'Jupyter Notebook for Data Science',                 'course',        'Udemy',                       'https://www.udemy.com/course/jupyter-notebook-for-data-science/',         4,   'Paid ~$15',      'beginner',      'Learn Jupyter Notebook for data science, visualisation and reporting.'),
('Jupyter',              'Build a Data Analysis Notebook',                    'project',       'Self-directed',               'https://jupyter.org/try',                                                  6,   'Free',           'beginner',      'Create a complete data analysis notebook with visualisations using Jupyter and Pandas.'),

('Kali Linux',           'Learn Ethical Hacking from Scratch',                'course',        'Udemy / Zaid Sabih',          'https://www.udemy.com/course/learn-ethical-hacking-from-scratch/',       14,  'Paid ~$15',      'beginner',      'Learn ethical hacking using Kali Linux from beginner to advanced.'),
('Kali Linux',           'TryHackMe â€" Jr Penetration Tester Path',            'course',        'TryHackMe',                   'https://tryhackme.com/path/outline/jrpenetrationtester',                 64,  'Free / $14/mo',  'intermediate',  'Structured penetration testing learning path using Kali Linux tools.'),

('Kotlin',               'Kotlin for Java Developers',                        'course',        'Coursera / JetBrains',        'https://www.coursera.org/learn/kotlin-for-java-developers',              21,  'Free to audit',  'intermediate',  'Learn Kotlin for Android and server-side development from JetBrains.'),
('Kotlin',               'Build an Android App with Kotlin',                  'project',       'Self-directed',               'https://developer.android.com/courses/android-basics-kotlin/course',      20,  'Free',           'beginner',      'Build a basic Android app using Kotlin following Google developer guides.'),

('Log Analysis',         'Security Monitoring and SIEM Fundamentals',         'course',        'Cybrary',                     'https://www.cybrary.it/course/security-monitoring-and-siem/',             6,   'Free',           'beginner',      'Learn log analysis and SIEM fundamentals for security monitoring.'),
('Log Analysis',         'Analyse System Logs with Splunk Free',              'project',       'Self-directed',               'https://www.splunk.com/en_us/download/splunk-enterprise.html',            6,   'Free',           'beginner',      'Use Splunk Free to ingest and analyse system logs from a local machine.'),

('Looker',               'Looker Studio for Beginners',                       'course',        'Google',                      'https://lookerstudio.google.com/u/0/navigation/reporting',                4,   'Free',           'beginner',      'Learn to create interactive dashboards and reports using Google Looker Studio.'),
('Looker',               'Build a Dashboard in Looker Studio',                'project',       'Self-directed',               'https://lookerstudio.google.com/',                                         5,   'Free',           'beginner',      'Build a public data dashboard using Google Looker Studio connected to a free dataset.'),

('Malware Analysis',     'Malware Analysis and Reverse Engineering',           'course',        'Cybrary',                     'https://www.cybrary.it/course/malware-analysis/',                         10,  'Free',           'intermediate',  'Introduction to malware analysis techniques and reverse engineering.'),
('Malware Analysis',     'Analyse a Malware Sample in a Safe Lab',            'project',       'Self-directed',               'https://any.run/',                                                        8,   'Free tier',      'intermediate',  'Analyse a malware sample using ANY.RUN or Cuckoo Sandbox in a safe virtual environment.'),

('Matplotlib',           'Matplotlib Tutorial for Beginners',                 'course',        'freeCodeCamp / YouTube',      'https://www.youtube.com/watch?v=3Xc3CA655Y4',                             4,   'Free',           'beginner',      'Free Matplotlib tutorial covering plotting, subplots and customisation.'),
('Matplotlib',           'Create a Data Story with Matplotlib',               'project',       'Self-directed',               'https://matplotlib.org/stable/gallery/',                                   8,   'Free',           'beginner',      'Create a multi-chart data story using Matplotlib and a real dataset.'),

('Metasploit',           'Metasploit Framework for Penetration Testing',       'course',        'Udemy',                       'https://www.udemy.com/course/metasploit-framework-penetration-testing/',  6,   'Paid ~$15',      'intermediate',  'Learn Metasploit Framework for network and system penetration testing.'),
('Metasploit',           'Complete a Metasploit Lab on TryHackMe',            'project',       'TryHackMe',                   'https://tryhackme.com/module/metasploit',                                 8,   'Free / $14/mo',  'intermediate',  'Complete the TryHackMe Metasploit module with guided practical exercises.'),

('Microservices',        'Microservices with Node.js and React',              'course',        'Udemy / Stephen Grider',      'https://www.udemy.com/course/microservices-with-node-js-and-react/',     54,  'Paid ~$15',      'advanced',      'Build production-grade microservices using Docker, Kubernetes and NATS.'),
('Microservices',        'Design a Microservices Architecture',               'project',       'Self-directed',               'https://microservices.io/patterns/index.html',                            10,  'Free',           'intermediate',  'Design a microservices architecture diagram and implement two communicating services.'),

('Monitoring & Observability', 'Site Reliability Engineering: Measuring and Managing Reliability', 'course', 'Coursera / Google', 'https://www.coursera.org/learn/site-reliability-engineering-slos', 8, 'Free to audit', 'intermediate', 'Learn SRE practices including monitoring, alerting and reliability measurement.'),
('Monitoring & Observability', 'Set Up Prometheus and Grafana',              'project',       'Self-directed',               'https://prometheus.io/docs/visualization/grafana/',                        8,   'Free',           'intermediate',  'Set up Prometheus and Grafana to monitor a local application.'),

('MySQL',                'MySQL Bootcamp: Go from SQL Beginner to Expert',    'course',        'Udemy / Colt Steele',         'https://www.udemy.com/course/the-ultimate-mysql-bootcamp-go-from-sql-beginner-to-expert/', 20, 'Paid ~$15', 'beginner', 'Comprehensive MySQL course from basics to advanced queries and stored procedures.'),
('MySQL',                'Design and Query a MySQL Database',                 'project',       'Self-directed',               'https://dev.mysql.com/doc/refman/8.0/en/tutorial.html',                   8,   'Free',           'beginner',      'Design a normalised database and write complex queries using MySQL.'),

('Nessus',               'Vulnerability Scanning with Nessus Essentials',     'course',        'Tenable',                     'https://www.tenable.com/education/nessus',                                4,   'Free',           'beginner',      'Official Tenable course on vulnerability scanning with Nessus Essentials.'),
('Nessus',               'Perform a Network Vulnerability Scan',              'project',       'Self-directed',               'https://www.tenable.com/products/nessus/nessus-essentials',               6,   'Free',           'beginner',      'Use Nessus Essentials to scan a lab network and produce a vulnerability report.'),

('Networking',           'Computer Networking â€" A Top-Down Approach',         'course',        'Coursera / University of Michigan', 'https://www.coursera.org/learn/computer-networking',               24,  'Free to audit',  'intermediate',  'Comprehensive computer networking course covering protocols and architecture.'),
('Networking',           'CompTIA Network+ Certification (N10-009)',          'certification', 'CompTIA',                     'https://www.comptia.org/certifications/network',                          40,  '$338 USD',       'intermediate',  'Industry-standard networking certification covering LAN, WAN and security.'),

('Nmap',                 'Network Scanning with Nmap',                        'course',        'Udemy',                       'https://www.udemy.com/course/nmap/',                                       3,   'Paid ~$15',      'beginner',      'Learn network discovery and security scanning using Nmap.'),
('Nmap',                 'TryHackMe â€" Nmap Room',                            'project',       'TryHackMe',                   'https://tryhackme.com/room/furthernmap',                                   3,   'Free / $14/mo',  'beginner',      'Complete the TryHackMe Nmap room covering scanning techniques and flags.'),

('NumPy',                'NumPy Tutorial for Beginners',                      'course',        'freeCodeCamp / YouTube',      'https://www.youtube.com/watch?v=QUT1VHiLmmI',                             2,   'Free',           'beginner',      'Free NumPy tutorial covering arrays, operations and linear algebra.'),
('NumPy',                'NumPy Exercises on Kaggle',                         'project',       'Kaggle',                      'https://www.kaggle.com/learn/numpy',                                       4,   'Free',           'beginner',      'Complete NumPy exercises and apply array operations to a dataset.'),

('Object-Oriented Programming', 'Python OOP Tutorial',                        'course',        'Corey Schafer / YouTube',     'https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeqVj', 4, 'Free', 'beginner', 'Free Python OOP tutorial series covering classes, inheritance and encapsulation.'),
('Object-Oriented Programming', 'Refactor a Project Using OOP Principles',   'project',       'Self-directed',               'https://refactoring.guru/design-patterns',                                10,  'Free',           'intermediate',  'Refactor an existing project to use OOP principles and design patterns.'),

('OWASP Top 10',         'OWASP Top 10 Web Application Security Risks',       'course',        'TryHackMe',                   'https://tryhackme.com/room/owasptop10',                                    6,   'Free / $14/mo',  'beginner',      'Hands-on lab covering all 10 OWASP web application security risks.'),
('OWASP Top 10',         'Test a Web App for OWASP Vulnerabilities',          'project',       'PortSwigger',                 'https://portswigger.net/web-security/all-labs',                           10,  'Free',           'intermediate',  'Complete PortSwigger labs covering SQL injection, XSS and other OWASP risks.'),

('PostgreSQL',           'Learn PostgreSQL Tutorial',                          'course',        'freeCodeCamp / YouTube',      'https://www.youtube.com/watch?v=qw--VYLpxG4',                             4,   'Free',           'beginner',      'Free PostgreSQL tutorial covering setup, queries and advanced features.'),
('PostgreSQL',           'Build a PostgreSQL Database for a Project',         'project',       'Self-directed',               'https://www.postgresql.org/docs/current/tutorial.html',                   6,   'Free',           'beginner',      'Design and implement a PostgreSQL database for a personal project.'),

('PowerShell',           'PowerShell Master Class',                            'course',        'YouTube / John Savill',       'https://www.youtube.com/playlist?list=PLlVtbbG169nFq_hR7FcMYg32xsSAObuq8', 8, 'Free', 'beginner', 'Free PowerShell master class covering scripting and automation.'),
('PowerShell',           'Automate Windows Tasks with PowerShell',            'project',       'Self-directed',               'https://learn.microsoft.com/en-us/powershell/scripting/learn/tutorials/01-discover-powershell', 5, 'Free', 'beginner', 'Write PowerShell scripts to automate common Windows administration tasks.'),

('R',                    'R Programming',                                      'course',        'Coursera / Johns Hopkins',    'https://www.coursera.org/learn/r-programming',                            57,  'Free to audit',  'beginner',      'Introduction to R programming for statistical computing and data analysis.'),
('R',                    'Data Analysis with R â€" Kaggle Course',              'course',        'Kaggle',                      'https://www.kaggle.com/learn/r',                                           4,   'Free',           'beginner',      'Free hands-on R course for data analysis and visualisation.'),

('Redis',                'Redis Crash Course',                                 'course',        'freeCodeCamp / YouTube',      'https://www.youtube.com/watch?v=jgpVdJB2sKQ',                             1,   'Free',           'beginner',      'Free Redis crash course covering data structures, caching and pub/sub.'),
('Redis',                'Add Redis Caching to a Web Application',            'project',       'Self-directed',               'https://redis.io/docs/getting-started/',                                   5,   'Free',           'intermediate',  'Add Redis caching to an existing web application to improve performance.'),

('Rust',                 'The Rust Programming Language (The Book)',           'course',        'Rust Foundation',             'https://doc.rust-lang.org/book/',                                         30,  'Free',           'intermediate',  'Official Rust programming language book with comprehensive tutorials.'),
('Rust',                 'Rustlings â€" Small Rust Exercises',                  'project',       'Self-directed',               'https://github.com/rust-lang/rustlings',                                  15,  'Free',           'beginner',      'Complete Rustlings exercises to learn Rust syntax and concepts hands-on.'),

('Seaborn',              'Seaborn Tutorial for Beginners',                    'course',        'freeCodeCamp / YouTube',      'https://www.youtube.com/watch?v=6GUZXDef2U0',                             2,   'Free',           'beginner',      'Free Seaborn tutorial covering statistical visualisations and plot types.'),
('Seaborn',              'Create a Statistical Visualisation Report',         'project',       'Self-directed',               'https://seaborn.pydata.org/tutorial.html',                                 6,   'Free',           'beginner',      'Create a portfolio visualisation report using Seaborn on a real dataset.'),

('Security Frameworks',  'NIST Cybersecurity Framework Fundamentals',         'course',        'NIST',                        'https://www.nist.gov/cyberframework/getting-started',                     4,   'Free',           'beginner',      'Introduction to the NIST Cybersecurity Framework for risk management.'),
('Security Frameworks',  'ISO 27001 Lead Implementer Certification',          'certification', 'PECB',                        'https://pecb.com/en/education-and-training-for-iso-iec-27001',           40,  '$495 USD',       'advanced',      'ISO 27001 information security management system certification.'),

('Security Operations (SOC)', 'TryHackMe SOC Level 1',                       'certification', 'TryHackMe',                   'https://tryhackme.com/path/outline/soclevel1',                            60,  'Free / $14/mo',  'beginner',      'Structured SOC analyst certification path on TryHackMe.'),
('Security Operations (SOC)', 'Build a Home SOC Lab',                        'project',       'Self-directed',               'https://www.elastic.co/security/siem',                                    12,  'Free',           'intermediate',  'Set up a home SOC lab using ELK Stack or Wazuh to monitor and analyse security events.'),

('SIEM',                 'Splunk Core Certified User',                        'certification', 'Splunk',                      'https://www.splunk.com/en_us/training/certification-track/splunk-core-certified-user.html', 8, '$130 USD', 'beginner', 'Entry-level Splunk certification covering search, reports and dashboards.'),
('SIEM',                 'Microsoft Sentinel SIEM Fundamentals',              'course',        'Microsoft Learn',             'https://learn.microsoft.com/en-us/azure/sentinel/overview',              6,   'Free',           'beginner',      'Free Microsoft learning path for Azure Sentinel SIEM.'),

('Snort',                'Intrusion Detection with Snort',                    'course',        'Cybrary',                     'https://www.cybrary.it/course/snort/',                                     4,   'Free',           'intermediate',  'Learn network intrusion detection using Snort.'),
('Snort',                'Set Up Snort IDS in a Lab',                        'project',       'Self-directed',               'https://www.snort.org/documents',                                          6,   'Free',           'intermediate',  'Configure Snort as an intrusion detection system in a virtual lab environment.'),

('Splunk',               'Splunk Fundamentals 1',                             'course',        'Splunk',                      'https://www.splunk.com/en_us/training/free-courses/splunk-fundamentals-1.html', 9, 'Free', 'beginner', 'Official free Splunk course covering search, reports and visualisation.'),
('Splunk',               'Analyse Security Logs with Splunk',                'project',       'Self-directed',               'https://www.splunk.com/en_us/download/splunk-enterprise.html',            6,   'Free',           'beginner',      'Use Splunk Free to analyse security event logs and create a dashboard.'),

('Spring Boot',          'Spring Boot Masterclass',                           'course',        'Udemy',                       'https://www.udemy.com/course/spring-boot-tutorial-for-beginners/',       16,  'Paid ~$15',      'intermediate',  'Learn Spring Boot for building Java REST APIs and microservices.'),
('Spring Boot',          'Build a REST API with Spring Boot',                 'project',       'Self-directed',               'https://spring.io/guides/gs/rest-service/',                               10,  'Free',           'intermediate',  'Follow the official Spring Boot guide to build a REST service.'),

('SQLite',               'SQLite Tutorial',                                    'course',        'SQLiteTutorial.net',          'https://www.sqlitetutorial.net/',                                          4,   'Free',           'beginner',      'Free SQLite tutorial covering CRUD operations, joins and Python integration.'),
('SQLite',               'Build a Python App with SQLite',                   'project',       'Self-directed',               'https://docs.python.org/3/library/sqlite3.html',                           5,   'Free',           'beginner',      'Build a Python command-line application using SQLite as the database.'),

('Swift',                'iOS and Swift â€" The Complete iOS App Development Bootcamp', 'course', 'Udemy / Angela Yu',          'https://www.udemy.com/course/ios-13-app-development-bootcamp/',          55,  'Paid ~$15',      'beginner',      'Complete iOS development course covering Swift and UIKit from scratch.'),
('Swift',                'Build a Swift iOS App',                             'project',       'Self-directed',               'https://developer.apple.com/tutorials/app-dev-training',                  15,  'Free',           'beginner',      'Build a simple iOS app using Swift following Apple developer tutorials.'),

('Terraform',            'HashiCorp Certified: Terraform Associate',          'certification', 'HashiCorp',                   'https://www.hashicorp.com/certification/terraform-associate',             20,  '$70.50 USD',     'intermediate',  'Official HashiCorp Terraform associate certification for infrastructure as code.'),
('Terraform',            'Terraform for Beginners',                           'course',        'Udemy / KodeKloud',           'https://www.udemy.com/course/terraform-beginner-to-advanced/',            8,   'Paid ~$15',      'beginner',      'Learn Terraform from scratch to provision cloud infrastructure.'),

('Threat Intelligence',  'Cyber Threat Intelligence',                          'course',        'Coursera / IBM',              'https://www.coursera.org/learn/ibm-cyber-threat-intelligence',           16,  'Free to audit',  'intermediate',  'IBM course on cyber threat intelligence frameworks, tools and techniques.'),
('Threat Intelligence',  'TryHackMe Cyber Threat Intelligence Path',          'course',        'TryHackMe',                   'https://tryhackme.com/module/cyber-threat-intelligence',                  12,  'Free / $14/mo',  'intermediate',  'Hands-on cyber threat intelligence learning on TryHackMe.'),

('VPN',                  'VPN Fundamentals',                                   'course',        'Cybrary',                     'https://www.cybrary.it/course/vpn-fundamentals/',                          3,   'Free',           'beginner',      'Introduction to VPN technologies, protocols and configuration.'),
('VPN',                  'Set Up a Personal VPN Server',                      'project',       'Self-directed',               'https://www.wireguard.com/quickstart/',                                    4,   'Free',           'intermediate',  'Set up a personal VPN server using WireGuard on a cloud VM.'),

('Windows Server',       'Windows Server Administration Fundamentals',        'certification', 'Microsoft',                   'https://learn.microsoft.com/en-us/certifications/mta-windows-server-administration-fundamentals/', 20, '$127 USD', 'beginner', 'Microsoft Windows Server administration fundamentals certification.'),
('Windows Server',       'Windows Server â€" Free Microsoft Learn Path',        'course',        'Microsoft Learn',             'https://learn.microsoft.com/en-us/training/paths/windows-server-fundamentals-getting-started/', 8, 'Free', 'beginner', 'Free Microsoft learning path for Windows Server fundamentals.')

) AS r(skill_name, resource_title, resource_type, provider, url, duration_hours, cost, difficulty, description)
ON sl.skill_name = r.skill_name
WHERE sl.is_active = TRUE

ON CONFLICT DO NOTHING;

-- â"€â"€ VERIFY â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
SELECT COUNT(*) AS total_resources FROM recommendations_library;

SELECT COUNT(*) AS skills_without_resources
FROM skills_library sl
LEFT JOIN recommendations_library rl ON rl.skill_id = sl.skill_id
WHERE rl.resource_id IS NULL
AND sl.is_active = TRUE;

