"""
SEAGAS — FastAPI Main Entry Point
Group 10 | COS40005 | Swinburne University
Author: Soh Way Miin (Carl) — Backend Developer
"""
 
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from routers import auth, students, jobs, assessments, advisor, admin, intake, library
from routers.progress import router as progress_router
from routers.cv import router as cv_router
from routers.experiences import router as experiences_router
from routers.career import router as career_router
from routers.system_settings import public_router as settings_router, admin_router as admin_settings_router
import nlp_service
 
# Load the NLP model in the background so the first assessment does not wait for it
@asynccontextmanager
async def lifespan(app):
    nlp_service.warm_up_in_background()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="SEAGAS API",
    description="Student Employability Assessment and Skill Gap Analysis System",
    version="1.0.0"
)
 
# CORS — allows React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Register routers
app.include_router(auth.router,        prefix="/api/auth",        tags=["Authentication"])
app.include_router(cv_router,          prefix="/api/students/cv", tags=["Students"])
app.include_router(experiences_router, prefix="/api/students/experiences", tags=["Students"])
app.include_router(career_router,      prefix="/api/students/career-paths", tags=["Students"])
app.include_router(students.router,    prefix="/api/students",    tags=["Students"])
app.include_router(jobs.router,        prefix="/api/jobs",        tags=["Jobs"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(advisor.router,     prefix="/api/advisor",     tags=["Advisor"])
app.include_router(progress_router,    prefix="/api/progress",    tags=["Progress"])
app.include_router(admin_settings_router, prefix="/api/admin/settings", tags=["Admin"])
app.include_router(admin.router,       prefix="/api/admin",       tags=["Admin"])
app.include_router(library.router,     prefix="/api/library",     tags=["Library"])
app.include_router(settings_router,    prefix="/api/settings",    tags=["Settings"])
app.include_router(intake.router,      prefix="/api/intake",      tags=["Student intake"])
 
 
@app.get("/")
def root():
    return {"message": "SEAGAS API is running", "version": "1.0.0"}
 
 
@app.get("/health")
def health_check():
    return {"status": "healthy"}
 