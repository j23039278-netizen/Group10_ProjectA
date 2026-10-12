"""
SEAGAS — Create an admin account (interactive)

Admins create advisor accounts from the Admin page, so the very first admin
has to be created here. Nothing is hard-coded: the email, name and password
are typed in, and only the bcrypt hash is stored.

Usage (from the backend folder):
    python create_admin.py
start_backend.bat offers to run this when the database has no admin yet.
"""

import getpass
import re
import sys

from sqlalchemy import text

from database import SessionLocal
from routers.auth import hash_password

PASSWORD_MIN = 8
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def ask(prompt, check, error):
    while True:
        value = input(prompt).strip()
        if check(value):
            return value
        print("  " + error)


def ask_password():
    while True:
        pw = getpass.getpass(f"Password (min {PASSWORD_MIN} characters, hidden): ")
        if len(pw) < PASSWORD_MIN:
            print(f"  Password must be at least {PASSWORD_MIN} characters.")
            continue
        if getpass.getpass("Confirm password: ") != pw:
            print("  Passwords do not match.")
            continue
        return pw


def main():
    db = SessionLocal()
    try:
        print("Create a SEAGAS admin account")
        email = ask("Email: ", lambda v: EMAIL_RE.match(v), "Please enter a valid email address.")
        if db.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": email}).fetchone():
            print(f"An account with {email} already exists. Nothing was changed.")
            return 1
        full_name = ask("Full name: ", bool, "Full name is required.")
        password = ask_password()

        db.execute(
            text("""
                INSERT INTO users (email, password_hash, role, full_name)
                VALUES (:email, :pw, 'admin', :name)
            """),
            {"email": email, "pw": hash_password(password), "name": full_name}
        )
        db.commit()
        print(f"Admin account created for {email}. Sign in at http://localhost:5173/admin/login")
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled. No account was created.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
