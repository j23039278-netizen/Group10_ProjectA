# Role template retune: proposal

**Status:** approved as recommended on 31 October 2026 and applied (section 8). Effect on readiness: `nlp/experiments/results/role_retune_effect.md`.
**Date:** 30 October 2026 · **Author:** Ng Yong Hin (AI / NLP Engineer) · **Task:** retune `database/seed_job_role_skills.sql` against the JD dataset (the TODO in that file)

How to approve: reply with the IDs or sections you accept, for example "all of section 4 except DS-12; P1 yes; P3 keep; new skills N1–N5". Anything not approved stays as it is.

## 1. What was run

- **Data:** `data/jd_dataset/jd_dataset.csv`, 350 JDs, 35 per role. Seniority: 212 entry, 134 junior, 4 mid. Region: 65 Malaysia (manual), 285 LinkedIn Job Postings 2023–2024 (Kaggle, CC BY-SA 4.0).
- **Extraction:** `python data/jd_dataset/analyse_jd_skills.py` now takes `--method {hybrid,keyword,semantic,baseline}`. The default is now `hybrid`, which calls `nlp.extract_skills(method="hybrid")`, the method the website uses for JDs. `baseline` is the old keyword matcher in `jd_common.py`. The script writes a new file, `jd_skill_evidence.csv`, with one row per JD and skill: the matched text and the sentence around it. Every number below can be checked against that file.
- **Hybrid vs baseline:** 3,530 role–skill JD hits against 2,560. Of the 3,530, 639 are semantic only. The biggest gains come from context-resolved ambiguous names (Excel for Financial Analyst: 6 → 20 JDs; R for Data Scientist: 0 → 15) and from semantic phrases ("charts, dashboards" → Data Visualisation for Data Analyst: 4 → 17; "present findings to stakeholders" → Stakeholder Communication for Business Analyst: 0 → 11).
- **Boilerplate filter:** hits inside equal-opportunity, agency, privacy, accommodation or pay/benefits text are not counted ("recruitment agencies", "during the hiring process", "subject to business needs"). For HR Executive, pay and benefits text is counted, because payroll and benefits are HR work.
- **Manual review:** I read every candidate that is semantic-heavy and every add with 6 JDs or fewer. 10 hits were wrong and are not counted, for example "see their data magic **spark** real-world change" (Apache Spark) and "known as an **agile**, innovative" company (Agile / Scrum). Candidates the evidence does not support are listed under "Checked, no change" for each role, with the reason.

`k of 35` below means the number of the role's 35 JDs that ask for the skill after the filter and the review. "(n semantic)" means n of those k JDs were found only by semantic matching.

## 2. Rules

With 35 JDs per role, one JD is 2.9 points, and the 95% interval around 30% is about ±15 points. So a skill needs strong evidence to become required, and clear evidence before it stops being required. Each skill moves at most one level per retune.

| Current level | Change when | To |
|---|---|---|
| required | k ≤ 6 (< 20%) | preferred |
| preferred | k ≥ 18 (≥ 50%) / k ≤ 3 (< 10%) | required / bonus |
| bonus | k ≥ 18 / k ≥ 7 / k ≤ 1 | required / preferred / removed |
| not mapped | k ≥ 18 / k ≥ 7 / 4–6 | required / preferred / bonus (bonus only for technical and professional skills, not generic soft skills) |

Two checks come on top of the rule:
- **Extraction gaps.** If a required skill falls below 7, I searched the JD text for the usual phrasings. Where that search finds 7 or more JDs, the skill stays required. The gap is logged as an alias suggestion (section 5.3). Seven skills stay required this way.
- **Evidence review.** Wrong-sense hits are removed, as described in section 1.

### Policy decisions (please answer each)

- **P1: soft-skill cap for the 6 IT roles. Recommended: yes.** Generic soft skills (Communication, Teamwork, Problem Solving, Critical Thinking, Time Management, Attention to Detail, Self-Motivation, Interpersonal Skills, Leadership, Adaptability, Decision Making, Customer Focus, Creativity) are at most *preferred* in IT templates. In IT JDs they are general attributes. A self-reported soft skill is weak evidence, and `derive_evidence()` rarely finds project evidence for one, so making it required would mostly lower everyone's score without telling students what to learn. Effect: Problem Solving goes from required to preferred for Software Developer (SD-10) and Cybersecurity Analyst (CY-6), and Communication and Teamwork join IT templates as preferred. Business roles have no cap: there, communication is the job (BA-1 makes Communication required for Business Analyst).
  *If P1 = no:* these become or stay required instead: Data Analyst Communication (20) and Problem Solving (18), Cybersecurity Analyst Communication (19), Cloud Engineer Problem Solving (19) and Communication (18), Data Scientist Teamwork (18), and Problem Solving for Software Developer (18) and Cybersecurity Analyst (12).
- **P2: "either-or" cloud and language lists. Recommended: yes.** Cloud Engineer **Azure** is in 18/35 JDs, but 16 of those 18 name it as an alternative to AWS or GCP ("AWS, Azure or GCP"), and AWS is already required. So Azure stays preferred rather than becoming required. Cloud Engineer **Java** (10/35) is always one option in a list ("Python, Java, or Go"), so it goes in as bonus, not preferred.
- **P3: template size. Recommended: accept.** The proposal grows templates from 24.4 to 28.7 skills on average (before any new library skills). The preferred lists of IT roles grow from 8–10 to 13–16, above the "6–10 preferred" band in the seed header. Those bands were set before there was JD data. *Alternative:* keep preferred at 12 or fewer by moving the lowest-k preferred adds of each role to bonus. That is about 12 rows; I would list them before applying.

## 3. Summary

| Role | Add | Promote | Demote | Remove | Now (req/pref/bonus) | Proposed |
|---|---|---|---|---|---|---|
| Data Analyst | 8 | 0 | 1 | 2 | 9/8/7 (24) | 8/14/8 (30) |
| Data Scientist | 10 | 1 | 6 | 1 | 9/9/8 (26) | 6/16/13 (35) |
| Software Developer | 7 | 2 | 4 | 1 | 10/8/7 (25) | 7/13/11 (31) |
| Cybersecurity Analyst | 4 | 1 | 3 | 2 | 10/10/8 (28) | 9/13/8 (30) |
| Cloud Engineer | 9 | 2 | 1 | 1 | 10/9/6 (25) | 10/13/10 (33) |
| Web Developer | 12 | 1 | 1 | 2 | 9/8/7 (24) | 9/15/10 (34) |
| Business Analyst | 4 | 0 | 4 | 1 | 9/8/6 (23) | 10/7/9 (26) |
| Financial Analyst | 3 | 0 | 5 | 2 | 9/8/6 (23) | 8/8/8 (24) |
| HR Executive | 1 | 0 | 2 | 1 | 9/8/6 (23) | 9/7/7 (23) |
| Marketing Executive | 2 | 1 | 6 | 4 | 9/8/6 (23) | 6/11/4 (21) |
| **Total** | **60** | **8** | **33** | **17** | 24.4 skills | 28.7 skills |

What the JDs say, in short:
- **Library-level skills are rarely named.** Data Scientist JDs ask for "machine learning" and "Python", not Pandas (5/35), scikit-learn (4) or feature engineering (1). These move from required to preferred (DS-12, DS-13, DS-15). The Data Scientist template keeps 6 required skills: Python, Statistical Analysis, Machine Learning, Data Analysis, SQL, Model Evaluation.
- **Professional skills are under-weighted.** Documentation is in 7–12 of 35 JDs in every IT role, but only Cloud Engineer maps it, and only as bonus. Teamwork is in 15–18 of 35 for 7 of the 10 roles. Agile / Scrum is in 7 of 35 for Data Analyst and Cloud Engineer, where it is not mapped.
- **Web Developer JDs are full-stack.** Angular (14), CI/CD (12), Java (9), C# (7) and AWS / Azure (7 each) are asked for but not mapped.
- **Marketing Executive JDs are general, not technical.** SEO (4), Google Analytics (3) and Presentation Skills (3) are required now but rarely asked for. Four bonus skills appear in no JD.
- **Removals** are bonus skills found in at most 1 JD (A/B Testing for Data Analyst, Network Security for Cloud Engineer, Figma and GraphQL for Web Developer, and others).

¹ = generic soft skill (policy P1).

## 4. Changes per role

### Data Analyst (`DATA_ANALYST`)

Template now 9 required / 8 preferred / 7 bonus → proposed 8 / 14 / 8.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| DA-1 | Teamwork ¹ | **add** as preferred | 15 (8 semantic) | JD-DA-0003: "...r key operational and financial metrics. Stakeholder **Collaboration** ' partner with cross-functional teams (Operations, Pro..."<br>JD-DA-0017: "...orting deadlines & on time delivery of data. Organized **Team player** Curious & Quick Learner Summary The main function of t..." |
| DA-2 | Documentation | **add** as preferred | 9 (1 semantic) | JD-DA-0006: "...keholders. Assist in maintaining data structures and **documentation**. Reporting & Analysis Support Generate scheduled ope..."<br>JD-DA-0014: "...s for I/S new hires.Will also help create departmental **documentation** for multiple workstation support teams.Will be asked t..." |
| DA-3 | Business Analysis | **add** as bonus <br>*5 keyword hits on "business requirements gathering"; the 3 semantic hits are "business needs" boilerplate* | 8 (3 semantic) | JD-DA-0009: "Responsibilities Assist in business **requirements gathering** to meet the objectives of business intelligence and st..."<br>JD-DA-0023: "...vel expertise in gathering, analyzing, and documenting **business requirements**. If you do not have experience as a Business Analyst o..." |
| DA-4 | Business Process Improvement | **add** as preferred | 8 (1 semantic) | JD-DA-0006: "...in developing and maintaining data standards and SOPs. **Process Improvement** Recommend improvements to data collection and manage..."<br>JD-DA-0011: "...ities, capacity constraints and delivery requirements. **Business Process Improvement** Work closely with Production, PPC, Warehouse, Qualit..." |
| DA-5 | Agile / Scrum | **add** as preferred | 7 | JD-DA-0019: "...see their data magic spark real-world change. Join our **agile** team as a Business Intelligence Specialist and become..."<br>JD-DA-0023: "...nternship program.Experience in Requirement Gathering, **Agile methodology**, writing user stories, and building and planning roadm..." |
| DA-6 | Time Management ¹ | **add** as preferred | 7 (2 semantic) | JD-DA-0005: "...nizational skills and ability to work independently to **meet deadlines** Good communication and interpersonal skills with att..."<br>JD-DA-0006: "...to detail and accuracy. Excellent organizational and **time management** skills. Analytical and problem-solving mindset. Ab..." |
| DA-7 | Azure | **add** as bonus | 5 | JD-DA-0015: "...ty with cloud-based database platforms (e.g., AWS RDS, **Azure** Database). A track record of optimizing databases for..."<br>JD-DA-0020: "...msExperience with the Common Data ModelExperience with **Azure** framework Skills and Abilities:Displays natural curios..." |
| DA-8 | Data Modelling | **add** as bonus | 5 (1 semantic) | JD-DA-0008: "...volumes of data to discover patterns and insights. 3. **Data Modelling**: Develop statistical models to understand and predict..."<br>JD-DA-0010: "...taining Power BI dashboards and reports. Support basic **data modelling**, DAX calculations, and data visualisation. Data Prep..." |
| DA-9 | Pandas | required → **preferred** | 1 | JD-DA-0003: "...with Python for data manipulation using tools such as **pandas** and NumPy. Basic understanding of data analysis, sta..." |
| DA-10 | A/B Testing | **remove** (was bonus) | 0 | none in the 35 JDs |
| DA-11 | Google Analytics | **remove** (was bonus) | 0 | none in the 35 JDs |

Checked, no change:
- **Data Cleaning** stays required: hybrid finds 6/35, but a targeted search finds 7/35 ("data cleansing", "data quality"). E.g. JD-DA-0003: "...he next step. Key responsibilities Data Extraction & **Wrangling** ' write efficient SQL queries across our cloud data wa..."
- **Data Structures & Algorithms** not added (8/35, the rule says preferred): "data structures" = data layouts, "algorithms" = ML algorithms.
- **Leadership** not added (9/35, the rule says preferred): "leadership" is the audience ("present to leadership"), not a skill asked for.
- **Project Management** not added (5/35, the rule says bonus): semantic hits on "multiple projects", "project managers".

### Data Scientist (`DATA_SCIENTIST`)

Template now 9 required / 9 preferred / 8 bonus → proposed 6 / 16 / 13.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| DS-1 | Teamwork ¹ | **add** as preferred | 18 (6 semantic) | JD-DS-0003: "...utions to global customers and strategic partners. Our **team works** closely with world-class organizations and events such..."<br>JD-DS-0007: "...to drive decisions and optimize digital performance. **Collaboration**: Work with cross-functional teams, including IT, Busin..." |
| DS-2 | Tableau | **add** as preferred | 10 | JD-DS-0006: "...tand their analytical needs for dashboard development (**Tableau**). Develop the dashboard (Tableau) according to the e..."<br>JD-DS-0007: "...Python, Java, SQL), and/or data analytics tools (e.g., **Tableau**, Power BI) is a plus. Excellent communication skills..." |
| DS-3 | Stakeholder Communication | **add** as preferred | 9 (9 semantic) | JD-DS-0003: "...dings and present project progress to team members and **stakeholders**. Complete assigned project tasks efficiently under t..."<br>JD-DS-0004: "...bility to present data insights and recommendations to **stakeholders**. Knowledge of forecasting, predictive modelling, or..." |
| DS-4 | Documentation | **add** as preferred | 7 (1 semantic) | JD-DS-0008: "...ed outputs with current manual records Prepare basic **documentation** on the work completed Participate in team meetings a..."<br>JD-DS-0009: "...plications and planning-system capabilities. Prepare **technical documentation**, follow coding standards and collaborate with cross-fu..." |
| DS-5 | ETL | **add** as preferred | 7 | JD-DS-0003: "...mputer Vision and Multimodal RAG technologies. Build **data pipelines**, model evaluation workflows, and proof-of-concept demo..."<br>JD-DS-0009: "...roblems alongside experienced team members, developing **data pipelines**, analytical solutions and digital applications. Key re..." |
| DS-6 | Power BI | **add** as preferred | 7 | JD-DS-0006: "...ernship. Strong knowledge - SQL, R, Python, Tableau, **PowerBI**, Hadoop, C++, C, C#, RStudio, Visual Studio, MS Office..."<br>JD-DS-0007: "...ava, SQL), and/or data analytics tools (e.g., Tableau, **Power BI**) is a plus. Excellent communication skills (verbal a..." |
| DS-7 | Excel | **add** as bonus | 6 | JD-DS-0004: "...ics, or a related field is preferred. Proficiency in **Excel**, SQL, BI tools, and Python (e.g. pandas, scikit-learn)..."<br>JD-DS-0008: "...ursework or personal projects Basic familiarity with **Excel** (formulas, pivot tables) Some awareness of databases..." |
| DS-8 | Business Process Improvement | **add** as bonus | 5 | JD-DS-0004: "...rns, and insights to improve procurement strategies. **Process Improvement** (Added Advantage) Identifies process gaps, proposing..."<br>JD-DS-0008: "...SQL (even from coursework) Interest in automation or **process improvement** Skills Basic programming (Python, R, or VBA) Funda..." |
| DS-9 | Project Management | **add** as bonus | 5 (1 semantic) | JD-DS-0007: "...echnologies, and Digital Transformation initiatives. **Project Management**: Support and manage digital technology projects from c..."<br>JD-DS-0012: "...ojects from start to finish including cross-functional **project management**, data gathering and manipulation, analysis and modelin..." |
| DS-10 | Data Mining | **add** as bonus | 4 | JD-DS-0005: "...ficient in either R, Python, Matlab or other analytics/**data mining** packages. Experience in machine learning, predictive..."<br>JD-DS-0019: "...ated field and other thematic areas. Research includes **data mining**, model building/maintenance, and developing reports to..." |
| DS-11 | R | bonus → **preferred** | 15 | JD-DS-0005: "...hematics, or actuarial science. Proficient in either **R**, Python, Matlab or other analytics/data mining package..."<br>JD-DS-0006: "...availability for internship. Strong knowledge - SQL, **R**, Python, Tableau, PowerBI, Hadoop, C++, C, C#, RStudio..." |
| DS-12 | Pandas | required → **preferred** | 5 | JD-DS-0001: "...arly Must Haves Proficiency in Python for data work (**pandas**, numpy, and at least one ML library such as scikit-lea..."<br>JD-DS-0004: "...Proficiency in Excel, SQL, BI tools, and Python (e.g. **pandas**, scikit-learn). Strong analytical, problem-solving, an..." |
| DS-13 | Scikit-learn | required → **preferred** | 4 | JD-DS-0001: "...rk (pandas, numpy, and at least one ML library such as **scikit-learn**) Working knowledge of SQL Solid grounding in core..."<br>JD-DS-0004: "...ency in Excel, SQL, BI tools, and Python (e.g. pandas, **scikit-learn**). Strong analytical, problem-solving, and structured-t..." |
| DS-14 | Git | preferred → **bonus** | 3 (1 semantic) | JD-DS-0009: "...loud technologies, or exposure to Power BI, Tableau or **Git**, are advantageous"<br>JD-DS-0012: "...id understanding of software engineering practices and **version control** systems.Excellent problem-solving skills and a passion..." |
| DS-15 | Feature Engineering | required → **preferred** | 1 | JD-DS-0020: "...regression, survival analysis, GLM, GBM, neural nets, **feature engineering** and selection, and validation.Experience with comparin..." |
| DS-16 | Jupyter | preferred → **bonus** | 1 | JD-DS-0019: "...earn, TensorFlow, or PyTorch for machine learning, and **Jupyter Notebook** or RStudio for data analysis. Ability to clean, prepro..." |
| DS-17 | NumPy | preferred → **bonus** | 1 | JD-DS-0001: "...t Haves Proficiency in Python for data work (pandas, **numpy**, and at least one ML library such as scikit-learn) W..." |
| DS-18 | Research Skills | **remove** (was bonus) | 1 | JD-DS-0021: "...munication and writing skills with success in previous **academic research** Application Instructions: To apply, include a letter o..." |

Checked, no change:
- **Model Evaluation** stays required: hybrid finds 4/35, but a targeted search finds 7/35 ("evaluating their performance", "model validation"). E.g. JD-DS-0002: "...Assist with data processing, chatbot evaluation, AI **model evaluation**, and building RPA pipelines. Support multiple concur..."
- **AI Literacy** not added (4/35, the rule says bonus): "Artificial Intelligence" as a degree field.
- **Business Analysis** not added (7/35, the rule says preferred): "business requirements" / "subject to business needs" boilerplate.
- **C++** not added (4/35, the rule says bonus): one option in "R, Python, C++" lists.
- **Data Structures & Algorithms** not added (9/35, the rule says preferred): "algorithms" = ML algorithms (covered by Machine Learning).
- **Leadership** not added (8/35, the rule says preferred): "leadership" is the audience ("collaborate with senior leadership").
- **UI/UX Design** not added (5/35, the rule says bonus): "user experience" as a product outcome, not design work.

### Software Developer (`SOFTWARE_DEV`)

Template now 10 required / 8 preferred / 7 bonus → proposed 7 / 13 / 11.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| SD-1 | Documentation | **add** as preferred | 12 (1 semantic) | JD-SD-0001: "...nd software release activities. Prepare and maintain **technical documentation**, including system documentation, technical specificati..."<br>JD-SD-0002: "...resolve issues in existing software. Prepare design **documentation**. Write and maintain technical documentation to descr..." |
| SD-2 | AWS | **add** as bonus | 6 | JD-SD-0013: "...nment-related activities. Gain practical exposure to **AWS**/cloud infrastructure, Docker, CI/CD and system monitor..."<br>JD-SD-0015: "...ityFamiliarity with some of the following technologies:**AWS** services such as Lambda, S3, SQS, SNS, among othersObj..." |
| SD-3 | Requirements Analysis | **add** as bonus | 5 (5 semantic) | JD-SD-0001: "...nior team members. Assist in gathering and analysing **user requirements**, system functionality, and performance feedback. Mon..."<br>JD-SD-0002: "...optimization. Design and update software database. **Analyze user needs and software requirement** to determine feasibility of design within time and cos..." |
| SD-4 | Angular | **add** as bonus | 4 | JD-SD-0010: "...ent development framework and tools: Spring framework, **Angular**, React, Kubernetes, Gradle, Docker, Bootstrap, Ionic,..."<br>JD-SD-0016: "...modern Web frameworks and services such as Bootstrap, **Angular**, ReactJS, RESTful services Understanding of object-ori..." |
| SD-5 | CSS | **add** as bonus | 4 | JD-SD-0002: "...d to apply Proficient in ASP.NET Core MVC C#, HTML5, **CSS**, Razor/React.js, Javascript and MSSQL. Experience wi..."<br>JD-SD-0003: "...ies Assisting Software Engineers to develop in HTML, **CSS**, Javascript, ASP.net & C# Involve in whole Software..." |
| SD-6 | HTML | **add** as bonus | 4 | JD-SD-0002: "...couraged to apply Proficient in ASP.NET Core MVC C#, **HTML5**, CSS, Razor/React.js, Javascript and MSSQL. Experien..."<br>JD-SD-0003: "...ibilities Assisting Software Engineers to develop in **HTML**, CSS, Javascript, ASP.net & C# Involve in whole Soft..." |
| SD-7 | Machine Learning | **add** as bonus | 4 | JD-SD-0008: "...er, VB, Python, Web Programming, Dashboards, SECS/GEM, **Machine Learning**. Familiar with the use of A.I. tools for software de..."<br>JD-SD-0012: "...or similar programming languages. Exposure to AI or **Machine Learning**. Experience with data processing, dataset preparatio..." |
| SD-8 | React | bonus → **preferred** | 8 (1 semantic) | JD-SD-0002: "...nt. Have at least 2 years of working experience with **React** Native or in related fields Fresh Graduates with exc..."<br>JD-SD-0010: "...opment framework and tools: Spring framework, Angular, **React**, Kubernetes, Gradle, Docker, Bootstrap, Ionic, Microse..." |
| SD-9 | C++ | bonus → **preferred** | 7 | JD-SD-0012: "...t. Knowledge of Python, JavaScript / TypeScript, C / **C++**, or similar programming languages. Exposure to AI or..."<br>JD-SD-0017: "...raphical user interfaces and back-end software using C/**C++** and Qt on Linux. Qualifications You meet our minimum q..." |
| SD-10 | Problem Solving ¹ | required → **preferred** <br>*soft-skill cap for IT roles (policy P1)* | 18 (4 semantic) | JD-SD-0006: "...gineering is preferred. Must have strong analytical, **problem-solving**, good communication and stakeholder management skills..."<br>JD-SD-0007: "...e using AI coding tools Strong debugging and logical **problem-solving** skills Able to understand business logic and transla..." |
| SD-11 | Git | required → **preferred** | 4 | JD-SD-0012: "...ontrollers, or firmware development. Experience with **Git** or other version control systems. Interest in roboti..."<br>JD-SD-0013: "...ies and data-related tasks. Follow coding standards, **Git**/version control and software development practices...." |
| SD-12 | CI/CD | preferred → **bonus** | 3 | JD-SD-0009: "...issues Learn and contribute to internal tooling and **CI/CD** pipelines What We're Looking For Currently pursuing..."<br>JD-SD-0013: "...ractical exposure to AWS/cloud infrastructure, Docker, **CI/CD** and system monitoring. Assist with basic deployment,..." |
| SD-13 | Data Structures & Algorithms | required → **preferred** | 2 | JD-SD-0022: "...ry Responsibilities Integrate third party products and **algorithms** and make any code modifications required to insert the..."<br>JD-SD-0025: "...ms and deploying in real-world environmentsFeature and **algorithm** development with an understanding of behavior treesDev..." |
| SD-14 | FastAPI | **remove** (was bonus) | 0 | none in the 35 JDs |

Checked, no change:
- **Object-Oriented Programming** stays required: hybrid finds 5/35, but a targeted search finds 7/35 ("object-oriented" / "OOP"). E.g. JD-SD-0010: "...according to specifications. 2. Software Development: **Object-oriented** design & development. 3. SIT and UAT Support. Troubles..."
- **Unit Testing** stays required: hybrid finds 6/35, but a targeted search finds 19/35 ("designing, developing, testing"; hybrid counts only unit-test aliases). E.g. JD-SD-0001: "...but not limited to: Assist in designing, developing, **testing**, and maintaining software applications and systems und..."
- **Business Analysis** not added (8/35, the rule says preferred): "business requirements" / "business needs" phrasing, not BA as a skill.
- **Project Management** not added (9/35, the rule says preferred): semantic hits on "project meetings", "project team".
- **UI/UX Design** not added (4/35, the rule says bonus): "implement UI/UX flows" (building, not designing).

### Cybersecurity Analyst (`CYBER_ANALYST`)

Template now 10 required / 10 preferred / 8 bonus → proposed 9 / 13 / 8.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| CY-1 | Teamwork ¹ | **add** as preferred | 17 (10 semantic) | JD-CY-0008: "...ments. If you will like to experience how the security **team work** and consistently update your knowledge on all those ne..."<br>JD-CY-0010: "...orld cybersecurity scenarios. Strong communication & **teamwork** skills ' Work effectively with SOC professionals and s..." |
| CY-2 | Documentation | **add** as preferred | 9 | JD-CY-0002: "...yze and respond to alerts; including log retrieval and **documentation**. Conduct an analysis of network traffic and host act..."<br>JD-CY-0003: "...y vulnerabilities Help prepare technical reports and **documentation** Conduct research on vulnerabilities, exploits and cy..." |
| CY-3 | Azure | **add** as preferred | 7 | JD-CY-0011: "...d environments Knowledge of cloud based architectures (**Azure**, AWS) Knowledge of Microsoft Servers, Active Directory..."<br>JD-CY-0014: "...e with cloud infrastructure (i.e. Amazon Web Services, **Microsoft Azure**)Familiarity with STIG requirementsUnderstanding of any..." |
| CY-4 | Malware Analysis | **add** as bonus | 4 (1 semantic) | JD-CY-0002: "...response activities such as host triage and retrieval, **malware analysis**, remote system analysis and remediation efforts. Lea..."<br>JD-CY-0010: "...working & security concepts ' Familiar with firewalls, **malware analysis**, TCP/IP, and operating systems. Eager to learn & gro..." |
| CY-5 | Risk Analysis | bonus → **preferred** | 9 (4 semantic) | JD-CY-0013: "...sess the risk of IT systems documenting them in formal **risk assessments** and supporting artifacts associated with the A&A proce..."<br>JD-CY-0025: "...eer will focus on integrating information security and **risk management** into the system development lifecycles. This position..." |
| CY-6 | Problem Solving ¹ | required → **preferred** <br>*soft-skill cap for IT roles (policy P1)* | 12 (2 semantic) | JD-CY-0005: "...e, and vulnerability scanners. Strong analytical and **problem-solving** skills. Good communication skills for documenting in..."<br>JD-CY-0009: "...ent, software testing, network administration, perform **troubleshooting**, and ensure systems' reliability and security. Additio..." |
| CY-7 | Windows Server | preferred → **bonus** | 3 | JD-CY-0011: "...d Systems Engineer include: 7 years of experience as a **Windows Server** Administrator in cloud environments Knowledge of cloud..."<br>JD-CY-0015: "...eries firewallsFortinet FortiGate IPS devicesMicrosoft **Windows Server**, Active Directory, DNS and DHCP, etc.Microsoft Windows..." |
| CY-8 | Wireshark | preferred → **bonus** | 1 (1 semantic) | JD-CY-0033: "...Cyber role. Knowledge, Skills And Abilities Ability to **investigate and evaluate network traffic**, read and interpret logs and packet capturesGeneral ex..." |
| CY-9 | Cryptography | **remove** (was bonus) | 1 | JD-CY-0023: "...y Scoring System (CVSS), OWASP, etc.Basic knowledge of **cryptography**, including symmetric and asymmetric encryption and sof..." |
| CY-10 | Digital Forensics | **remove** (was bonus) | 1 (1 semantic) | JD-CY-0004: "...nts ' assisting with containment, evidence collection, **forensic analysis**, and reporting. Acquire and triage forensic artifact..." |

Checked, no change:
- **Log Analysis** stays required: hybrid finds 5/35, but a targeted search finds 10/35 ("review logs", "log sources"). E.g. JD-CY-0002: "...s Research, analyze and respond to alerts; including **log** retrieval and documentation. Conduct an analysis of..."
- **Network Security** stays required: hybrid finds 4/35, but a targeted search finds 10/35 ("IDS/IPS", "intrusion detection"). E.g. JD-CY-0002: "...security events of interest from defense systems like **IDS**, endpoint protection and other security-related system..."
- **Stakeholder Communication** not added (4/35, the rule says bonus): 4 JDs, semantic only ("work with stakeholders") - too weak.

### Cloud Engineer (`CLOUD_ENGINEER`)

Template now 10 required / 9 preferred / 6 bonus → proposed 10 / 13 / 10.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| CE-1 | Communication ¹ | **add** as preferred | 18 | JD-CE-0001: "...nd work collaboratively with the technical team Good **communication skills** and attention to detail"<br>JD-CE-0002: "...rive organizational improvement. Requirements Strong **communication** and interpersonal abilities. Effective time manageme..." |
| CE-2 | Java | **add** as bonus <br>*listed as one option among languages ("Python, Java, or Go"); Python already covers scripting* | 10 | JD-CE-0012: "...is a plus.Knowledge and experience in Python, C++, or **JAVA** is a plus.Knowledge and/or certificate around AWS, GCP..."<br>JD-CE-0022: "...basis.Opportunity to work on the following tech stacks:**Java**, Spring/SpringBoot, Microservices, Agile, CI/CD,Tekton..." |
| CE-3 | Critical Thinking ¹ | **add** as preferred | 8 (8 semantic) | JD-CE-0001: "...ng or infrastructure monitoring tools is a plus Good **analytical** and problem-solving skills Willingness to learn, tak..."<br>JD-CE-0003: "...o speak to internal stakeholders and clients. Strong **analytical** and troubleshooting skills, and the discipline to test..." |
| CE-4 | Agile / Scrum | **add** as preferred | 7 | JD-CE-0011: "...formance AnalyzerExperience with PagerDutyKnowledge of **Agile** Development, with experience with tools such as JIRA K..."<br>JD-CE-0014: "...for DOD technical development efforts.Experience with **Agile** workflows, AWS CloudFormation, JIRA (At least Familiar..." |
| CE-5 | JavaScript | **add** as bonus | 6 | JD-CE-0009: "...is an added advantage (PHP Laravel, Node.js, React.ks, **JavaScript**, HTML, CSS, Flutter) Language Skills: A professional..."<br>JD-CE-0016: "...ter Notebooks and GitLab. Preferred: Experience with **Javascript** and Typescript. Understanding of Cyber mission. Un..." |
| CE-6 | Stakeholder Communication | **add** as bonus | 6 (6 semantic) | JD-CE-0008: "...mously as well as collaborate effectively with various **stakeholders** Comfortable working in a fast paced environment Ab..."<br>JD-CE-0011: "...ollaborate effectively with cross-functional teams and **stakeholders**.Creative problem solving with demonstrated pattern of..." |
| CE-7 | Apache Spark | **add** as bonus | 5 | JD-CE-0023: "..., distributed systems performance. Experience in using **Spark**, Object Storage (Dell ECS preferred), and Metadata. Ex..."<br>JD-CE-0024: "...e with data streaming and messaging frameworks (Kafka, **Spark**, etc.)Understanding of dependency injection frameworks..." |
| CE-8 | Splunk | **add** as bonus | 5 | JD-CE-0022: "...D using TektonKnowledge on using monitoring tools like **Splunk**, Dynatrace, Sleuth etcStrong oral and written communic..."<br>JD-CE-0023: "...xperience using DevOps-related tools like GIT, Gitlab, **Splunk**, and Ansible. Knowledge of one or more major Cloud Ser..." |
| CE-9 | REST API | **add** as bonus | 4 | JD-CE-0022: "...java Spring boot development, designing and developing **REST APIs** and front-end development using JavaScript, Next.js, H..."<br>JD-CE-0024: "...(AWS, GCP, Azure, etc.)Experience with micro services/**RESTful API**, relational/NoSQL databases, data modeling and data in..." |
| CE-10 | Documentation | bonus → **preferred** | 8 | JD-CE-0001: "...lerts and documenting incidents Prepare and maintain **technical documentation**, configuration records and troubleshooting guides As..."<br>JD-CE-0002: "...ructure components. Maintain accurate and up-to-date **documentation** of IT systems, configurations, processes and procedure..." |
| CE-11 | SQL | bonus → **preferred** | 8 | JD-CE-0002: "...(RPA) and programming or database technologies such as **SQL** is an advantage"<br>JD-CE-0003: "...ewall concepts. Basic MySQL ' able to read and write **SQL**, run a backup and a restore, and explain what an index..." |
| CE-12 | Serverless | preferred → **bonus** | 2 | JD-CE-0017: "...upport customers with software-related topics, such as **cloud function**, OCPP integration, cyber security discussion, etc.Part..."<br>JD-CE-0032: "...d Qualifications 1+ years of experience in containers, **serverless**, streaming technologies (Kafka, Kinesis, etc.), distri..." |
| CE-13 | Network Security | **remove** (was bonus) | 0 | none in the 35 JDs |

Checked, no change:
- **Azure** stays preferred (18/35, the rule says required): 18/35 but 16 of the 18 JDs list it as an alternative to AWS / GCP; AWS is already required.
- **C++** not added (4/35, the rule says bonus): one option in "Python, Java or C++" lists.
- **MLOps** not added (4/35, the rule says bonus): "deployment pipelines" = CI/CD (already in the template).

### Web Developer (`WEB_DEV`)

Template now 9 required / 8 preferred / 7 bonus → proposed 9 / 15 / 10.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| WD-1 | Angular | **add** as preferred | 14 | JD-WD-0008: "...evelopment (HTML, CSS, JavaScript, and frameworks like **Angular**, React, or Vue) together with hands-on experience in b..."<br>JD-WD-0013: "...using scripting languages such as Java Script, jQuery, **Angular**, React. Experience in code reviews, contribute to team..." |
| WD-2 | CI/CD | **add** as preferred | 12 | JD-WD-0008: "...) databases. Familiarity with version control (Git), **CI/CD** workflows, and basic DevOps practices. Bonus: Experi..."<br>JD-WD-0012: "...avaScript, CSS, SQL, and AWS services. Participates in **CI/CD** delivery and adheres to standards and conventions outl..." |
| WD-3 | Documentation | **add** as preferred | 10 | JD-WD-0001: "...plications. Assist in preparing software and product **documentation**. Perform testing and debugging to identify and resol..."<br>JD-WD-0003: "...eviews, testing, and debugging. Contribute to system **documentation** and knowledge sharing. What you need Minimum of 2 so..." |
| WD-4 | Java | **add** as preferred | 9 | JD-WD-0001: "...nt. Basic knowledge in programming languages such as **Java** and JavaScript Basic knowledge in development framew..."<br>JD-WD-0012: "...ud hosted (AWS) enterprise application. Skills include **Java**, JavaScript, CSS, SQL, and AWS services. Participates..." |
| WD-5 | AWS | **add** as preferred | 7 | JD-WD-0008: "...ience with containerization (Docker), cloud platforms (**AWS**, Azure), or testing frameworks (Jest, xUnit, etc.)...."<br>JD-WD-0012: "...Performs work to maintain and enhance a cloud hosted (**AWS**) enterprise application. Skills include Java, JavaScri..." |
| WD-6 | Azure | **add** as preferred | 7 | JD-WD-0008: "...with containerization (Docker), cloud platforms (AWS, **Azure**), or testing frameworks (Jest, xUnit, etc.). Willing..."<br>JD-WD-0013: "...applications with DevSecOps tools and processes (e.g., **Azure** DevOps, Git, SonarQube) to include experience with Con..." |
| WD-7 | C# | **add** as preferred | 7 | JD-WD-0003: "...and Next.js. Implement backend APIs using .NET Core (**C#**) and Node.js. Work with databases (MS SQL & MySQL) t..."<br>JD-WD-0013: "...ng .Net Framework, .Net Core, J2EE, Spring boot, Java, **C#** or similar modern OO programming language, Web Service..." |
| WD-8 | Cloud Computing | **add** as bonus | 6 (2 semantic) | JD-WD-0008: "...s. Bonus: Experience with containerization (Docker), **cloud platforms** (AWS, Azure), or testing frameworks (Jest, xUnit, etc..."<br>JD-WD-0019: "...on.Deploy, configure, and manage applications on Azure **cloud platform**.Monitor application performance, troubleshoot issues,..." |
| WD-9 | MySQL | **add** as bonus | 6 | JD-WD-0003: "...re, and Node.js while managing databases in MS SQL and **MySQL**. A day in life Develop and maintain front-end compon..."<br>JD-WD-0008: "...APIs. Solid understanding of relational (PostgreSQL, **MySQL**) or NoSQL (MongoDB) databases. Familiarity with vers..." |
| WD-10 | Data Modelling | **add** as bonus | 5 (2 semantic) | JD-WD-0005: "...Participate in ClickHouse database table design and **data modeling** Write and optimize complex SQL queries including agg..."<br>JD-WD-0016: "...ization of work on the platform. Hands-on development, **data modelling**, code quality, static code analysis, unit testing, des..." |
| WD-11 | Spring Boot | **add** as bonus | 5 | JD-WD-0012: "...ganizations. Strong programming skills with Java (8+), **Spring Framework** (Core, Boot, Data), Vert.x, JavaScript, ReactJS, Redux..."<br>JD-WD-0013: "...ack development using .Net Framework, .Net Core, J2EE, **Spring boot**, Java, C# or similar modern OO programming language, W..." |
| WD-12 | Microservices | **add** as bonus | 4 | JD-WD-0013: "...ing developing applications using SOA Design patterns, **Microservices** Containerization using Docker or OpenShift, Databases..."<br>JD-WD-0015: "...SQL DB, Angular, Kafka/EventHub Required Skill : Net/C#**MicroServices**/MVC/Web APIAngularOOPsSql ServerCoding Dot Net FullSta..." |
| WD-13 | Vue.js | bonus → **preferred** | 8 | JD-WD-0001: "...pt Basic knowledge in development frameworks such as **Vue.js** ecosystem and UI styling with Tailwind CSS. Self-Dri..."<br>JD-WD-0002: "...r who explores new tech and challenges Nice to have: **Vue** or React Nice to have: Docker, Linux or cloud hostin..." |
| WD-14 | Express.js | preferred → **bonus** | 0 | none in the 35 JDs |
| WD-15 | Figma | **remove** (was bonus) | 1 | JD-WD-0014: "...e will entail developers designing out components from **Figma** files; support and fix current Live Style Guide (LSG)..." |
| WD-16 | GraphQL | **remove** (was bonus) | 1 | JD-WD-0031: "...ent tools such as Babel, WebPack, NPM.Familiarity with **GraphQL** for API data fetching.Understanding of the Software De..." |

Checked, no change:
- **Project Management** not added (8/35, the rule says preferred): semantic hits on "complex projects", "achieve project goals".

### Business Analyst (`BUSINESS_ANALYST`)

Template now 9 required / 8 preferred / 6 bonus → proposed 10 / 7 / 9.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| BA-1 | Communication ¹ | **add** as required | 24 | JD-BA-0001: "...Excel, PowerPoint, SharePoint, and SQL skillsExcellent **communication**, presentation, and delivery skills requiredAbility to..."<br>JD-BA-0002: "...greeStrong interest in research and analyticsExcellent **communication** and teamwork skills.Ability to learn quickly and adapt..." |
| BA-2 | Teamwork ¹ | **add** as preferred | 15 (9 semantic) | JD-BA-0002: "...rs.Develops an understanding of the problem domain the **team works** on. Additional Qualifications For Consideration Curren..."<br>JD-BA-0007: "...and a passion for innovation.Excellent communication, **collaboration**, and interpersonal skills" |
| BA-3 | Interpersonal Skills ¹ | **add** as preferred | 9 (3 semantic) | JD-BA-0007: "...innovation.Excellent communication, collaboration, and **interpersonal skills**"<br>JD-BA-0009: "...other data analysis tools.Excellent communication and **interpersonal skills**, with the ability to effectively collaborate with team..." |
| BA-4 | Time Management ¹ | **add** as preferred | 7 (1 semantic) | JD-BA-0016: "...ional verbal and written communications skills, proven **organization** and attention to detail are required 3 years of Busine..."<br>JD-BA-0019: "...adership and customer advocacy to influence design and **prioritization** of roadmaps to deliver on both client and business obj..." |
| BA-5 | Data Visualisation | preferred → **bonus** | 3 (3 semantic) | JD-BA-0015: "...lated to current and future operationCreating reports, **charts**, graphs, and presentations to aid in proposing new str..."<br>JD-BA-0022: "...in a team environmentExperience with data analysis and **visualization tools** is a plusBachelor's degree in Business, Information Sy..." |
| BA-6 | Power BI | preferred → **bonus** | 3 | JD-BA-0027: "...role, you will Manage project management data tools in **PowerBi** via importation of data through the MS office suite to..."<br>JD-BA-0028: "...Y The toolset is: Visio Word Excel Jira Outlook **Power BI** The interaction is heavy with the development team, bu..." |
| BA-7 | User Acceptance Testing | preferred → **bonus** | 3 | JD-BA-0004: "...ments per documented user acceptance criteria. Conduct **user acceptance testing** with end users to ensure the implemented solution meet..."<br>JD-BA-0008: "...ness needs are met. Prepare test scenarios for TUT/FIT/**UAT** phases of project and enhancement work; collaborate wi..." |
| BA-8 | Business Process Improvement | preferred → **bonus** | 2 | JD-BA-0027: "...de visibility of supply chain management gaps to drive **process improvements**.Monitor trends of supply chain metrics reporting tools..."<br>JD-BA-0030: "...cycle industry.2+ years of hands-on business analyst, **process improvement**, workflow, or technology experience, preferably in a t..." |
| BA-9 | Financial Analysis | **remove** (was bonus) | 0 | none in the 35 JDs |

Checked, no change:
- **Accounting** not added (4/35, the rule says bonus): domain mentions ("tax, accounting professionals", job category).
- **Risk Analysis** not added (5/35, the rule says bonus): only 2 keyword hits; the rest are "reduce risk" phrases.

### Financial Analyst (`FINANCIAL_ANALYST`)

Template now 9 required / 8 preferred / 6 bonus → proposed 8 / 8 / 8.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| FA-1 | Communication ¹ | **add** as preferred | 14 (1 semantic) | JD-FA-0003: "...and prior experience in financial modeling. Excellent **communication** and organizational skills, strong attention to detail,..."<br>JD-FA-0004: "...nd email Preferred Qualifications CPA Preferred Strong **communication skills** Ability to multi-task and attention to detail Come joi..." |
| FA-2 | Problem Solving ¹ | **add** as preferred | 9 (2 semantic) | JD-FA-0001: "...y to employ mathematical, statistical, analytical, and **problem-solving** skills to identify problems, analyze and compile data,..."<br>JD-FA-0015: "...iness models and new technologies. Strong knowledge of **troubleshooting** skills, techniques, and tools. Excellent interpersonal..." |
| FA-3 | Teamwork ¹ | **add** as preferred | 8 (4 semantic) | JD-FA-0011: "...stics and/or accounting courses.- Self-motivated, good **team player**, dependable, accountable, and desire to learn all abou..."<br>JD-FA-0016: "...ttitude, desire to learn, self-motivated and effective **team player** Technical Skills Advanced Microsoft Excel and modeling..." |
| FA-4 | Critical Thinking ¹ | required → **preferred** | 5 (5 semantic) | JD-FA-0001: "...ies (KSA):Ability to employ mathematical, statistical, **analytical**, and problem-solving skills to identify problems, anal..."<br>JD-FA-0017: "...ctive verbal and written communication skillsResearch, **analytical**, and problem-solving skills Bachelor's degree in a rel..." |
| FA-5 | Power BI | preferred → **bonus** | 3 | JD-FA-0019: "...rship within the Finance team.Technology tools such as **PowerBI**, Tableau, and excel to create self-serve dashboards an..."<br>JD-FA-0032: "...iness intelligence (BI) and reporting tools (Hyperion, **Power BI**, SAP Analytics, etc.) Work with the Operations leaders..." |
| FA-6 | Statistical Analysis | preferred → **bonus** | 3 (1 semantic) | JD-FA-0011: "...mathematics, or similar education. Need to have taken **statistics** and/or accounting courses.- Self-motivated, good team..."<br>JD-FA-0019: "...ally Excel (pivot tables and simple macros)Knowlege of **statistical analysis** tool Power BI would be a plus.Proven experience managi..." |
| FA-7 | Accounting Software | preferred → **bonus** | 1 | JD-FA-0028: "...m Lead or Supervisor.Experience with Uniform Statewide **Accounting System** (USAS) and Automated Budget and Evaluation System of [..." |
| FA-8 | Taxation | preferred → **bonus** | 0 | none in the 35 JDs |
| FA-9 | Auditing | **remove** (was bonus) | 0 | none in the 35 JDs |
| FA-10 | Python | **remove** (was bonus) | 0 | none in the 35 JDs |

Checked, no change:
- **Data Analysis** stays required: hybrid finds 5/35, but a targeted search finds 8/35 ("analyze financial data"). E.g. JD-FA-0007: "...P&L) for financial forecasting, budgeting, and analysis**Analyze financial data** by comparing and analyzing budgets and forecasts with..."
- **Business Analysis** not added (5/35, the rule says bonus): 2 genuine hits; the rest are "business unit" / "business needs".
- **Leadership** not added (7/35, the rule says preferred): "leadership" is the audience ("monthly leadership meeting").

### HR Executive (`HR_EXEC`)

Template now 9 required / 8 preferred / 6 bonus → proposed 9 / 7 / 7.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| HR-1 | Self-Motivation ¹ | **add** as preferred | 10 (2 semantic) | JD-HR-0005: "...manage various projects.Keen attention to detail and a **proactive** approach to administrative and task efficiency.High di..."<br>JD-HR-0007: "...pportunity is for a detail-orientated, personable, and **proactive** HR & Payroll officer to support their 250-person workf..." |
| HR-2 | Training & Development | preferred → **bonus** | 3 (1 semantic) | JD-HR-0005: "...very of impactful learning experiences.Support ongoing **learning and development** programs, ensuring employees have access to resources..."<br>JD-HR-0023: "...g operations, ATS migration, professional development, **L&D**, employee relations, etc.) Must be able to work well u..." |
| HR-3 | Negotiation | preferred → **bonus** | 1 (1 semantic) | JD-HR-0032: "...and competency-based evaluations.Provides guidance and **negotiates** fee agreements with clients; completes appropriate cor..." |
| HR-4 | Power BI | **remove** (was bonus) | 1 | JD-HR-0012: "...y Implementation Experience Any reporting experience (**Power BI**, Tableau, Service Now, etc.) Any Workday Certificatio..." |

Checked, no change:
- **Networking** not added (5/35, the rule says bonus): professional networking (sourcing), not computer networking.
- **Stakeholder Communication** not added (4/35, the rule says bonus): 4 JDs, 3 semantic only - too weak.

### Marketing Executive (`MARKETING_EXEC`)

Template now 9 required / 8 preferred / 6 bonus → proposed 6 / 11 / 4.

| ID | Skill | Change | JDs (k of 35) | Evidence |
|---|---|---|---|---|
| MK-1 | Time Management ¹ | **add** as preferred | 11 (6 semantic) | JD-MK-0009: "...ns. Develops and manages timelines and displays strong **organization** and time management skills to handle multiple projects..."<br>JD-MK-0016: "...ng approach to completion of tasksGood organizational, **prioritization**, and interpersonal skills with the ability to work clo..." |
| MK-2 | Attention to Detail ¹ | **add** as preferred | 10 (1 semantic) | JD-MK-0002: "...independently and manage multiple tasks simultaneously.**Detail-oriented** with excellent organizational skills.Enthusiasm for di..."<br>JD-MK-0018: "...l communication skills.Highly organized with excellent **attention to detail**.Ability to work independently and collaboratively in a..." |
| MK-3 | Teamwork ¹ | bonus → **preferred** | 17 (12 semantic) | JD-MK-0006: "...SuiteMonitor social media platformsResearch potential **collaboration** opportunitiesAssist with the implementation of seasona..."<br>JD-MK-0013: "...work in a very busy, high-pressure, team settingStrong **collaboration** skills - can work well with navigating various stakeho..." |
| MK-4 | Search Engine Optimisation | required → **preferred** | 4 | JD-MK-0002: "...are, and content management systems.Basic knowledge of **SEO** principles and best practices.Familiarity with graphic..."<br>JD-MK-0003: "...rtising platforms, including Google Ads, Bing Ads, etc.**Keyword Research** and identification Experience designing and interpreti..." |
| MK-5 | Google Analytics | required → **preferred** | 3 | JD-MK-0022: "...les, charts)Experience using Analytics programs (e.g., **Google Analytics**, Adobe Analytics).Lead generation and/or B2B digital m..."<br>JD-MK-0027: "...rmance of digital marketing efforts using a variety of **Web analytics** tools (Google Analytics, Webtrends etc.)Acquire insigh..." |
| MK-6 | Presentation Skills | required → **preferred** | 3 (2 semantic) | JD-MK-0021: "...ting / advertising budget Conducting, summarizing, and **presenting** local market research Management of internal communica..."<br>JD-MK-0012: "...lays. Assist in staffing the booth, and to observe our **presentation**, process, customers, and competitors. Analyze the succ..." |
| MK-7 | CRM Software | preferred → **bonus** | 2 | JD-MK-0014: "...gement, field mapping, and work with team to sync with **Salesforce** CRM systems ' form creation and management includes in..."<br>JD-MK-0020: "...n from legacy systems experience a huge plusSalesforce **CRM** and Adobe CDP experience a plus Description Planning a..." |
| MK-8 | Data Analysis | preferred → **bonus** | 2 | JD-MK-0030: "...e Ads/Analytics, Facebook Ads/InsightsBe proficient in **data analysis** tools and extract insights to enhance our social media..."<br>JD-MK-0033: "...s, and strategies. Typical project work is centered on **data analysis**, creative development and overall support of product,..." |
| MK-9 | Excel | preferred → **bonus** | 1 | JD-MK-0022: "...y organized, and detail orientedProven experience with **Excel** to manipulate and analyze data (e.g., vlookup, pivot t..." |
| MK-10 | Data Visualisation | **remove** (was bonus) | 0 | none in the 35 JDs |
| MK-11 | Figma | **remove** (was bonus) | 0 | none in the 35 JDs |
| MK-12 | Looker | **remove** (was bonus) | 0 | none in the 35 JDs |
| MK-13 | Negotiation | **remove** (was bonus) | 0 | none in the 35 JDs |

Checked, no change:
- **Stakeholder Communication** not added (4/35, the rule says bonus): 4 JDs, semantic only - too weak.
## 5. New library skills

`unmatched_terms.csv` (hybrid, spaCy noun chunks) is mostly equal-opportunity boilerplate ("national origin", "veteran status") and generic nouns ("data", "development", "solutions"). I took the skill-like terms from it ("microsoft suite", "powerpoint", "testing", "devops", "organizational", "dashboards", "multiple tasks"…) and counted them in the JD text with a targeted search. The library cannot extract these skills yet, so the counts come from that search, not from `extract_skills()`. For that reason a new skill enters templates at **preferred at most**. After the library is rebuilt, the analysis is re-run with them, and any promotion waits for the next retune.

### 5.1 Proposed new skills

| ID | Skill (category / subcategory) | Aliases (ambiguous in *italics*) | JDs | Evidence | Templates |
|---|---|---|---|---|---|
| N1 | **Microsoft Office** (Technical / Business Software) | MS Office, Microsoft Office Suite, Microsoft 365, Office 365, PowerPoint, Microsoft Word, MS Word, Outlook; *Word*, *Office* | 67 of 350: HR 20, BA 12, DA 11, FA 10, MK 7 | JD-DA-0004: "Proficiency in **Microsoft Office suite** (Word, Excel, PowerPoint)"<br>JD-HR-0001: "proficiency in payroll and HRIS software, **Microsoft Office Suite**, and other databases" | preferred: HR, BA, DA, FA, MK |
| N2 | **Organisational Skills** (Soft / Soft) | Organizational skills, Organisation skills, Organization skills, Highly organised, Highly organized, Well organised, Well organized | 44: MK 14, HR 10, FA 7, BA 4 | JD-MK-0001: "Attention to detail and **organizational skills**"<br>JD-FA-0001: "**Organizational skills** to work with changing priorities and demanding workloads" | preferred: MK, HR, FA |
| N3 | **Software Testing** (Technical / Software Engineering) | Manual testing, Test cases, Test plans, QA testing, Quality assurance testing, Functional testing, Regression testing, Integration testing; *QA*, *Testing* | 43: SD 12, BA 9, WD 7 | JD-WD-0001: "Perform **testing and debugging** to identify and resolve software issues"<br>JD-SD-0001: "Assist in designing, developing, **testing**, and maintaining software applications" | preferred: SD, WD |
| N4 | **DevOps** (Technical / DevOps) | DevOps practices, Development and Operations, DevOps culture | 33: CE 15, WD 8 | JD-CE-0007: "We are looking for an enthusiastic **DevOps** Engineer"<br>JD-WD-0003: "Familiarity with basic **DevOps** practices or CI/CD tools" | preferred: CE, WD |
| N5 | **Employee Onboarding** (Technical / Human Resources) | Onboarding, New hire onboarding, Offboarding, New hire orientation | 13 of 35 HR JDs (other roles use "onboarding" in other senses) | JD-HR-0004: "Schedule **onboarding** for new hires"<br>JD-HR-0030: "**onboarding**, offboarding, contractor management, payroll processing" | preferred: HR |
| N6 | **Graphic Design** (Technical / Design) | Adobe Creative Suite, Adobe Photoshop, Photoshop, Adobe Illustrator, Illustrator, InDesign, Canva | 10 of 35 MK JDs | JD-MK-0002: "Familiarity with **graphic design software (e.g., Adobe Creative Suite)** is a plus" | preferred: MK |
| N7 | **ERP Systems** (Technical / Business Software), *optional* | SAP, Oracle ERP, NetSuite, Microsoft Dynamics, Enterprise resource planning; *ERP* | 8 of 35 FA JDs, DA 4 | JD-FA-0014: "Advanced skills in Excel… **SAP** experience"<br>JD-DA-0006: "Experience with **ERP**, CRM, or business information systems is preferred" | preferred: FA |

New skills need `source = v4`. `data/skills/skills_lib.py` allows only v1–v3, so `VALID_SOURCES` gets "v4" (a one-line change outside `backend/`, `frontend/` and `nlp/`). Course visibility needs no change to Carl's `seed_business_skills.sql`: its rule already gives soft skills to every course, and gives any skill used by a Business role to every course. So N1, N2, N5, N6 and N7 are visible to all courses, and N3 and N4 to CS and ICT.

### 5.2 Alias-only suggestions (no new skill)

| ID | Alias(es) | Add to | JDs | Why |
|---|---|---|---|---|
| A1 | Dashboards, Dashboard development, Dashboard reporting | Data Visualisation | DA 17, DS 14, FA 6 | JDs say "build dashboards". The current aliases are "Dashboard creation" and "Creating interactive dashboards". |
| A2 | Multitasking, Multi-tasking, Managing multiple priorities | Time Management | 41: MK 11, HR 9 | "ability to multi-task", "manage multiple tasks simultaneously" |
| A3 | Relational databases | SQL | 28 (WD 8, CE 7, DA 6) | "Familiar with relational databases (MS SQL, MySQL)" |

### 5.3 Extraction gaps found by the checks (aliases, optional)

These skills stay required (section 4, "Checked, no change"). Better aliases would make the next analysis count them directly.

| ID | Skill | Phrasings missed | Targeted count |
|---|---|---|---|
| G1 | Network Security | IDS/IPS, intrusion detection, intrusion prevention | CY 10 vs 4 |
| G2 | Log Analysis | log review, review logs, log retrieval | CY 10 vs 5 |
| G3 | Model Evaluation | model validation, model performance | DS 7 vs 4 |
| G4 | Data Cleaning | data quality checks, "Extraction & Wrangling" ("Data cleansing" and "Data wrangling" are already aliases) | DA 7 vs 6 |
| G5 | Unit Testing | (covered by N3 Software Testing) | SD 19 vs 6 |
| G6 | Data Structures & Algorithms | make "Algorithms" and "Data structures" ambiguous: 16 of the 17 DA / DS hits mean ML algorithms or data layouts | (precision fix) |

### 5.4 Considered, not proposed

- **Mathematics** (41 JDs), **Economics**: almost always a degree field ("degree in Mathematics, Statistics…").
- **English** (24): a language requirement, not a skill the library tracks.
- **Compliance** (48: HR 13, CY 10): it means employment law in HR JDs and security frameworks in Cybersecurity JDs. Both skills exist, so a combined skill would be ambiguous.
- **Automation** (63, CE 20), **Reporting** (72), **Sales** (34): too generic. Financial Analyst already has Financial Reporting.

Any library change (N, A or G) changes extraction and matching, so it is part of the same `MATCH_RULES_VERSION` bump.

## 6. After approval (steps 2 and 3)

1. `database/seed_job_role_skills.sql`: only the approved rows of the role → skill list, and the header (the TODO goes, and a v4 note with a link to this file is added).
2. If N / A / G items are approved: `data/skills/skills_library.csv` (+ `skills_lib.py` VALID_SOURCES), then `python data/skills/build_skills_seed.py`, which regenerates `database/seed_skills_library_v2.sql` and `nlp/resources/skills_taxonomy.json`. Then `pytest tests/test_skills_library.py`.
3. `python data/generate_synthetic_data.py` (5,000 students, seed 42) regenerates `data/output/`. The generator reads the role lists (required → core, preferred + bonus → secondary). The number of random draws depends on list length, so with the same seed **every synthetic student changes**, not only the skills.
4. `nlp/config.py`: bump `MATCH_RULES_VERSION` (to "2026-10-30b") with a comment, so `start_backend.bat` re-assesses. This is the only `nlp/` edit, as the task asks.
5. Re-run `analyse_jd_skills.py` and the tests.
6. Step 3 writes `nlp/experiments/results/role_retune_effect.md` with two comparisons, each per role (mean readiness, and share of Strong / Developing / Gap skill rows and of students):
   - **Template effect:** the *current* synthetic cohort assessed against the old templates and the new ones. This isolates the retune.
   - **Dashboard view:** the old cohort with old templates vs the *regenerated* cohort with new templates. This is what advisors will see after Carl reloads.
   Both use hybrid matching and the backend weights (required 3, preferred 2, bonus 1; Strong 1, Developing 0.5, Gap 0), offline like `nlp/experiments/evidence_effect.py`. Note: these readiness numbers predate the tiered formula of 5 November 2026 (`docs/JOB_READINESS_SCORE.md`).

## 7. Files changed so far (step 1)

- `data/jd_dataset/analyse_jd_skills.py`: `--method` option (default hybrid), the `semantic_jd_count` column, the new `jd_skill_evidence.csv`, all mentions of a matched term masked before unmatched-term mining, and `<<…>>` context markers (the JDs already contain `[COMPANY]`).
- `data/jd_dataset/README.md`: documents `--method` and the evidence file.
- Regenerated with `--method hybrid`: `data/jd_dataset/jd_skill_frequency.csv`, `role_skill_diff.csv`, `unmatched_terms.csv`, and the new `jd_skill_evidence.csv`.
- This file.

## 8. Applied (31 October 2026)

Approved as recommended: every change in section 4, P1 yes, P2 yes, P3 accept, new skills N1–N6 and aliases A1–A3. Not applied, because they were marked optional: N7 (ERP Systems) and the extraction-gap aliases G1–G6.

- `database/seed_job_role_skills.sql`: the 118 changes of section 4 plus the N1–N6 rows (14 rows, all preferred). 301 rows, 30.1 skills per role (6–10 required, 8–17 preferred, 4–13 bonus). The header TODO is replaced by a v4 note.
- `data/skills/skills_library.csv`: N1–N6 with `source = v4` (172 skills), A1–A3. One change from section 5.1: "Outlook" is an *ambiguous* alias of Microsoft Office, because Financial Analyst JDs use "outlook" for forecasts ("market outlook"); "Microsoft Outlook" is a plain alias. `data/skills/skills_lib.py` accepts `v4`. `database/seed_skills_library_v2.sql` and `nlp/resources/skills_taxonomy.json` are regenerated.
- `data/output/`: regenerated, 5,000 students, seed 42. `SYNTHETIC_DATA_VERSION` = `2026-10-31-role-retune`, so `start_backend.bat` replaces the synthetic students.
- `nlp/config.py`: `MATCH_RULES_VERSION` = `2026-10-31` (today's date rather than the "2026-10-30b" of section 6).
- `data/jd_dataset/*.csv`: re-run against the retuned seed. `role_skill_diff.csv` falls from 294 to 213 rows. It uses the plain 50 / 20 / 10% cut-offs, without the hysteresis and policies above, so it is not expected to reach zero.
- `tests/test_backend_api.py`: two tests read the Business template sizes from the seed file instead of the fixed 23.

New skills and Business-role soft skills fall under the existing course-visibility rule in `seed_business_skills.sql`, so that file needs no change. The six v4 skills had no learning resource at first. Section 4 of `database/seed_recommendations_library_final.sql` (2026-11-01) adds 13: two or three per skill, links checked, none repeated from a related skill. A guard stops the seed if a v4 skill has none, and `test_every_seed_skill_has_a_learning_resource` checks every seed skill.
