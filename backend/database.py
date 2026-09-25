"""
SEAGAS — Database Connection
Group 10 | COS40005 | Swinburne University
Author: Soh Way Miin (Carl) — Backend Developer
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency — used in every FastAPI endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()