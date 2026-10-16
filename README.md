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
| Student | Registers on the website | `@student.newinti.edu.my` |
| Advisor | An admin creates it in **User Management** | `@advisor.newinti.edu.my` |
| Admin | The first one in the backend window (`backend/create_admin.py`); more in User Management | `@admin.newinti.edu.my` |

Everyone signs in on the same page; the role stored in the database decides which portal opens.
Test student: `student0001@synthetic.example.com` / `Seagas@2026` (synthetic data only).

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
