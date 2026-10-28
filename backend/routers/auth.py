"""
SEAGAS — Authentication Router
Handles login, first-login password change, JWT token.
Students do not register themselves: their accounts are created from the
advisor's intake list by an admin (routers/intake.py).
Author: Soh Way Miin (Carl)
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import os

import audit
from advisor_scope import courses_of, position_label
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
class ChangePasswordRequest(BaseModel):
    # Not needed while the password is temporary: the user has just signed in with it
    current_password: str = ""
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    must_change_password: bool = False


# ── Helper Functions ──────────────────────────────────────────
# bcrypt only reads the first 72 bytes and bcrypt 5 raises on longer input
PASSWORD_MIN_CHARS = 8
PASSWORD_MAX_BYTES = 72


# Rules for every new password (frontend copy: frontend/src/utils/passwordRules.js)
PASSWORD_RULE_TEXT = ("at least 8 characters, with an uppercase letter, a lowercase letter, "
                      "a number and a symbol")


def password_error(password: str):
    """Message to show if the password breaks the rules, otherwise None"""
    if len(password.encode()) > PASSWORD_MAX_BYTES:
        return f"Password must be at most {PASSWORD_MAX_BYTES} bytes (about 72 letters or digits)."
    if (len(password) < PASSWORD_MIN_CHARS
            or not any(c.isupper() for c in password)
            or not any(c.islower() for c in password)
            or not any(c.isdigit() for c in password)
            or not any(not c.isalnum() and not c.isspace() for c in password)):
        return f"Password must have {PASSWORD_RULE_TEXT}."
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
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# While an account still has its temporary password, only these requests work
PASSWORD_CHANGE_PATHS = ("/api/auth/me", "/api/auth/change-password")


def get_current_user(
    request: Request,
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
    # A temporary password (new student, admin reset) must be changed before
    # the account can do anything else
    if result.must_change_password and request.url.path not in PASSWORD_CHANGE_PATHS:
        raise HTTPException(status_code=403,
                            detail="Please change your temporary password before continuing.")
    return result


# ── Endpoints ─────────────────────────────────────────────────
@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    student_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """Email + password; students also give their student ID.

    Every failure gives the same message, so the response never tells which of
    the three was wrong.
    """
    from sqlalchemy import text

    user = db.execute(
        text("SELECT * FROM users WHERE lower(email) = :email"),
        {"email": form_data.username.strip().lower()}
    ).fetchone()

    reason = None
    if not user:
        reason = "unknown email"
    elif not verify_password(form_data.password, user.password_hash):
        reason = "wrong password"
    elif user.role == "student" and (student_id or "").strip() != user.student_number:
        reason = "wrong or missing student ID"
    if reason:
        audit.record(db, "auth.login_failed", user=user, email=form_data.username.strip().lower(),
                     request=request, details={"reason": reason}, commit=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, student ID or password"
        )

    if not user.is_active:
        audit.record(db, "auth.login_failed", user=user, request=request,
                     details={"reason": "account disabled"}, commit=True)
        raise HTTPException(status_code=403, detail="Account is disabled")

    audit.record(db, "auth.login", user=user, request=request, commit=True)

    token = create_access_token({"sub": str(user.user_id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "must_change_password": user.must_change_password
    }


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "student_number": current_user.student_number,
        "course": current_user.course,
        # Advisors: Dean / Head of Programme, the courses they see, 5-digit staff ID
        "staff_number": current_user.staff_number,
        "advisor_position": current_user.advisor_position,
        "advisor_courses": courses_of(current_user) if current_user.role != "student" else [],
        "position_label": position_label(current_user.advisor_position, current_user.advisor_courses),
        "must_change_password": current_user.must_change_password
    }


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a new password; required after a temporary one (first sign-in, admin reset).

    While the password is temporary the current password is not asked again: the
    user has just signed in with it. A voluntary change must give it.
    """
    from sqlalchemy import text

    if not current_user.must_change_password and             not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Your current password is not correct.")
    check_password(req.new_password)
    if verify_password(req.new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Choose a password different from the current one.")
    db.execute(
        text("""
            UPDATE users SET password_hash = :pw, must_change_password = FALSE,
                             updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :uid
        """),
        {"pw": hash_password(req.new_password), "uid": str(current_user.user_id)}
    )
    audit.record(db, "auth.password_change", user=current_user, request=request,
                 target_type="user", target_id=current_user.user_id)
    db.commit()
    return {"message": "Password changed"}