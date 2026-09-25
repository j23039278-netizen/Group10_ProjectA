"""
SEAGAS — Authentication Router
Handles login, register, JWT token
Author: Soh Way Miin (Carl)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import bcrypt
import os

from database import get_db
from database import engine
import sys
sys.path.append("..")
from database import SessionLocal

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


# ── Pydantic Schemas ──────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"  # student | advisor | admin


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str


# ── Helper Functions ──────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Import here to avoid circular imports
    from database import SessionLocal
    from database import engine
    # Get user from DB
    db_session = db
    result = db_session.execute(
        __import__('sqlalchemy').text("SELECT * FROM users WHERE user_id = :uid"),
        {"uid": user_id}
    ).fetchone()

    if result is None:
        raise credentials_exception
    return result


# ── Endpoints ─────────────────────────────────────────────────
@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    from sqlalchemy import text

    # Check if email exists
    existing = db.execute(
        text("SELECT user_id FROM users WHERE email = :email"),
        {"email": req.email}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ("student", "advisor", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    hashed = hash_password(req.password)

    db.execute(
        text("""
            INSERT INTO users (email, password_hash, role, full_name)
            VALUES (:email, :pw, :role, :name)
        """),
        {"email": req.email, "pw": hashed, "role": req.role, "name": req.full_name}
    )
    db.commit()
    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    from sqlalchemy import text

    user = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": form_data.username}
    ).fetchone()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.user_id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name
    }


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }