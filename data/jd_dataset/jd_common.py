"""
Shared helpers for the JD dataset scripts (ingest, analysis, gold sample).

The keyword matcher here is a simple baseline for dataset analysis only.
It is NOT the Sprint 3 NLP extractor (nlp/extractor.py) and must not be used
to create gold labels.
"""

import csv
import hashlib
import html
import re
import sys
from pathlib import Path

JD_DIR = Path(__file__).resolve().parent
REPO_ROOT = JD_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "data" / "skills"))
from skills_lib import load_skills  # noqa: E402

DATASET_PATH = JD_DIR / "jd_dataset.csv"
ROLE_SKILLS_SEED_PATH = REPO_ROOT / "database" / "seed_job_role_skills.sql"

DATASET_FIELDS = ["jd_ref", "role_code", "title", "company", "location", "seniority",
                  "source", "source_url", "source_license", "collected_date", "raw_text"]

ROLE_ABBR = {
    "DATA_ANALYST": "DA", "DATA_SCIENTIST": "DS", "SOFTWARE_DEV": "SD",
    "CYBER_ANALYST": "CY", "CLOUD_ENGINEER": "CE", "WEB_DEV": "WD",
}

# Title keyword rules, checked in this order (first match wins).
ROLE_TITLE_RULES = [
    ("CYBER_ANALYST", ["security", "cyber", "soc analyst", "penetration", "infosec", "pentest"]),
    ("CLOUD_ENGINEER", ["cloud", "devops", "site reliability", "sre", "platform engineer"]),
    ("DATA_SCIENTIST", ["data scientist", "machine learning", "ml engineer", "ai engineer", "data science"]),
    ("DATA_ANALYST", ["data analyst", "business intelligence", "bi analyst", "bi developer",
                      "reporting analyst", "analytics", "insights analyst"]),
    ("WEB_DEV", ["web developer", "frontend", "front-end", "front end", "full stack", "fullstack",
                 "full-stack", "react developer", "ui developer", "web engineer"]),
    ("SOFTWARE_DEV", ["software engineer", "software developer", "backend", "back-end", "back end",
                      "java developer", "python developer", "application developer", "programmer",
                      ".net developer", "software development"]),
]
# SEAGAS targets graduates, so senior / management postings are skipped.
SENIOR_WORDS = re.compile(r"\b(senior|sr\.?|lead|principal|manager|head|director|architect|staff|vp)\b", re.I)
ENTRY_WORDS = re.compile(r"\b(intern|internship|graduate|trainee|entry[- ]level|fresh(?:er|\s+grad)?)\b", re.I)
JUNIOR_WORDS = re.compile(r"\b(junior|jr\.?|associate)\b", re.I)


def classify_role(title):
    t = f" {title.lower()} "
    for code, words in ROLE_TITLE_RULES:
        for w in words:
            if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", t):
                return code
    return None


def classify_seniority(title, text=""):
    """entry / junior / mid, or 'senior' (skipped by ingest)."""
    if SENIOR_WORDS.search(title):
        return "senior"
    if ENTRY_WORDS.search(title):
        return "entry"
    if JUNIOR_WORDS.search(title):
        return "junior"
    if ENTRY_WORDS.search(text[:600]):
        return "entry"
    return "mid"


# ── Cleaning ───────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,4}\d{3,4}(?!\w)")


# "<Capitalised words> Sdn Bhd / Berhad / Pte Ltd / Ltd / Inc / Corp"
COMPANY_SUFFIX_RE = re.compile(
    r"\b(?:[A-Z][\w&.'-]*\s+){1,5}(?:Sdn\.?\s*Bhd\.?|Berhad|Bhd\.?|Pte\.?\s*Ltd\.?|Ltd\.?|Inc\.?|Corp(?:oration)?\.?)(?!\w)")


def clean_text(text, companies=()):
    """Strip HTML and remove emails, URLs, phone numbers and company names.

    `companies` is every company name known in the batch, so a company named in
    one posting is also removed from its re-posts that lack the company field.
    """
    t = html.unescape(text or "")
    t = re.sub(r"(?i)<\s*(br|/p|/li|/div|/h\d)\s*/?>", "\n", t)
    t = re.sub(r"(?i)<\s*li[^>]*>", "\n- ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = EMAIL_RE.sub("[EMAIL]", t)
    t = URL_RE.sub("[URL]", t)
    t = PHONE_RE.sub(lambda m: "[PHONE]" if sum(c.isdigit() for c in m.group()) >= 8 else m.group(), t)
    for company in sorted({c.strip() for c in companies if c and len(c.strip()) >= 3}, key=len, reverse=True):
        if company.lower() != "anonymised":
            t = re.sub(r"(?<!\w)" + re.escape(company) + r"(?!\w)", "[COMPANY]", t, flags=re.I)
    t = COMPANY_SUFFIX_RE.sub("[COMPANY]", t)
    t = t.replace("\r", "")
    t = re.sub(r"[ \t ]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"\n+- ", "\n- ", t)  # no blank lines between bullet points
    return t.strip()


def text_hash(text):
    norm = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.md5(norm.encode("utf-8")).hexdigest()


# ── Dataset I/O ────────────────────────────────────────────────────────────
def read_dataset(path=DATASET_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load_role_skills(path=ROLE_SKILLS_SEED_PATH):
    """{role_code: {skill_name: importance}} from seed_job_role_skills.sql."""
    sql = Path(path).read_text(encoding="utf-8")
    out = {}
    for code, skill, imp in re.findall(
            r"^\s*\('([A-Z_]+)',\s*'((?:[^']|'')+)',\s*'(required|preferred|bonus)'\)", sql, re.M):
        out.setdefault(code, {})[skill.replace("''", "'")] = imp
    return out


# ── Keyword skill matcher (baseline) ───────────────────────────────────────
class SkillMatcher:
    """Case-insensitive, word-bounded match of skill names + aliases.

    Ambiguous aliases (and skill names flagged as ambiguous, e.g. "Go", "R")
    are NOT used. Overlapping matches keep the longest term, so
    "security monitoring" counts as SOC, not also as "Monitoring".
    """

    def __init__(self, skills=None):
        skills = skills or load_skills()
        self.terms = []  # (term, skill_name)
        for s in skills:
            ambiguous = {a.lower() for a in s["ambiguous_aliases"]}
            for term in [s["skill_name"]] + s["aliases"]:
                if term.lower() in ambiguous:
                    continue
                self.terms.append((term, s["skill_name"]))
        self.terms.sort(key=lambda x: -len(x[0]))
        self.patterns = [
            (re.compile(r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#])", re.I), skill)
            for term, skill in self.terms
        ]

    def find(self, text):
        """Return [(start, end, matched_text, skill_name)] without overlaps."""
        taken = []
        hits = []
        for pat, skill in self.patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                if any(s < te and ts < e for ts, te in taken):
                    continue
                taken.append((s, e))
                hits.append((s, e, m.group(), skill))
        return sorted(hits)

    def skills_in(self, text):
        return {h[3] for h in self.find(text)}
