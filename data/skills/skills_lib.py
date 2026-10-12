"""
Shared loader + validator for data/skills/skills_library.csv.

The CSV is the single source of truth for the SEAGAS skills library.
Used by build_skills_seed.py, generate_synthetic_data.py, the JD analysis
scripts and tests/test_skills_library.py.
"""

import csv
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILLS_DIR.parent.parent
CSV_PATH = SKILLS_DIR / "skills_library.csv"
SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"

VALID_CATEGORIES = {"Technical", "AI_Digital", "Analytical", "Soft"}
MIN_SKILLS, MAX_SKILLS = 120, 150
MAX_NAME_LEN = 100  # skills_library.skill_name VARCHAR(100)


def _split(value):
    return [v.strip() for v in (value or "").split("|") if v.strip()]


def load_skills(path=CSV_PATH):
    """Return a list of dicts; aliases / ambiguous_aliases are lists."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["skill_name"] = r["skill_name"].strip()
        r["aliases"] = _split(r.get("aliases"))
        r["ambiguous_aliases"] = _split(r.get("ambiguous_aliases"))
    return rows


def load_v1_skill_names(schema_path=SCHEMA_PATH):
    """The 32 skill names seeded by schema.sql (read-only; schema.sql is owned by Carl)."""
    text = Path(schema_path).read_text(encoding="utf-8")
    start = text.index("INSERT INTO skills_library")
    block = text[start:text.index(";\n", start)]
    return re.findall(r"^\s*\('((?:[^']|'')+)'\s*,", block, re.M)


def validate(rows, v1_names=None):
    """Return a list of human-readable problems (empty list == valid)."""
    problems = []
    seen_names = {}
    for r in rows:
        key = r["skill_name"].lower()
        if key in seen_names:
            problems.append(f"duplicate skill_name: {r['skill_name']!r}")
        seen_names[key] = r["skill_name"]
        if r["category"] not in VALID_CATEGORIES:
            problems.append(f"{r['skill_name']}: invalid category {r['category']!r}")
        if not r.get("description", "").strip():
            problems.append(f"{r['skill_name']}: missing description")
        if len(r["skill_name"]) > MAX_NAME_LEN:
            problems.append(f"{r['skill_name']}: skill_name longer than {MAX_NAME_LEN}")
        if r.get("source") not in {"v1", "v2"}:
            problems.append(f"{r['skill_name']}: source must be v1 or v2")

    # every alias (incl. ambiguous ones) must belong to exactly one skill
    # and must not equal any skill_name. Exception: an ambiguous alias may equal
    # the skill's OWN name (e.g. "R"), flagging that the name itself is ambiguous.
    owner = {}
    for r in rows:
        own = r["skill_name"].lower()
        for a in r["aliases"] + r["ambiguous_aliases"]:
            key = a.strip().lower()
            if key == own and a in r["ambiguous_aliases"]:
                continue
            if key in seen_names:
                problems.append(f"{r['skill_name']}: alias {a!r} equals skill_name {seen_names[key]!r}")
            if key in owner and owner[key] != r["skill_name"]:
                problems.append(f"alias {a!r} used by both {owner[key]!r} and {r['skill_name']!r}")
            elif key in owner:
                problems.append(f"{r['skill_name']}: alias {a!r} listed twice")
            owner[key] = r["skill_name"]

    if not MIN_SKILLS <= len(rows) <= MAX_SKILLS:
        problems.append(f"skill count {len(rows)} outside {MIN_SKILLS}-{MAX_SKILLS}")

    if v1_names is not None:
        names = {r["skill_name"] for r in rows}
        for n in v1_names:
            if n not in names:
                problems.append(f"v1 skill missing or renamed: {n!r}")
    return problems
