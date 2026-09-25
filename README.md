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
| Frontend | React.js, Chart.js, Plotly |
| Backend | Python, FastAPI |
| AI / NLP | spaCy, Sentence Transformers, scikit-learn |
| Database | PostgreSQL |
| Development | GitHub, Docker, VS Code |

---

## 📁 Project Structure

```
Group10_ProjectA/
├── frontend/           # React frontend (Ren Hang)
├── backend/            # FastAPI backend (Carl)
├── nlp/                # NLP & AI matching engine (Yong Hin)
├── recommendation/     # Rule-based recommendation engine (Aaron)
├── database/           # Database schema & migrations (Carl)
├── data/               # Synthetic dataset & JD dataset (Yong Hin)
├── docs/               # Technical documentation
└── README.md
```

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
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Git

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### NLP Setup
```bash
cd nlp
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

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
