"""
SEAGAS — Synthetic Student Profile Generator
Author: Ng Yong Hin (AI / NLP Engineer)

Generates anonymised, synthetic student profiles that match database/schema.sql:
    users, student_profiles, student_skills, student_projects, student_certifications

Outputs (in data/output/):
    users.csv, student_profiles.csv, student_skills.csv,
    student_projects.csv, student_certifications.csv
    seed_synthetic_students.sql   -> load with psql (see README_synthetic.md)
    students_meta.csv             -> generation ground truth (NOT loaded into DB)
    summary_stats.txt             -> distribution statistics for the report

Usage:
    pip install faker bcrypt
    python generate_synthetic_data.py                 # 500 students, seed 42
    python generate_synthetic_data.py --n 300 --seed 7

Design notes (for the Dataset section of the report):
  * Every student has a target role (one of the 6 job_roles) and an "archetype"
    (strong / average / weak) that controls how many role-relevant skills they
    have. This gives a realistic spread of readiness scores instead of every
    student scoring the same.
  * Skills are sampled per role: core skills are likely, secondary skills less
    likely, plus a few random off-role skills (noise).
  * Proficiency depends on year of study and archetype.
  * Evidence (project / certification / internship / coursework) is derived from
    the student's actual generated projects, certifications and internships,
    so the profile is internally consistent.
  * Counts in student_profiles (project_count, etc.) equal the rows generated in
    the detail tables.
  * All emails use the reserved example domain @synthetic.example.com so synthetic data
    can be identified and removed with one DELETE.
  * No real personal data is used. Fixed random seed => reproducible dataset.
"""

import argparse
import csv
import os
import random
import re
import uuid
from collections import Counter
from datetime import date, datetime, timedelta

from faker import Faker

try:
    import bcrypt
except ImportError:  # bcrypt is already in backend/requirements.txt
    bcrypt = None

# ── Config ────────────────────────────────────────────────────────────────
DEFAULT_N = 5000
DEFAULT_SEED = 42
DEMO_PASSWORD = "Seagas@2026"          # same password for every synthetic account
EMAIL_DOMAIN = "synthetic.example.com"
UNIVERSITY = "Swinburne University of Technology (INTI International College Subang)"
CURRENT_YEAR = 2026

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
SCHEMA_PATH = os.path.join(HERE, "..", "database", "schema.sql")

# ── Reference data ─────────────────────────────────────────────────────────
# Skill names MUST exactly match skills_library.skill_name in schema.sql.
# When the skills library is expanded to 100–150 skills, add them here too.

ROLES = {
    "Data Analyst": {
        "core": ["Python", "SQL", "Excel", "Power BI", "Data Analysis",
                 "Data Visualisation", "Statistical Analysis"],
        "secondary": ["Tableau", "R", "Communication", "Problem Solving",
                      "Machine Learning", "Git"],
        "programmes": ["Bachelor of Computer Science (Data Science)",
                       "Bachelor of Information Technology (Business Analytics)",
                       "Bachelor of Computer Science (Artificial Intelligence)"],
        "interests": ["Data Analytics", "Business Intelligence", "Data Science"],
    },
    "Data Scientist": {
        "core": ["Python", "Machine Learning", "Statistical Analysis", "SQL",
                 "Data Analysis", "Deep Learning"],
        "secondary": ["R", "Natural Language Processing", "Data Visualisation",
                      "Git", "Research Skills", "Cloud Computing", "AI Literacy"],
        "programmes": ["Bachelor of Computer Science (Data Science)",
                       "Bachelor of Computer Science (Artificial Intelligence)"],
        "interests": ["Data Science", "Machine Learning", "Artificial Intelligence"],
    },
    "Software Developer": {
        "core": ["Java", "Python", "Git", "SQL", "Problem Solving", "JavaScript"],
        "secondary": ["C++", "Docker", "Linux", "Teamwork", "FastAPI", "Flask",
                      "Node.js", "React"],
        "programmes": ["Bachelor of Computer Science (Software Development)",
                       "Bachelor of Software Engineering",
                       "Bachelor of Information Technology"],
        "interests": ["Software Engineering", "Backend Development", "Mobile Development"],
    },
    "Cybersecurity Analyst": {
        "core": ["Linux", "Problem Solving", "Python", "Cloud Computing"],
        "secondary": ["SQL", "AWS", "Azure", "Git", "Communication", "Research Skills",
                      "Docker", "C++"],
        "programmes": ["Bachelor of Computer Science (Cybersecurity)",
                       "Bachelor of Information Technology (Network Security)"],
        "interests": ["Cybersecurity", "Network Security", "Digital Forensics"],
    },
    "Cloud Engineer": {
        "core": ["Cloud Computing", "AWS", "Linux", "Docker", "Git"],
        "secondary": ["Azure", "Python", "SQL", "Node.js", "Problem Solving",
                      "Teamwork"],
        "programmes": ["Bachelor of Computer Science (Cloud Computing)",
                       "Bachelor of Information Technology (Network Security)",
                       "Bachelor of Information Technology"],
        "interests": ["Cloud Computing", "DevOps", "Infrastructure"],
    },
    "Web Developer": {
        "core": ["JavaScript", "React", "Node.js", "Git", "SQL"],
        "secondary": ["Python", "Flask", "FastAPI", "Docker", "Teamwork",
                      "Communication", "Data Visualisation"],
        "programmes": ["Bachelor of Computer Science (Software Development)",
                       "Bachelor of Information Technology",
                       "Bachelor of Software Engineering"],
        "interests": ["Web Development", "Frontend Development", "UI/UX"],
    },
}

# Rough share of students aiming at each role (sums to 1.0)
ROLE_WEIGHTS = {
    "Software Developer": 0.24, "Data Analyst": 0.20, "Web Developer": 0.18,
    "Data Scientist": 0.13, "Cybersecurity Analyst": 0.13, "Cloud Engineer": 0.12,
}

SOFT_SKILLS = ["Communication", "Teamwork", "Time Management", "Leadership",
               "Problem Solving"]

# archetype -> (share, P(core), P(secondary), gpa_mean)
ARCHETYPES = {
    "strong":  (0.25, 0.75, 0.40, 3.45),
    "average": (0.50, 0.45, 0.20, 3.00),
    "weak":    (0.25, 0.18, 0.08, 2.55),
}

# cert name, issuer, skills it evidences, credential URL
CERTIFICATIONS = [
    ("AWS Certified Cloud Practitioner", "Amazon Web Services", ["AWS", "Cloud Computing"],
     "https://aws.amazon.com/certification/certified-cloud-practitioner/"),
    ("Microsoft Certified: Azure Fundamentals (AZ-900)", "Microsoft", ["Azure", "Cloud Computing"],
     "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/"),
    ("Microsoft Certified: Power BI Data Analyst Associate (PL-300)", "Microsoft",
     ["Power BI", "Data Visualisation"],
     "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/"),
    ("Google Data Analytics Professional Certificate", "Google / Coursera",
     ["Data Analysis", "SQL", "Tableau", "R"],
     "https://www.coursera.org/professional-certificates/google-data-analytics"),
    ("Machine Learning Specialization", "DeepLearning.AI / Coursera",
     ["Machine Learning", "Python"],
     "https://www.coursera.org/specializations/machine-learning-introduction"),
    ("Deep Learning Specialization", "DeepLearning.AI / Coursera", ["Deep Learning"],
     "https://www.coursera.org/specializations/deep-learning"),
    ("Oracle Certified Associate, Java SE Programmer", "Oracle", ["Java"],
     "https://education.oracle.com/"),
    ("PCEP – Certified Entry-Level Python Programmer", "Python Institute", ["Python"],
     "https://pythoninstitute.org/pcep"),
    ("CompTIA Security+", "CompTIA", ["Linux", "Problem Solving"],
     "https://www.comptia.org/certifications/security"),
    ("Cisco Certified Network Associate (CCNA)", "Cisco", ["Linux"],
     "https://www.cisco.com/site/us/en/learn/training-certifications/certifications/enterprise/ccna/index.html"),
    ("Docker Certified Associate", "Docker / Mirantis", ["Docker"],
     "https://training.mirantis.com/"),
    ("Meta Front-End Developer Professional Certificate", "Meta / Coursera",
     ["JavaScript", "React"],
     "https://www.coursera.org/professional-certificates/meta-front-end-developer"),
    ("Microsoft Office Specialist: Excel Associate", "Microsoft", ["Excel"],
     "https://learn.microsoft.com/en-us/credentials/"),
    ("Tableau Desktop Specialist", "Tableau / Salesforce", ["Tableau", "Data Visualisation"],
     "https://www.tableau.com/learn/certification"),
    ("Elements of AI", "University of Helsinki", ["AI Literacy"],
     "https://www.elementsofai.com/"),
]

# project templates per role: (title template, description, skills used)
PROJECTS = {
    "Data Analyst": [
        ("{c} Sales Dashboard", "Built an interactive dashboard to track monthly sales KPIs.",
         ["Power BI", "Excel", "Data Visualisation"]),
        ("Customer Churn Analysis", "Cleaned and analysed telco customer data to identify churn drivers.",
         ["Python", "Data Analysis", "Statistical Analysis"]),
        ("Covid-19 Malaysia Data Explorer", "Exploratory analysis of public MOH datasets with SQL and charts.",
         ["SQL", "Python", "Data Visualisation"]),
        ("Retail Inventory Report Automation", "Automated weekly inventory reporting from a SQL database.",
         ["SQL", "Excel"]),
    ],
    "Data Scientist": [
        ("House Price Prediction", "Trained regression models to predict Klang Valley property prices.",
         ["Python", "Machine Learning", "Statistical Analysis"]),
        ("Sentiment Analysis of Product Reviews", "Classified Shopee product reviews using NLP techniques.",
         ["Python", "Natural Language Processing", "Machine Learning"]),
        ("Plant Disease Image Classifier", "CNN model to detect leaf diseases from photos.",
         ["Deep Learning", "Python"]),
        ("Student Performance Predictor", "Predicted at-risk students from academic records.",
         ["Machine Learning", "Data Analysis", "R"]),
    ],
    "Software Developer": [
        ("Library Management System", "Desktop system for book loans and returns with a relational database.",
         ["Java", "SQL"]),
        ("Campus Event Booking API", "REST API for booking campus events with authentication.",
         ["Python", "FastAPI", "SQL", "Git"]),
        ("Inventory Tracker CLI", "Command-line tool for small-business stock tracking.",
         ["C++", "Git"]),
        ("Food Delivery Backend", "Microservice backend for order handling, containerised with Docker.",
         ["Node.js", "Docker", "SQL"]),
    ],
    "Cybersecurity Analyst": [
        ("Home Network Vulnerability Scan", "Scanned and hardened a home lab network; documented findings.",
         ["Linux", "Research Skills"]),
        ("Phishing Email Detector", "Rule-based and ML approach to flag phishing emails.",
         ["Python", "Machine Learning"]),
        ("Secure Login Module", "Implemented hashing, rate limiting and MFA for a web login.",
         ["Python", "Flask", "SQL"]),
        ("CTF Team Participation", "Solved web and forensics challenges in a university CTF.",
         ["Linux", "Problem Solving", "Teamwork"]),
    ],
    "Cloud Engineer": [
        ("Serverless Image Resizer", "Built an event-driven image pipeline on AWS Lambda and S3.",
         ["AWS", "Cloud Computing", "Python"]),
        ("CI/CD Pipeline for Web App", "Automated build, test and deploy with GitHub Actions and Docker.",
         ["Docker", "Git", "Linux"]),
        ("Azure-hosted Student Portal", "Deployed a web portal to Azure App Service with a managed database.",
         ["Azure", "Cloud Computing", "SQL"]),
        ("Linux Server Monitoring Scripts", "Bash scripts to monitor CPU, memory and disk usage.",
         ["Linux"]),
    ],
    "Web Developer": [
        ("Personal Portfolio Website", "Responsive portfolio site built with React.",
         ["React", "JavaScript"]),
        ("E-commerce Store", "Full-stack store with cart, checkout and admin dashboard.",
         ["React", "Node.js", "SQL"]),
        ("Club Management Web App", "Web app for a student club to manage members and events.",
         ["JavaScript", "Flask", "SQL", "Teamwork"]),
        ("Weather Dashboard", "Front-end app consuming a public weather API with charts.",
         ["JavaScript", "Data Visualisation"]),
    ],
}

PROJECT_TYPES = ["academic", "academic", "academic", "personal", "competition"]

# Romanised Malaysian names (Faker has no Malaysian locale)
CHINESE_SURNAMES = ["Tan", "Lim", "Lee", "Ng", "Wong", "Chan", "Ong", "Teh", "Goh", "Chong",
                    "Yap", "Low", "Koh", "Soh", "Tee", "Chin", "Liew", "Yeoh", "Khoo", "Foo"]
CHINESE_GIVEN = ["Wei Jie", "Jia Hui", "Zi Xuan", "Kai Wen", "Yi Ting", "Jun Hao", "Mei Ling",
                 "Chee Keong", "Xin Yi", "Wen Hao", "Hui Min", "Yong Sheng", "Pei Shan",
                 "Zhi Hao", "Shu Ting", "Ming Jun", "Li Ying", "Jing Wen", "Kok Leong", "En Qi"]
MALAY_MALE = ["Muhammad Aiman", "Ahmad Danial", "Muhammad Hafiz", "Amirul Hakim", "Faris Iskandar",
              "Adam Haikal", "Irfan Zikri", "Syafiq Rahman", "Luqman Hakim", "Arif Imran"]
MALAY_FEMALE = ["Nur Aisyah", "Siti Nurhaliza", "Nurul Izzah", "Aina Sofea", "Farah Nabila",
                "Alya Maisarah", "Nur Iman", "Balqis Humaira", "Hannah Zulaikha", "Syazwani Ain"]
MALAY_FATHER = ["Ahmad", "Ismail", "Rahman", "Hassan", "Abdullah", "Yusof", "Ibrahim",
                "Zainal", "Kamarudin", "Osman"]


# ── Helpers ────────────────────────────────────────────────────────────────
def load_schema_skills(path):
    """Return the set of skill names seeded in schema.sql (for validation)."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    block = sql.split("INSERT INTO skills_library", 1)
    if len(block) < 2:
        return None
    body = block[1].split(";", 1)[0]
    return set(re.findall(r"^\s*\('([^']+)'", body, flags=re.M))


def make_name(rng, fk_in, fk_intl):
    """~55% Chinese, ~30% Malay, ~10% Indian, ~5% international students."""
    r = rng.random()
    if r < 0.55:
        return f"{rng.choice(CHINESE_SURNAMES)} {rng.choice(CHINESE_GIVEN)}"
    if r < 0.85:
        if rng.random() < 0.5:
            return f"{rng.choice(MALAY_MALE)} bin {rng.choice(MALAY_FATHER)}"
        return f"{rng.choice(MALAY_FEMALE)} binti {rng.choice(MALAY_FATHER)}"
    if r < 0.95:
        return fk_in.name()
    return fk_intl.name()


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def pg_array(items):
    """Python list -> PostgreSQL array literal usable in CSV COPY."""
    if not items:
        return "{}"
    esc = ['"' + str(i).replace("\\", "\\\\").replace('"', '\\"') + '"' for i in items]
    return "{" + ",".join(esc) + "}"


def sql_str(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def sql_array(items, cast="TEXT[]"):
    if not items:
        return f"'{{}}'::{cast}"
    return "ARRAY[" + ",".join(sql_str(i) for i in items) + f"]::{cast}"


def pick_proficiency(rng, year, archetype, has_evidence):
    base = {"strong": 0.45, "average": 0.0, "weak": -0.45}[archetype]
    score = base + 0.2 * (year - 2) + (0.3 if has_evidence else 0) + rng.gauss(0, 0.45)
    if score > 0.75:
        return "advanced"
    if score > -0.15:
        return "intermediate"
    return "beginner"


# ── Generator ──────────────────────────────────────────────────────────────
def generate(n, seed):
    rng = random.Random(seed)
    Faker.seed(seed)
    fk = Faker("en_US")
    fk_in = Faker("en_IN")

    all_skills = sorted({s for r in ROLES.values() for s in r["core"] + r["secondary"]}
                        | set(SOFT_SKILLS)
                        | {s for c in CERTIFICATIONS for s in c[2]}
                        | {s for p in PROJECTS.values() for t in p for s in t[2]})

    known = load_schema_skills(SCHEMA_PATH)
    if known is not None:
        missing = sorted(set(all_skills) - known)
        if missing:
            raise SystemExit(f"These skills are not in skills_library (schema.sql): {missing}")

    if bcrypt:
        pw_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt(rounds=10)).decode()
    else:
        pw_hash = "REPLACE_WITH_BCRYPT_HASH"
        print("WARNING: bcrypt not installed — password_hash is a placeholder, logins will fail.")

    roles = list(ROLE_WEIGHTS)
    role_w = [ROLE_WEIGHTS[r] for r in roles]
    arch_names = list(ARCHETYPES)
    arch_w = [ARCHETYPES[a][0] for a in arch_names]

    users, profiles, skills_rows, projects_rows, certs_rows, meta = [], [], [], [], [], []
    base_time = datetime(2026, 7, 1, 9, 0, 0)

    for i in range(1, n + 1):
        role = rng.choices(roles, role_w)[0]
        arch = rng.choices(arch_names, arch_w)[0]
        _, p_core, p_sec, gpa_mean = ARCHETYPES[arch]
        spec = ROLES[role]

        user_id, profile_id = str(uuid.UUID(int=rng.getrandbits(128))), str(uuid.UUID(int=rng.getrandbits(128)))
        full_name = make_name(rng, fk_in, fk)
        email = f"student{i:04d}@{EMAIL_DOMAIN}"
        created = base_time + timedelta(days=rng.randint(0, 80), minutes=rng.randint(0, 1440))

        year = rng.choices([1, 2, 3, 4], [0.15, 0.30, 0.35, 0.20])[0]
        grad_year = CURRENT_YEAR + (4 - year) if year < 4 else CURRENT_YEAR + rng.choice([0, 1])
        expected_grad = f"{rng.choice(['June', 'December'])} {grad_year}"
        gpa = round(clamp(rng.gauss(gpa_mean, 0.3), 2.0, 4.0), 2)

        # ── Skills ──
        chosen = set()
        for s in spec["core"]:
            if rng.random() < p_core:
                chosen.add(s)
        for s in spec["secondary"]:
            if rng.random() < p_sec:
                chosen.add(s)
        for s in SOFT_SKILLS:
            if rng.random() < 0.35 + (0.15 if arch == "strong" else 0):
                chosen.add(s)
        # off-role noise: 0–2 random skills
        for s in rng.sample(all_skills, rng.randint(0, 2)):
            chosen.add(s)
        if not chosen:
            chosen.add(rng.choice(spec["core"]))

        # ── Projects ──
        n_proj = clamp(int(round(rng.gauss({"strong": 2.5, "average": 1.5, "weak": 0.6}[arch] + (year - 2) * 0.4, 0.8))), 0, 5)
        proj_pool = PROJECTS[role][:]
        other = [t for r, ts in PROJECTS.items() if r != role for t in ts]
        proj_skill_evidence = set()
        for k in range(n_proj):
            tpl = proj_pool.pop(rng.randrange(len(proj_pool))) if proj_pool and rng.random() < {"strong": 0.85, "average": 0.65, "weak": 0.4}[arch] \
                else rng.choice(other)
            title = tpl[0].format(c=fk.company().split()[0])
            techs = list(tpl[2])
            ptype = "internship" if (k == 0 and rng.random() < 0.15 and year >= 3) else rng.choice(PROJECT_TYPES)
            yr = rng.randint(max(CURRENT_YEAR - year + 1, CURRENT_YEAR - 3), CURRENT_YEAR)
            projects_rows.append({
                "project_id": str(uuid.UUID(int=rng.getrandbits(128))),
                "profile_id": profile_id,
                "project_title": title,
                "description": tpl[1],
                "technologies": techs,
                "project_type": ptype,
                "year_completed": yr,
                "created_at": created,
            })
            proj_skill_evidence.update(techs)
            chosen.update(techs)  # a student who did the project has the skill

        # ── Certifications ──
        n_cert = clamp(int(round(rng.gauss({"strong": 1.6, "average": 0.7, "weak": 0.1}[arch], 0.7))), 0, 4)
        relevant = [c for c in CERTIFICATIONS if set(c[2]) & set(spec["core"] + spec["secondary"])]
        cert_pool = relevant + rng.sample(CERTIFICATIONS, 2)
        cert_skill_evidence = set()
        seen_cert = set()
        for _ in range(n_cert):
            c = rng.choice(cert_pool)
            if c[0] in seen_cert:
                continue
            seen_cert.add(c[0])
            issue = date(CURRENT_YEAR, 9, 1) - timedelta(days=rng.randint(30, 365 * min(year, 3)))
            expiry = issue + timedelta(days=365 * 3) if c[1] in ("Amazon Web Services", "CompTIA", "Cisco") else None
            certs_rows.append({
                "cert_id": str(uuid.UUID(int=rng.getrandbits(128))),
                "profile_id": profile_id,
                "cert_name": c[0],
                "issuer": c[1],
                "issue_date": issue.isoformat(),
                "expiry_date": expiry.isoformat() if expiry else None,
                "credential_url": c[3],
                "created_at": created,
            })
            cert_skill_evidence.update(c[2])
            chosen.update(c[2])

        # ── Internships ──
        p_intern = {1: 0.02, 2: 0.10, 3: 0.40, 4: 0.65}[year] * {"strong": 1.3, "average": 1.0, "weak": 0.5}[arch]
        n_intern = 0
        if rng.random() < p_intern:
            n_intern = 2 if (year == 4 and rng.random() < 0.2) else 1
        intern_skills = set(rng.sample(sorted(chosen), min(len(chosen), 3))) if n_intern else set()

        # ── student_skills rows ──
        for s in sorted(chosen):
            ev = []
            if s in proj_skill_evidence:
                ev.append("project")
            if s in cert_skill_evidence:
                ev.append("certification")
            if s in intern_skills:
                ev.append("internship")
            if rng.random() < 0.5 or not ev:
                ev.append("coursework")
            prof = pick_proficiency(rng, year, arch, len(ev) > 1 or "coursework" not in ev)
            notes = None
            if "project" in ev:
                notes = "Applied in project work."
            elif "internship" in ev:
                notes = "Used during internship."
            skills_rows.append({
                "student_skill_id": str(uuid.UUID(int=rng.getrandbits(128))),
                "profile_id": profile_id,
                "skill_name": s,
                "proficiency_level": prof,
                "evidence_type": ev,
                "evidence_notes": notes,
                "added_at": created,
            })

        interests = rng.sample(spec["interests"], rng.randint(1, len(spec["interests"])))
        is_complete = rng.random() < {"strong": 0.95, "average": 0.8, "weak": 0.55}[arch]

        users.append({
            "user_id": user_id, "email": email, "password_hash": pw_hash, "role": "student",
            "full_name": full_name, "is_active": True, "created_at": created, "updated_at": created,
        })
        profiles.append({
            "profile_id": profile_id, "user_id": user_id,
            "programme": rng.choice(spec["programmes"]), "university": UNIVERSITY,
            "gpa": gpa, "expected_graduation": expected_grad, "year_of_study": year,
            "internship_count": n_intern, "project_count": n_proj,
            "certification_count": len(seen_cert),
            "target_role": role, "career_interests": interests, "is_complete": is_complete,
            "created_at": created, "updated_at": created,
        })
        core_have = len(set(spec["core"]) & chosen)
        meta.append({
            "profile_id": profile_id, "email": email, "target_role": role, "archetype": arch,
            "year_of_study": year, "n_skills": len(chosen),
            "core_skills_covered": core_have, "core_skills_total": len(spec["core"]),
            "core_coverage_pct": round(core_have / len(spec["core"]) * 100, 1),
        })

    return users, profiles, skills_rows, projects_rows, certs_rows, meta


# ── Writers ────────────────────────────────────────────────────────────────
def write_csv(path, rows, array_cols=()):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (pg_array(v) if k in array_cols else ("" if v is None else v)) for k, v in r.items()})


def write_sql(path, users, profiles, skills, projects, certs, n, seed):
    L = []
    L.append("-- SEAGAS synthetic student data (generated by data/generate_synthetic_data.py)")
    L.append(f"-- students={n} seed={seed} generated={datetime.now():%Y-%m-%d %H:%M}")
    L.append(f"-- All accounts use email @{EMAIL_DOMAIN}. Remove with data/delete_synthetic_data.sql")
    L.append("SET client_encoding = 'UTF8';")
    L.append("BEGIN;\n")

    def batched(rows, size=200):
        for k in range(0, len(rows), size):
            yield rows[k:k + size]

    for b in batched(users):
        L.append("INSERT INTO users (user_id, email, password_hash, role, full_name, is_active, created_at, updated_at) VALUES")
        L.append(",\n".join(
            f"({sql_str(u['user_id'])}, {sql_str(u['email'])}, {sql_str(u['password_hash'])}, 'student', "
            f"{sql_str(u['full_name'])}, TRUE, {sql_str(str(u['created_at']))}, {sql_str(str(u['updated_at']))})"
            for u in b) + ";\n")

    for b in batched(profiles):
        L.append("INSERT INTO student_profiles (profile_id, user_id, programme, university, gpa, expected_graduation, "
                 "year_of_study, internship_count, project_count, certification_count, target_role, career_interests, "
                 "is_complete, created_at, updated_at) VALUES")
        L.append(",\n".join(
            f"({sql_str(p['profile_id'])}, {sql_str(p['user_id'])}, {sql_str(p['programme'])}, {sql_str(p['university'])}, "
            f"{p['gpa']}, {sql_str(p['expected_graduation'])}, {p['year_of_study']}, {p['internship_count']}, "
            f"{p['project_count']}, {p['certification_count']}, {sql_str(p['target_role'])}, "
            f"{sql_array(p['career_interests'])}, {sql_str(p['is_complete'])}, "
            f"{sql_str(str(p['created_at']))}, {sql_str(str(p['updated_at']))})"
            for p in b) + ";\n")

    # student_skills: resolve skill_id by name, so UUIDs of skills_library don't matter
    for b in batched(skills, 400):
        L.append("INSERT INTO student_skills (student_skill_id, profile_id, skill_id, proficiency_level, "
                 "evidence_type, evidence_notes, added_at)")
        L.append("SELECT v.id::uuid, v.pid::uuid, sl.skill_id, v.prof, v.ev::varchar(20)[], v.notes, v.added::timestamp")
        L.append("FROM (VALUES")
        L.append(",\n".join(
            f"({sql_str(s['student_skill_id'])}, {sql_str(s['profile_id'])}, {sql_str(s['skill_name'])}, "
            f"{sql_str(s['proficiency_level'])}, {sql_str(pg_array(s['evidence_type']))}, "
            f"{sql_str(s['evidence_notes']) if s['evidence_notes'] else 'NULL::text'}, {sql_str(str(s['added_at']))})"
            for s in b))
        L.append(") AS v(id, pid, skill, prof, ev, notes, added)")
        L.append("JOIN skills_library sl ON sl.skill_name = v.skill;\n")

    for b in batched(projects):
        L.append("INSERT INTO student_projects (project_id, profile_id, project_title, description, technologies, "
                 "project_type, year_completed, created_at) VALUES")
        L.append(",\n".join(
            f"({sql_str(p['project_id'])}, {sql_str(p['profile_id'])}, {sql_str(p['project_title'])}, "
            f"{sql_str(p['description'])}, {sql_array(p['technologies'])}, {sql_str(p['project_type'])}, "
            f"{p['year_completed']}, {sql_str(str(p['created_at']))})"
            for p in b) + ";\n")

    for b in batched(certs):
        L.append("INSERT INTO student_certifications (cert_id, profile_id, cert_name, issuer, issue_date, "
                 "expiry_date, credential_url, created_at) VALUES")
        L.append(",\n".join(
            f"({sql_str(c['cert_id'])}, {sql_str(c['profile_id'])}, {sql_str(c['cert_name'])}, {sql_str(c['issuer'])}, "
            f"{sql_str(c['issue_date'])}, {sql_str(c['expiry_date'])}, {sql_str(c['credential_url'])}, "
            f"{sql_str(str(c['created_at']))})"
            for c in b) + ";\n")

    L.append("COMMIT;")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def write_summary(path, users, profiles, skills, projects, certs, meta, n, seed):
    def dist(counter, total):
        return "\n".join(f"  {k:<28} {v:>5}  ({v / total * 100:5.1f}%)" for k, v in counter.most_common())

    gpas = [p["gpa"] for p in profiles]
    skill_counts = Counter(s["skill_name"] for s in skills)
    per_student = Counter(s["profile_id"] for s in skills)
    lines = [
        "SEAGAS Synthetic Dataset — Summary Statistics",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M}   seed={seed}",
        "=" * 60,
        f"Students:              {n}",
        f"Student skill entries: {len(skills)}  (mean {len(skills) / n:.1f} per student, "
        f"min {min(per_student.values())}, max {max(per_student.values())})",
        f"Projects:              {len(projects)}",
        f"Certifications:        {len(certs)}",
        f"GPA:                   mean {sum(gpas) / n:.2f}, min {min(gpas):.2f}, max {max(gpas):.2f}",
        "",
        "Target role:", dist(Counter(p["target_role"] for p in profiles), n), "",
        "Archetype:", dist(Counter(m["archetype"] for m in meta), n), "",
        "Year of study:", dist(Counter(f"Year {p['year_of_study']}" for p in profiles), n), "",
        "Internships:", dist(Counter(f"{p['internship_count']} internship(s)" for p in profiles), n), "",
        "Proficiency level:", dist(Counter(s["proficiency_level"] for s in skills), len(skills)), "",
        "Mean core-skill coverage by archetype:",
    ]
    for a in ARCHETYPES:
        vals = [m["core_coverage_pct"] for m in meta if m["archetype"] == a]
        if vals:
            lines.append(f"  {a:<10} {sum(vals) / len(vals):5.1f}%  (n={len(vals)})")
    lines += ["", "Students holding each skill:", dist(skill_counts, n)]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Generate SEAGAS synthetic student profiles")
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="number of students (default 500)")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help="random seed (default 42)")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    users, profiles, skills, projects, certs, meta = generate(args.n, args.seed)

    write_csv(os.path.join(OUT_DIR, "users.csv"), users)
    write_csv(os.path.join(OUT_DIR, "student_profiles.csv"), profiles, array_cols=("career_interests",))
    write_csv(os.path.join(OUT_DIR, "student_skills.csv"), skills, array_cols=("evidence_type",))
    write_csv(os.path.join(OUT_DIR, "student_projects.csv"), projects, array_cols=("technologies",))
    write_csv(os.path.join(OUT_DIR, "student_certifications.csv"), certs)
    write_csv(os.path.join(OUT_DIR, "students_meta.csv"), meta)
    write_sql(os.path.join(OUT_DIR, "seed_synthetic_students.sql"),
              users, profiles, skills, projects, certs, args.n, args.seed)
    write_summary(os.path.join(OUT_DIR, "summary_stats.txt"),
                  users, profiles, skills, projects, certs, meta, args.n, args.seed)

    print(f"Generated {args.n} students, {len(skills)} skill rows, {len(projects)} projects, "
          f"{len(certs)} certifications -> {OUT_DIR}")
    print(f"Demo login for any synthetic student: student0001@{EMAIL_DOMAIN} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
