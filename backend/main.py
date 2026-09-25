"""
SEAGAS — FastAPI Main Entry Point
Group 10 | COS40005 | Swinburne University
Author: Soh Way Miin (Carl) — Backend Developer
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, students, jobs, assessments, advisor

app = FastAPI(
    title="SEAGAS API",
    description="Student Employability Assessment and Skill Gap Analysis System",
    version="1.0.0"
)

# CORS — allows React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router,        prefix="/api/auth",        tags=["Authentication"])
app.include_router(students.router,    prefix="/api/students",    tags=["Students"])
app.include_router(jobs.router,        prefix="/api/jobs",        tags=["Jobs"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(advisor.router,     prefix="/api/advisor",     tags=["Advisor"])


@app.get("/")
def root():
    return {"message": "SEAGAS API is running", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}