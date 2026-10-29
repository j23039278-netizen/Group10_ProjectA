"""
Shared helpers for the gold annotation tools (make_workbook.py,
collect_workbook.py, agreement.py).

These tools only move a person's labels between a workbook and CSV files and
check them. They never create labels themselves. See ANNOTATION_GUIDE.md.
"""

import csv
import random
import re
import sys
from pathlib import Path

GOLD_DIR = Path(__file__).resolve().parent
JD_DIR = GOLD_DIR.parent
sys.path.insert(0, str(JD_DIR))
from jd_common import REPO_ROOT, write_csv  # noqa: E402,F401
from skills_lib import CSV_PATH as SKILLS_PATH, load_skills  # noqa: E402,F401

SAMPLE_PATH = GOLD_DIR / "gold_sample.csv"
DRAFT_PATH = GOLD_DIR / "gold_labels_draft.csv"
LABELS_PATH = {"A": GOLD_DIR / "gold_labels.csv", "B": GOLD_DIR / "gold_labels_B.csv"}
WORKBOOK_PATH = {"A": GOLD_DIR / "gold_workbook.xlsx", "B": GOLD_DIR / "gold_workbook_B.xlsx"}

LABEL_FIELDS = ["jd_ref", "skill_name", "importance", "evidence_text"]
TABLE_COLUMNS = ["skill_name", "importance", "evidence_text", "keep", "note"]
IMPORTANCE = ["required", "preferred", "bonus"]           # strongest first
IMPORTANCE_RANK = {imp: i for i, imp in enumerate(IMPORTANCE)}  # lower = stronger
NEW_PREFIX = "NEW:"

B_PER_ROLE = 2
B_SEED = 42

# Typographic characters that Excel or a copy from a web page may introduce.
_PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                        "–": "-", "—": "-", " ": " "})


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm_text(text):
    """Lower case, plain punctuation, single spaces (for evidence look-up)."""
    return re.sub(r"\s+", " ", str(text or "").translate(_PUNCT).lower()).strip()


def skill_key(name):
    """Comparison key for a skill name ('NEW: DevOps' == 'new:  devops')."""
    return norm_text(name)


def evidence_in_text(evidence, text):
    """True if the evidence appears in the JD text, ignoring case and whitespace.

    A trailing '?' (the guide's "please discuss" marker) is ignored.
    """
    ev = norm_text(evidence).rstrip("?").strip()
    return bool(ev) and ev in norm_text(text)


def strongest(importances):
    return min(importances, key=lambda imp: IMPORTANCE_RANK[imp])


def pick_b_refs(sample_rows, per_role=B_PER_ROLE, seed=B_SEED):
    """The JDs annotator B labels: `per_role` per role, fixed by `seed`."""
    rng = random.Random(seed)
    refs = []
    for role in sorted({r["role_code"] for r in sample_rows}):
        pool = sorted(r["jd_ref"] for r in sample_rows if r["role_code"] == role)
        refs += sorted(rng.sample(pool, min(per_role, len(pool))))
    return refs


class Catalogue:
    """Canonical skill names plus an alias index for "did you mean" hints."""

    def __init__(self, skills=None):
        skills = skills if skills is not None else load_skills()
        self.names = sorted((s["skill_name"] for s in skills), key=str.lower)
        self.by_key = {skill_key(n): n for n in self.names}
        self.alias_to_name = {}
        for s in skills:
            for alias in s.get("aliases", []) + s.get("ambiguous_aliases", []):
                self.alias_to_name.setdefault(skill_key(alias), s["skill_name"])

    def lookup(self, term):
        """Canonical name for a name or alias of a library skill, else None."""
        key = skill_key(term)
        return self.by_key.get(key) or self.alias_to_name.get(key)
