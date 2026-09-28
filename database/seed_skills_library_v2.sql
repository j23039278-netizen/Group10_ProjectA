-- ============================================================
-- SEAGAS — Skills Library Expansion (v2)
-- Expands from 32 to 130 skills covering all 6 IT job roles
-- Run this AFTER schema.sql (safe to run multiple times)
-- Author: Ng Yong Hin (AI/NLP Engineer)
-- ============================================================

INSERT INTO skills_library (skill_name, category, aliases, description) VALUES

-- ── TECHNICAL: Programming Languages ─────────────────────────
('C#',               'Technical', ARRAY['CSharp','C Sharp','.NET C#'],                  'Microsoft language for enterprise and game development.'),
('Go',               'Technical', ARRAY['Golang','Go language'],                         'Fast compiled language for cloud and backend systems.'),
('Rust',             'Technical', ARRAY['Rust lang'],                                    'Systems language focused on safety and performance.'),
('PHP',              'Technical', ARRAY['PHP 8','Laravel PHP'],                          'Server-side scripting language for web development.'),
('Swift',            'Technical', ARRAY['Swift iOS','Apple Swift'],                      'Apple language for iOS and macOS development.'),
('Kotlin',           'Technical', ARRAY['Kotlin Android'],                               'Modern JVM language for Android development.'),
('Bash',             'Technical', ARRAY['Shell scripting','Bash scripting','Shell'],     'Unix shell scripting for automation.'),
('PowerShell',       'Technical', ARRAY['PS scripting','Windows scripting'],             'Windows automation and task scripting.'),

-- ── TECHNICAL: Web Frameworks ────────────────────────────────
('Vue.js',           'Technical', ARRAY['Vue','VueJS'],                                  'Progressive JavaScript framework for UIs.'),
('Angular',          'Technical', ARRAY['AngularJS','Angular 2+'],                       'Google TypeScript-based web framework.'),
('Django',           'Technical', ARRAY['Django Python','Django REST'],                  'Full-featured Python web framework.'),
('Spring Boot',      'Technical', ARRAY['Spring','Spring Framework','SpringBoot'],       'Java framework for enterprise applications.'),

-- ── TECHNICAL: Databases ─────────────────────────────────────
('MongoDB',          'Technical', ARRAY['Mongo','MongoDB Atlas'],                        'NoSQL document database.'),
('Redis',            'Technical', ARRAY['Redis cache'],                                   'In-memory data structure store for caching.'),
('MySQL',            'Technical', ARRAY['MySQL DB'],                                     'Popular open-source relational database.'),
('SQLite',           'Technical', ARRAY['SQLite DB'],                                    'Lightweight embedded relational database.'),

-- ── TECHNICAL: DevOps & Tools ────────────────────────────────
('Kubernetes',       'Technical', ARRAY['K8s','K8','Kube'],                              'Container orchestration platform.'),
('CI/CD',            'Technical', ARRAY['Continuous Integration','GitHub Actions','Jenkins','CircleCI'], 'Automated build, test and deployment pipelines.'),
('Terraform',        'Technical', ARRAY['Infrastructure as Code','IaC','Terraform HCL'], 'Infrastructure-as-code tool for cloud provisioning.'),
('Ansible',          'Technical', ARRAY['Ansible automation'],                            'IT automation and configuration management tool.'),

-- ── TECHNICAL: Data & BI Tools ───────────────────────────────
('Pandas',           'Technical', ARRAY['Python Pandas','pd'],                           'Python library for data manipulation.'),
('NumPy',            'Technical', ARRAY['Numpy','Python NumPy','np'],                    'Python library for numerical computing.'),
('Matplotlib',       'Technical', ARRAY['Matplotlib Python','pyplot'],                   'Python plotting library.'),
('Seaborn',          'Technical', ARRAY['Seaborn Python'],                               'Statistical data visualisation library.'),
('Apache Spark',     'Technical', ARRAY['Spark','PySpark','Spark SQL'],                  'Large-scale data processing engine.'),
('Hadoop',           'Technical', ARRAY['Apache Hadoop','HDFS','MapReduce'],             'Distributed storage and processing framework.'),

-- ── TECHNICAL: Cybersecurity Tools ───────────────────────────
('Wireshark',        'Technical', ARRAY['Packet analysis','Wireshark tool'],             'Network protocol analyser for traffic inspection.'),
('Nmap',             'Technical', ARRAY['Network mapper','nmap scan'],                   'Network scanning and discovery tool.'),
('Metasploit',       'Technical', ARRAY['MSF','Metasploit Framework'],                   'Penetration testing framework.'),
('Burp Suite',       'Technical', ARRAY['BurpSuite','Burp'],                             'Web application security testing tool.'),
('Splunk',           'Technical', ARRAY['Splunk SIEM'],                                  'Security information and event management platform.'),
('SIEM',             'Technical', ARRAY['Security Information Event Management','QRadar','ArcSight'], 'Security monitoring and log analysis.'),
('Nessus',           'Technical', ARRAY['Nessus scanner','Tenable'],                     'Vulnerability scanning tool.'),
('Kali Linux',       'Technical', ARRAY['Kali','Kali OS'],                               'Linux distribution for penetration testing.'),
('Snort',            'Technical', ARRAY['Snort IDS'],                                    'Open-source intrusion detection system.'),
('Firewall Management', 'Technical', ARRAY['Firewall config','Network firewall','pfSense'], 'Configuring and managing network firewalls.'),
('VPN',              'Technical', ARRAY['Virtual Private Network','OpenVPN','VPN setup'], 'Secure encrypted network tunnelling.'),

-- ── AI_DIGITAL ───────────────────────────────────────────────
('GCP',              'AI_Digital', ARRAY['Google Cloud','Google Cloud Platform','BigQuery'], 'Google cloud computing platform.'),
('MLOps',            'AI_Digital', ARRAY['ML Operations','Model deployment','ML pipeline'],  'Deploying and managing ML models in production.'),
('Generative AI',    'AI_Digital', ARRAY['GenAI','LLM','Large Language Models','GPT'],       'AI systems that generate text, images or code.'),
('Feature Engineering','AI_Digital', ARRAY['Feature selection','Feature extraction'],         'Creating and selecting input features for ML models.'),
('Model Evaluation', 'AI_Digital', ARRAY['Model assessment','Precision recall F1','ROC AUC'], 'Measuring and comparing ML model performance.'),
('TensorFlow',       'AI_Digital', ARRAY['TF','TensorFlow Keras'],                            'Open-source ML framework by Google.'),
('PyTorch',          'AI_Digital', ARRAY['Torch','PyTorch ML'],                               'Open-source ML framework by Meta.'),
('Scikit-learn',     'AI_Digital', ARRAY['sklearn','scikit learn'],                           'Python ML library for classical algorithms.'),
('Hugging Face',     'AI_Digital', ARRAY['HuggingFace','Transformers library'],               'Platform and library for NLP transformer models.'),
('Cybersecurity',    'AI_Digital', ARRAY['Information security','InfoSec','Cyber defence'],   'Protecting systems and networks from digital attacks.'),
('Network Security', 'AI_Digital', ARRAY['Network defence','Network protection'],             'Securing computer networks from threats.'),
('Cryptography',     'AI_Digital', ARRAY['Encryption','Decryption','Crypto','PKI'],           'Techniques for securing information through encoding.'),
('Ethical Hacking',  'AI_Digital', ARRAY['Penetration testing','Pen testing','White hat'],    'Authorised testing of systems for vulnerabilities.'),
('Digital Forensics','AI_Digital', ARRAY['Cyber forensics','Incident response forensics'],    'Investigating digital evidence from cyber incidents.'),
('Incident Response','AI_Digital', ARRAY['IR','Cyber incident response','CSIRT'],             'Responding to and managing cybersecurity incidents.'),
('Vulnerability Assessment','AI_Digital', ARRAY['VA','Vulnerability scanning'],               'Identifying and evaluating security weaknesses.'),
('Computer Vision',  'AI_Digital', ARRAY['CV','Image recognition','Object detection'],        'AI for interpreting visual data.'),

-- ── ANALYTICAL ───────────────────────────────────────────────
('Critical Thinking',    'Analytical', ARRAY['Logical reasoning','Analytical thinking','Deductive reasoning'], 'Objective analysis and evaluation of issues.'),
('Business Analysis',    'Analytical', ARRAY['BA','Requirements gathering','Business requirements'],            'Analysing business processes and requirements.'),
('Requirements Analysis','Analytical', ARRAY['Requirements engineering','System requirements'],                 'Gathering and documenting system requirements.'),
('Risk Analysis',        'Analytical', ARRAY['Risk assessment','Risk management','Threat analysis'],            'Identifying and evaluating potential risks.'),
('Data Modelling',       'Analytical', ARRAY['ER diagram','Database modelling','Schema design'],                'Designing data structures and relationships.'),
('Systems Thinking',     'Analytical', ARRAY['Systems analysis','Holistic thinking'],                          'Understanding how components interact in a system.'),
('A/B Testing',          'Analytical', ARRAY['Split testing','Hypothesis testing','Experimentation'],           'Comparing two versions to determine which performs better.'),
('Financial Analysis',   'Analytical', ARRAY['Financial modelling','Budgeting','Cost analysis'],                'Evaluating financial data to support decisions.'),

-- ── SOFT ─────────────────────────────────────────────────────
('Adaptability',         'Soft', ARRAY['Flexibility','Agility','Resilience','Adaptable'],                      'Adjusting to new conditions and challenges.'),
('Presentation Skills',  'Soft', ARRAY['Public speaking','Presenting','Slide presentation'],                   'Delivering clear and engaging presentations.'),
('Project Management',   'Soft', ARRAY['PM','Agile','Scrum','Kanban','Sprint planning'],                       'Planning and executing projects on time.'),
('Attention to Detail',  'Soft', ARRAY['Detail-oriented','Accuracy','Thoroughness'],                           'Carefully checking work for accuracy.'),
('Self-Motivation',      'Soft', ARRAY['Self-driven','Initiative','Proactive'],                                 'Taking initiative without external prompting.'),
('Interpersonal Skills', 'Soft', ARRAY['People skills','Relationship building','Stakeholder management'],      'Building and maintaining professional relationships.'),
('Documentation',        'Soft', ARRAY['Technical writing','Report writing','Technical documentation'],        'Creating clear written records and guides.')

ON CONFLICT (skill_name) DO NOTHING;

-- ── VERIFY ───────────────────────────────────────────────────
SELECT category, COUNT(*) AS skill_count
FROM skills_library
WHERE is_active = TRUE
GROUP BY category
ORDER BY category;
