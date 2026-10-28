# Group10_ProjectA
## AI-Powered Student Employability Assessment and Skill Gap Analysis System (SEAGAS)

**COS40005 Computing Technology Projects A**
**Swinburne University of Technology | INTI International College Subang**
**Semester 2, 2026**

---

## 📋 Project Overview

SEAGAS is a Proof of Concept (POC) web-based platform that uses Natural Language Processing (NLP) and AI-driven skill matching to:

- Evaluate students' skills against real industry job requirements
- Generate a personalised Job Readiness Score
- Identify skill gaps (Strong Skills / Developing Skills / Skill Gaps)
- Provide targeted recommendations to improve employability
- Display cohort-level skill gap trends for academic advisors

---

## 👥 Team Members

| Name | Role | Responsibility |
|------|------|----------------|
| Yan Min Xuan (Shanice) | Team Leader & Report Lead | UI/UX design, Student Dashboard, report writing |
| Tan Jun Xiong (Aaron) | Co-Leader & Recommendation Engine | Rule-based recommendation engine, development tracking |
| Soh Way Miin (Carl) | Backend Developer | FastAPI backend, database, security, NLP integration |
| Tee Ren Hang | Frontend Developer & UI/UX Designer | React frontend, Advisor Dashboard, data visualisation |
| Ng Yong Hin | AI / NLP Engineer | NLP extraction, skill matching, dataset generation |

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, React Router, Recharts |
| Backend | Python, FastAPI, SQLAlchemy, JWT sign-in, bcrypt password hashing |
| AI / NLP | Keyword matching (standard library); spaCy + Sentence Transformers (`all-MiniLM-L6-v2`) for semantic and hybrid matching; scikit-learn |
| Database | PostgreSQL 17 |
| Development | GitHub, VS Code, pytest |

---

## 📁 Project Structure

```
Group10_ProjectA/
├── frontend/           # React + Vite app (student, advisor and admin portals)
├── backend/            # FastAPI API; start_backend.bat sets everything up
├── nlp/                # Skill extraction and Strong / Developing / Gap matching (Ng Yong Hin)
├── recommendation/     # Rule-based recommendation engine (Aaron)
├── database/           # schema.sql, migrate_existing_db.sql, seed files
├── data/               # Synthetic students, skills library CSV, JD dataset, run_assessments.py
├── tests/              # Backend API and data tests (pytest)
├── docs/               # NLP interface and rules, work reports, progress checks
├── start_all.bat       # One-click start: backend + frontend (Windows)
└── README.md
```

Key documents: `docs/NLP_INTERFACE.md` (backend ↔ NLP contract), `docs/NLP_CLASSIFICATION_RULES.md`
(how Strong / Developing / Gap is decided), `database/README.md` (tables).

---

## 🌿 Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, reviewed code only |
| `dev` | Main development branch |
| `feature/frontend-dashboard` | Feature branches (one per task) |
| `feature/backend-api` | |
| `feature/nlp-extraction` | |
| `feature/recommendation-engine` | |

**Rules:**
- Never push directly to `main`
- All changes go through `dev` first
- Create a Pull Request (PR) before merging into `main`
- At least one team member must review each PR

---

## 🚀 Getting Started

### Prerequisites
- Windows (the start scripts are `.bat` files; the manual steps below work anywhere)
- Python 3.10+ (tested with 3.12)
- Node.js 18+
- PostgreSQL 17 installed in `C:\Program Files\PostgreSQL\17`, user `postgres`, password `postgres123`
- Git

### Quick start (Windows)
Double-click **`start_all.bat`** in the repo root. It opens two windows:

| Window | What it does | URL |
|--------|--------------|-----|
| SEAGAS Backend (`backend\start_backend.bat`) | Creates `seagas_db` if needed, applies `schema.sql` / `migrate_existing_db.sql`, loads the skills, roles, recommendations, 5,000 synthetic students and the JD dataset, gives `backend\.env` a random `SECRET_KEY`, assesses the synthetic students once, then starts FastAPI | http://127.0.0.1:8000/docs |
| SEAGAS Frontend (`frontend\start_frontend.bat`) | `npm install` if needed, then `npm run dev` | http://localhost:5173 |

Every step checks first, so the scripts are safe to run again after `git pull`; that is also how
database changes reach an existing database.

**First run:** when the database has no admin, the backend window asks to create one
(email must end with `@admin.newinti.edu.my`). No passwords are stored in the code.

### Manual setup
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate            # macOS / Linux: source venv/bin/activate
pip install -r requirements.txt
python ensure_secret_key.py        # creates backend/.env SECRET_KEY if missing
# backend/.env also needs DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/seagas_db
uvicorn main:app --reload          # http://127.0.0.1:8000/docs

# Frontend (another terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173
```
For a new database, run `database/schema.sql`, then `database/migrate_existing_db.sql` and the seed
files in the order used by `backend/start_backend.bat`.

### NLP: semantic and hybrid matching (optional)
Keyword matching works with no extra install. For semantic and hybrid matching:
```bash
python -m pip install -r nlp/requirements.txt    # about 1 GB, mostly torch
```
Restart the backend afterwards. The first start downloads the model (~90 MB) and loads it in
20–30 s; the backend window then shows `NLP model loaded (hybrid ready)`. Without the packages,
semantic and hybrid requests fall back to keyword matching and the student sees a short notice.

### Accounts and roles
| Role | How the account is created | Email must end with |
|------|----------------------------|---------------------|
| Student | An advisor uploads the new-student list (**New Students**: Full Name, Phone Number, Personal Email, Course, Programme); an admin assigns the student ID and school email and creates the account (**Student Intake**) | `@student.newinti.edu.my` |
| Advisor | An admin creates it in **User Management** and sets the position (Dean or Head of Programme), which decides the courses the advisor sees, and a 5-digit staff ID | `@advisor.newinti.edu.my` |
| Admin | The first one in the backend window (`backend/create_admin.py`); more in User Management | `@admin.newinti.edu.my` |

Everyone signs in on the same page; the role stored in the database decides which portal opens.
Students also enter their 9-digit **student ID**. There is no sign-up page.
Every student belongs to one course: **Computer Science**, **Business** or **ICT** (the 5,000
synthetic students are split evenly). Advisor and admin student lists, and the advisor overview
and skill-gap charts, can be filtered by course. The course decides which target roles a student
can choose: Computer Science all 6 IT roles, ICT 4 of them (Web Developer, Data Analyst, Cloud
Engineer, Cybersecurity Analyst), Business the Business roles (Business Analyst, Marketing
Executive, Financial Analyst, HR Executive). The 28 Business skills (source v3) are in the skills
library (`data/skills/skills_library.csv`) and the Business role templates in
`database/seed_job_role_skills.sql`; their learning resources are in
`database/seed_business_skills.sql`. ICT roles share the IT skills and resources with Computer Science. Students only see the skills of their
course when adding skills (soft skills and shared tools such as Excel and Power BI are in every
list). Every student also has a programme (major) of their course, given in the new-student list
with the course; students cannot change it, admins can in User Management. Admins set a role's courses when adding or editing it. Students enter both
GPA and CGPA and are reminded to update them at the start of each semester (January, May,
September). The advisor's **Download the template** gives an Excel file whose Course column is
a drop-down list.

Advisors only see and add students of their own courses:

| Position | Courses | Staff ID |
|---|---|---|
| Dean, Computing | Computer Science and ICT | 10xxx |
| Head of Programme, Computer Science | Computer Science | 11xxx |
| Head of Programme, ICT | ICT | 12xxx |
| Dean, Business | Business | 20xxx |
| Head of Programme, Business | Business | 21xxx |

The admin enters the advisor's name and personal email and chooses the position and staff ID (a
free one is suggested). As for new students, the system makes a temporary password and emails the
staff ID, school email (`<staff ID>@advisor.newinti.edu.my` unless the admin changes it) and password
to the personal email; the advisor must choose a new password at first sign-in. The admin can later change the name, position and staff ID or reset the password. Each office (Computing, Business) has only one active Dean; to
replace a Dean, change the old Dean's position or deactivate the account first. Advisors that existed
before this change became Dean of Computing (the earliest one) or Head of Programme, CS; change them in
User Management if needed.

New students receive their student ID, school email and a temporary password at their personal
email, and must choose their own password at first sign-in (admin password resets work the same
way). Without a mail server the emails are only stored, and admins read them under
**Student Intake → Email outbox**. To send real emails, add `SMTP_HOST`, `SMTP_PORT`,
`SMTP_USER`, `SMTP_PASSWORD` and `SMTP_FROM` to `backend/.env` (never commit them).

Test student: `student0001@synthetic.example.com`, student ID `900000001`, password `Seagas@2026`
(synthetic data only; synthetic student number N has student ID 900000000 + N, e.g. student0042 → `900000042`).

### Running the tests
```bash
python -m pip install -r tests/requirements.txt
python -m pytest tests -q                      # backend API (own temporary database) + data tests
python -m pytest nlp/tests -q -m "not model"   # NLP tests without loading the model
```

### Batch assessments
`python data/run_assessments.py` assesses every synthetic student that has no assessment yet
(the start script runs it once), so the advisor dashboard has cohort data.
Options: `--method keyword|semantic|hybrid`, `--limit N`, `--force`.

---

## 📅 Sprint Plan

| Sprint | Duration | Focus |
|--------|----------|-------|
| Sprint 1 | Week 6–8 | Data preparation, database design, UI/UX wireframes |
| Sprint 2 | Week 9–10 | NLP module, backend API, recommendation engine |
| Sprint 3 | Week 11–12 | Frontend, system integration, testing |
| Sprint 4 | Week 13–14 | AI evaluation, usability evaluation, report, demo |

---

## 📄 License

This project is developed for academic purposes under COS40005 Computing Technology Projects A at Swinburne University of Technology.
