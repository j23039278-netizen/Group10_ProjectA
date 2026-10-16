"""
SEAGAS — Make sure backend/.env has a private SECRET_KEY

Login tokens are signed with SECRET_KEY. Older versions of start_backend.bat
wrote the same fixed key into everyone's .env, and that key is public (it is
in git), so anyone could forge a token. This script, run by start_backend.bat,
gives .env a random key when it has none or still has the old public one.
Changing the key only means users have to sign in again.

Usage (from the backend folder):  python ensure_secret_key.py
"""

import secrets
from pathlib import Path

ENV = Path(__file__).resolve().parent / ".env"
OLD_PUBLIC_KEYS = {"seagas_super_secret_key_change_in_production_2026", "fallback_secret"}


def main():
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    current = next((l.split("=", 1)[1].strip() for l in lines if l.startswith("SECRET_KEY=")), "")
    if current and current not in OLD_PUBLIC_KEYS:
        print("      SECRET_KEY ok")
        return
    new_line = "SECRET_KEY=" + secrets.token_urlsafe(48)
    lines = [l for l in lines if not l.startswith("SECRET_KEY=")] + [new_line]
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("      SECRET_KEY replaced with a new random key (please sign in again)"
          if current else "      SECRET_KEY created")


if __name__ == "__main__":
    main()
