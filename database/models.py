"""
SEAGAS — SQLAlchemy ORM Models
Group 10 | COS40005 | Swinburne University
Author: Soh Way Miin (Carl) — Backend Developer

Maps directly to schema.sql.
Used by FastAPI via SQLAlchemy + psycopg2.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime,
    ForeignKey, Integer, Numeric, SmallInteger, String,
    Text, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


# ── Base ──────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── TABLE 1: users ────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    user_id       = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email         = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20),  nullable=False)
    full_name     = Column(String(255), nullable=False)
    is_active     = Column(Boolean,     nullable=False, default=True)
    created_at    = Column(DateTime,    nullable=False, default=datetime.utcnow)
    updated_at    = Column(DateTime,    nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("role IN ('student','advisor','admin')", name="chk_user_role"),
    )

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)


# ── TABLE 2: student_profiles ─────────────────────────────────
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    profile_id          = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"),
                                 nullable=False, unique=True, index=True)
    programme           = Column(String(255))
    university          = Column(String(255))
    gpa                 = Column(Numeric(3, 2))
    expected_graduation = Column(String(20))
    year_of_study       = Column(SmallInteger)
    internship_count    = Column(SmallInteger, default=0)
    project_count       = Column(SmallInteger, default=0)
    certification_count = Column(SmallInteger, default=0)
    target_role         = Column(String(100), index=True)
    career_interests    = Column(ARRAY(Text))
    is_complete         = Column(Boolean, default=False)
    created_at          = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at          = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user             = relationship("User",                back_populates="student_profile")
    student_skills   = relationship("StudentSkill",        back_populates="profile", cascade="all, delete-orphan")
    projects         = relationship("StudentProject",       back_populates="profile", cascade="all, delete-orphan")
    certifications   = relationship("StudentCertification", back_populates="profile", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription",       back_populates="profile")
    assessments      = relationship("Assessment",           back_populates="profile", cascade="all, delete-orphan")
    recommendations  = relationship("StudentRecommendation",back_populates="profile", cascade="all, delete-orphan")


# ── TABLE 3: skills_library ───────────────────────────────────
class SkillLibrary(Base):
    __tablename__ = "skills_library"

    skill_id    = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    skill_name  = Column(String(100), nullable=False, unique=True, index=True)
    category    = Column(String(30),  nullable=False, index=True)
    aliases     = Column(ARRAY(Text))
    description = Column(Text)
    is_active   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "category IN ('Technical','AI_Digital','Analytical','Soft')",
            name="chk_skill_category"
        ),
    )

    # Relationships
    student_skills      = relationship("StudentSkill",          back_populates="skill")
    job_role_skills     = relationship("JobRoleSkill",          back_populates="skill")
    extracted_skills    = relationship("JDExtractedSkill",      back_populates="skill")
    match_results       = relationship("SkillMatchResult",      back_populates="skill")
    recommendations     = relationship("RecommendationLibrary", back_populates="skill",
                                        cascade="all, delete-orphan")


# ── TABLE 4: student_skills ───────────────────────────────────
class StudentSkill(Base):
    __tablename__ = "student_skills"

    student_skill_id  = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    profile_id        = Column(UUID(as_uuid=True), ForeignKey("student_profiles.profile_id", ondelete="CASCADE"),
                               nullable=False, index=True)
    skill_id          = Column(UUID(as_uuid=True), ForeignKey("skills_library.skill_id", ondelete="RESTRICT"),
                               nullable=False, index=True)
    proficiency_level = Column(String(20), nullable=False, default="intermediate")
    evidence_type     = Column(ARRAY(Text), default=[])
    evidence_notes    = Column(Text)
    added_at          = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="uq_student_skill"),
        CheckConstraint(
            "proficiency_level IN ('beginner','intermediate','advanced')",
            name="chk_proficiency"
        ),
    )

    profile = relationship("StudentProfile", back_populates="student_skills")
    skill   = relationship("SkillLibrary",   back_populates="student_skills")


# ── TABLE 5: job_roles + job_role_skills ──────────────────────
class JobRole(Base):
    __tablename__ = "job_roles"

    role_id        = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    role_name      = Column(String(100), nullable=False, unique=True)
    role_code      = Column(String(30),  nullable=False, unique=True)
    description    = Column(Text)
    industry_level = Column(String(20), default="entry")
    is_active      = Column(Boolean, nullable=False, default=True)
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "industry_level IN ('entry','junior','mid','senior')",
            name="chk_industry_level"
        ),
    )

    role_skills      = relationship("JobRoleSkill",   back_populates="role", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="role")
    assessments      = relationship("Assessment",     back_populates="role")


class JobRoleSkill(Base):
    __tablename__ = "job_role_skills"

    role_skill_id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    role_id       = Column(UUID(as_uuid=True), ForeignKey("job_roles.role_id",       ondelete="CASCADE"),
                           nullable=False, index=True)
    skill_id      = Column(UUID(as_uuid=True), ForeignKey("skills_library.skill_id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    importance    = Column(String(10), nullable=False, default="required")

    __table_args__ = (
        UniqueConstraint("role_id", "skill_id", name="uq_role_skill"),
        CheckConstraint("importance IN ('required','preferred','bonus')", name="chk_importance"),
    )

    role  = relationship("JobRole",      back_populates="role_skills")
    skill = relationship("SkillLibrary", back_populates="job_role_skills")


# ── TABLE 6: job_descriptions + jd_extracted_skills ──────────
class JobDescription(Base):
    __tablename__ = "job_descriptions"

    jd_id            = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    profile_id       = Column(UUID(as_uuid=True), ForeignKey("student_profiles.profile_id", ondelete="SET NULL"),
                              nullable=True, index=True)
    role_id          = Column(UUID(as_uuid=True), ForeignKey("job_roles.role_id", ondelete="SET NULL"),
                              nullable=True, index=True)
    title            = Column(String(255))
    company          = Column(String(255))
    raw_text         = Column(Text, nullable=False)
    source           = Column(String(20), default="student_input")
    nlp_status       = Column(String(20), nullable=False, default="pending", index=True)
    nlp_processed_at = Column(DateTime)
    created_at       = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("source IN ('student_input','admin_template','scraped')", name="chk_jd_source"),
        CheckConstraint("nlp_status IN ('pending','processing','complete','failed')", name="chk_nlp_status"),
    )

    profile          = relationship("StudentProfile",   back_populates="job_descriptions")
    role             = relationship("JobRole",          back_populates="job_descriptions")
    extracted_skills = relationship("JDExtractedSkill", back_populates="jd", cascade="all, delete-orphan")
    assessments      = relationship("Assessment",       back_populates="jd")


class JDExtractedSkill(Base):
    __tablename__ = "jd_extracted_skills"

    extracted_skill_id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    jd_id              = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.jd_id", ondelete="CASCADE"),
                                nullable=False, index=True)
    skill_id           = Column(UUID(as_uuid=True), ForeignKey("skills_library.skill_id", ondelete="SET NULL"),
                                nullable=True, index=True)
    raw_skill_text     = Column(String(255), nullable=False)
    extraction_method  = Column(String(20),  nullable=False)
    confidence_score   = Column(Numeric(4, 3))
    importance         = Column(String(10), default="required")
    extracted_at       = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "extraction_method IN ('spacy_ner','keyword','semantic')",
            name="chk_extraction_method"
        ),
        CheckConstraint("importance IN ('required','preferred','bonus')", name="chk_extracted_importance"),
    )

    jd    = relationship("JobDescription", back_populates="extracted_skills")
    skill = relationship("SkillLibrary",   back_populates="extracted_skills")


# ── TABLE 7: assessments + skill_match_results ───────────────
class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id       = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    profile_id          = Column(UUID(as_uuid=True), ForeignKey("student_profiles.profile_id", ondelete="CASCADE"),
                                 nullable=False, index=True)
    jd_id               = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.jd_id", ondelete="SET NULL"),
                                 nullable=True)
    role_id             = Column(UUID(as_uuid=True), ForeignKey("job_roles.role_id", ondelete="SET NULL"),
                                 nullable=True, index=True)
    matching_method     = Column(String(20), nullable=False, default="semantic")
    readiness_score     = Column(Numeric(5, 2), nullable=False)
    score_technical     = Column(Numeric(5, 2))
    score_ai_digital    = Column(Numeric(5, 2))
    score_analytical    = Column(Numeric(5, 2))
    score_communication = Column(Numeric(5, 2))
    score_industry_exp  = Column(Numeric(5, 2))
    score_project_exp   = Column(Numeric(5, 2))
    score_certification = Column(Numeric(5, 2))
    created_at          = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        CheckConstraint("matching_method IN ('keyword','semantic','hybrid')", name="chk_matching_method"),
        CheckConstraint("readiness_score BETWEEN 0 AND 100",                 name="chk_readiness_score"),
    )

    profile       = relationship("StudentProfile",      back_populates="assessments")
    jd            = relationship("JobDescription",      back_populates="assessments")
    role          = relationship("JobRole",             back_populates="assessments")
    match_results = relationship("SkillMatchResult",    back_populates="assessment", cascade="all, delete-orphan")
    recommendations = relationship("StudentRecommendation", back_populates="assessment", cascade="all, delete-orphan")


class SkillMatchResult(Base):
    __tablename__ = "skill_match_results"

    match_id              = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    assessment_id         = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"),
                                   nullable=False, index=True)
    skill_id              = Column(UUID(as_uuid=True), ForeignKey("skills_library.skill_id", ondelete="RESTRICT"),
                                   nullable=False)
    match_status          = Column(String(15), nullable=False, index=True)
    similarity_score      = Column(Numeric(4, 3))
    matching_method       = Column(String(20), nullable=False)
    matched_student_skill = Column(String(255))

    __table_args__ = (
        UniqueConstraint("assessment_id", "skill_id", name="uq_assessment_skill"),
        CheckConstraint("match_status IN ('strong','developing','gap')",          name="chk_match_status"),
        CheckConstraint("matching_method IN ('keyword','semantic','hybrid')",     name="chk_result_method"),
    )

    assessment = relationship("Assessment",   back_populates="match_results")
    skill      = relationship("SkillLibrary", back_populates="match_results")


# ── TABLE 8: recommendations_library ─────────────────────────
class RecommendationLibrary(Base):
    __tablename__ = "recommendations_library"

    resource_id    = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    skill_id       = Column(UUID(as_uuid=True), ForeignKey("skills_library.skill_id", ondelete="CASCADE"),
                            nullable=False, index=True)
    resource_title = Column(String(255), nullable=False)
    resource_type  = Column(String(20),  nullable=False, index=True)
    provider       = Column(String(255))
    url            = Column(Text)
    duration_hours = Column(SmallInteger)
    cost           = Column(String(50), default="Free")
    difficulty     = Column(String(15), default="beginner")
    description    = Column(Text)
    is_active      = Column(Boolean, nullable=False, default=True)
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('course','certification','project','workshop','competition','internship')",
            name="chk_resource_type"
        ),
        CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced')",
            name="chk_difficulty"
        ),
    )

    skill           = relationship("SkillLibrary",        back_populates="recommendations")
    student_recs    = relationship("StudentRecommendation", back_populates="resource")


# ── TABLE 9: student_recommendations ─────────────────────────
class StudentRecommendation(Base):
    __tablename__ = "student_recommendations"

    student_rec_id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    assessment_id  = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"),
                            nullable=False, index=True)
    profile_id     = Column(UUID(as_uuid=True), ForeignKey("student_profiles.profile_id", ondelete="CASCADE"),
                            nullable=False, index=True)
    resource_id    = Column(UUID(as_uuid=True), ForeignKey("recommendations_library.resource_id", ondelete="RESTRICT"),
                            nullable=False)
    status         = Column(String(15), nullable=False, default="not_started", index=True)
    started_at     = Column(DateTime)
    completed_at   = Column(DateTime)
    notes          = Column(Text)
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("assessment_id", "resource_id", name="uq_assessment_resource"),
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="chk_rec_status"),
    )

    assessment = relationship("Assessment",           back_populates="recommendations")
    profile    = relationship("StudentProfile",        back_populates="recommendations")
    resource   = relationship("RecommendationLibrary", back_populates="student_recs")


# ── TABLE 10: student_projects ────────────────────────────────
class StudentProject(Base):
    __tablename__ = "student_projects"

    project_id    = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    profile_id    = Column(UUID(as_uuid=True), ForeignKey("student_profiles.profile_id", ondelete="CASCADE"),
                           nullable=False, index=True)
    project_title = Column(String(255), nullable=False)
    description   = Column(Text)
    technologies  = Column(ARRAY(Text))
    project_type  = Column(String(20), default="academic")
    year_completed= Column(SmallInteger)
    created_at    = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "project_type IN ('academic','personal','internship','competition')",
            name="chk_project_type"
        ),
    )

    profile = relationship("StudentProfile", back_populates="projects")


# ── TABLE 11: student_certifications ─────────────────────────
class StudentCertification(Base):
    __tablename__ = "student_certifications"

    cert_id        = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    profile_id     = Column(UUID(as_uuid=True), ForeignKey("student_profiles.profile_id", ondelete="CASCADE"),
                            nullable=False, index=True)
    cert_name      = Column(String(255), nullable=False)
    issuer         = Column(String(255))
    issue_date     = Column(Date)
    expiry_date    = Column(Date)
    credential_url = Column(Text)
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)

    profile = relationship("StudentProfile", back_populates="certifications")
