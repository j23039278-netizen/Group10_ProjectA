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
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import os

from database import get_db
from database import engine
import sys
sys.path.append("..")
from database import SessionLocal

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Tokens are signed with SECRET_KEY, so there is no default: anyone who knew a
# default could forge a token for any account, including admins.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Add it to backend/.env "
                       "(start_backend.bat creates one with a random key).")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Every new account must use its role's NewInti email domain, so an account's
# email always matches its role. The role itself still comes from users.role.
# Accounts created before this rule (e.g. synthetic test students) still sign in.
ROLE_EMAIL_DOMAINS = {
    "student": "student.newinti.edu.my",
    "advisor": "advisor.newinti.edu.my",
    "admin":   "admin.newinti.edu.my",
}


# ── Pydantic Schemas ──────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=1, max_length=255)
    # Public sign-up is for students only. Advisor and admin accounts are
    # created by an admin through POST /api/admin/users.
    role: str = "student"


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str


# ── Helper Functions ──────────────────────────────────────────
# bcrypt only reads the first 72 bytes and bcrypt 5 raises on longer input
PASSWORD_MIN_CHARS = 8
PASSWORD_MAX_BYTES = 72


def password_error(password: str):
    """Message to show if the password breaks the rules, otherwise None"""
    if len(password) < PASSWORD_MIN_CHARS:
        return f"Password must be at least {PASSWORD_MIN_CHARS} characters."
    if len(password.encode()) > PASSWORD_MAX_BYTES:
        return f"Password must be at most {PASSWORD_MAX_BYTES} bytes (about 72 letters or digits)."
    return None


def check_password(password: str):
    error = password_error(password)
    if error:
        raise HTTPException(status_code=400, detail=error)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode()) > PASSWORD_MAX_BYTES:
        return False  # can never match a stored hash; bcrypt would raise
    return bcrypt.checkpw(password.encode(), hashed.encode())


def email_domain_error(email: str, role: str):
    """Message to show if email is not on the role's domain, otherwise None"""
    domain = ROLE_EMAIL_DOMAINS[role]
    if email.strip().lower().rsplit("@", 1)[-1] != domain:
        return f"{role.capitalize()} accounts must use an @{domain} email address."
    return None


def check_email_domain(email: str, role: str):
    error = email_domain_error(email, role)
    if error:
        raise HTTPException(status_code=400, detail=error)


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

    # A deactivated account must not keep using a token issued before
    if result is None or not result.is_active:
        raise credentials_exception
    return result


# ── Endpoints ─────────────────────────────────────────────────
@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    from sqlalchemy import text

    if req.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only student accounts can be registered. "
                   "Advisor and admin accounts are created by an administrator."
        )

    email = req.email.strip().lower()
    check_email_domain(email, "student")

    # Check if email exists
    existing = db.execute(
        text("SELECT user_id FROM users WHERE lower(email) = :email"),
        {"email": email}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    check_password(req.password)
    hashed = hash_password(req.password)

    db.execute(
        text("""
            INSERT INTO users (email, password_hash, role, full_name)
            VALUES (:email, :pw, 'student', :name)
        """),
        {"email": email, "pw": hashed, "name": req.full_name}
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
        text("SELECT * FROM users WHERE lower(email) = :email"),
        {"email": form_data.username.strip().lower()}
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