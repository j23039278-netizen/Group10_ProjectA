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

DATASET_FIELDS = ["jd_ref", "role_code", "title", "company", "location", "region", "seniority",
                  "source", "source_url", "source_license", "collected_date", "raw_text"]

ROLE_ABBR = {
    "DATA_ANALYST": "DA", "DATA_SCIENTIST": "DS", "SOFTWARE_DEV": "SD",
    "CYBER_ANALYST": "CY", "CLOUD_ENGINEER": "CE", "WEB_DEV": "WD",
    "BUSINESS_ANALYST": "BA", "FINANCIAL_ANALYST": "FA", "HR_EXEC": "HR", "MARKETING_EXEC": "MK",
}

# Title keyword rules, checked in this order (first match wins).
# - BUSINESS_ANALYST and FINANCIAL_ANALYST come first: their phrases name the job
#   ("IT Business Analyst", "Cloud Financial Analyst"). "Business intelligence
#   analyst" and "business data analyst" do not contain "business analyst", so they
#   stay DATA_ANALYST. "Financial reporting analyst" is FINANCIAL_ANALYST (it must
#   beat "reporting analyst"), while "financial data analyst" is deliberately
#   DATA_ANALYST: its head noun is "data analyst" and the work is SQL / BI on
#   finance data, not budgeting or forecasting.
# - Recruiter titles often name the field they hire for ("Technical Recruiter -
#   Cloud"), so they come before the IT rules. Other HR and marketing titles come
#   last, so "HR Data Analyst" and "Marketing Analytics Specialist" stay DATA_ANALYST.
ROLE_TITLE_RULES = [
    ("BUSINESS_ANALYST", ["business analyst", "business systems analyst", "business system analyst",
                          "business process analyst", "business analysis"]),
    ("FINANCIAL_ANALYST", ["financial analyst", "finance analyst", "fp&a", "financial planning analyst",
                           "financial planning and analysis", "financial planning & analysis",
                           "financial reporting analyst", "budget analyst"]),
    ("HR_EXEC", ["recruiter", "recruiting coordinator", "recruitment", "talent acquisition"]),
    ("CYBER_ANALYST", ["security", "cyber", "cybersecurity", "soc analyst", "penetration", "infosec", "pentest"]),
    ("CLOUD_ENGINEER", ["cloud", "devops", "site reliability", "sre", "platform engineer"]),
    ("DATA_SCIENTIST", ["data scientist", "machine learning", "ml engineer", "ai engineer", "data science"]),
    ("DATA_ANALYST", ["data analyst", "business intelligence", "bi analyst", "bi developer",
                      "reporting analyst", "analytics", "insights analyst"]),
    ("WEB_DEV", ["web developer", "frontend", "front-end", "front end", "full stack", "fullstack",
                 "full-stack", "react developer", "ui developer", "web engineer"]),
    ("SOFTWARE_DEV", ["software engineer", "software developer", "backend", "back-end", "back end",
                      "java developer", "python developer", "application developer", "programmer",
                      ".net developer", "software development"]),
    ("HR_EXEC", ["hr", "hris", "human resources", "human resource", "people operations", "people partner"]),
    ("MARKETING_EXEC", ["marketing executive", "marketing coordinator", "marketing specialist",
                        "marketing assistant", "marketing associate", "marketing intern", "marketing internship",
                        "marketing officer", "marketing analyst", "marketing generalist",
                        "marketing communications", "digital marketing", "social media", "content marketing",
                        "seo specialist", "seo executive", "brand executive", "brand coordinator"]),
]

# Some keywords are too broad on their own. They only count when the title also
# matches the context pattern: bare "security" must look like IT security (so
# "Security Officer" and "Armed Security Guard" are skipped, while "Information
# System Security Officer" stays CYBER_ANALYST), and "front end" must look like
# development (US retail uses "Front End Supervisor" for the checkout area).
KEYWORD_CONTEXT = {
    "security": re.compile(
        r"\b(?:information|info|it|ict|cyber|network|computer|application|app|cloud|data|soc|isso|issm|iam|"
        r"identity|email|siem|software|devsecops|vulnerability|threat|incident|blockchain|sap|"
        r"analyst|engineer|engineering|developer|researcher|tester|administrator|operations center)\b", re.I),
    **{w: re.compile(r"\b(?:developer|engineer|engineering|software|web|ui|react|angular|vue|javascript|"
                     r"typescript|dev)\b", re.I) for w in ("frontend", "front-end", "front end")},
}
# Titles that match a role's keyword but are not that job.
ROLE_TITLE_EXCLUDE = {
    # "Retail Sales Print & Marketing Associate", "Sales and Marketing Representative"
    "MARKETING_EXEC": re.compile(r"\b(?:sales|retail|door[- ]to[- ]door)\b", re.I),
    # "Associate Client Advisor - Cyber" (cyber insurance)
    "CYBER_ANALYST": re.compile(r"\b(?:insurance|underwrit\w*|claims|client advisor|broker)\b", re.I),
    # "HVAC Programmer", "Machinist/Programmer", "Computer Numerical Control Programmer"
    "SOFTWARE_DEV": re.compile(r"\b(?:hvac|cnc|plc|machinist|manufacturing|numerical control)\b", re.I),
    # "LVN - HR Employee Occupational Health"
    "HR_EXEC": re.compile(r"\blvn\b", re.I),
    # "Online Data Analyst" is a search / maps rating gig (no SQL, Excel or BI work)
    "DATA_ANALYST": re.compile(r"\bonline data analyst\b", re.I),
}
# Titles that are never one of the target jobs ("Volunteer: Finance Coordinator
# needed for Cyber Defense Center", "Assistant Teaching Professor in Business
# Analytics", "Enterprise Cloud Sales Representative", "Talent Acquisition Sales Representative").
NON_TARGET_TITLE_RE = re.compile(
    r"\b(?:volunteer|professor|faculty|lecturer|teacher|instructor|account executive"
    r"|sales (?:representative|rep|associate|executive|specialist|consultant|engineer))\b", re.I)
# Phrases removed from a title before matching: the part after "for" / "with" /
# "supporting" ("Jr. Python Developer for Cyber Program", "Data Analyst Supporting
# the FBI"), clearance wording, product and place names ("Salesforce Marketing
# Cloud", "Teller St Cloud South") and pay or shift rates ("$26.00/hr", "Operator 12-hr").
TITLE_NOISE_RE = re.compile(
    r"\s(?:for|with|supporting)\s.*$"
    r"|\b(?:(?:with|requires?|active|ts/sci|top secret|secret)\s+)*security clearance\b"
    r"|\bclearance required\b|\b(?:social|national|homeland) security\b"
    r"|\b(?:salesforce\s+)?(?:marketing|sales|service|commerce|ecommerce|experience|health|analytics) cloud\b"
    r"|\b(?:oracle|genesys|workday|netsuite) cloud\b|\bst\.?\s+cloud\b"
    r"|\$?\s*\d[\d,.]*\s*(?:/|-|per|an|a)?\s*(?:hr|hour|yr|year)s?\b|\$\s*\d[\d,.]*k?|/\s*hr\b|\bper\s+hr\b", re.I)
# SEAGAS targets graduates, so senior / management postings are skipped.
SENIOR_WORDS = re.compile(
    r"\b(senior|sr\.?|lead|principal|manager|mgr|head|director|architect|staff|vp|avp|svp|evp|chief|president|leader|supervisor)\b",
    re.I)
ENTRY_WORDS = re.compile(r"\b(intern|internship|graduate|trainee|entry[- ]level|fresh(?:er|\s+grad)?)\b", re.I)
JUNIOR_WORDS = re.compile(r"\b(junior|jr\.?|associate)\b", re.I)


def classify_role(title):
    t = f" {TITLE_NOISE_RE.sub(' ', title.lower())} "
    if NON_TARGET_TITLE_RE.search(t):
        return None
    for code, words in ROLE_TITLE_RULES:
        if code in ROLE_TITLE_EXCLUDE and ROLE_TITLE_EXCLUDE[code].search(t):
            continue
        for w in words:
            if not re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", t):
                continue
            context = KEYWORD_CONTEXT.get(w)
            if context and not context.search(t.replace(w, " ")):
                continue
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


# Experience-level column of some Kaggle files (LinkedIn: "Internship", "Entry level",
# "Associate", "Mid-Senior level", "Director", "Executive"). "Mid-Senior level"
# is left to the title rules because LinkedIn uses it for most mid-level jobs.
LEVEL_SENIORITY = {"internship": "entry", "entry level": "entry", "entry-level": "entry",
                   "associate": "junior", "director": "senior", "executive": "senior"}


def combine_seniority(title_seniority, level):
    """Title rules first (a senior title is always skipped, an intern title is
    always entry); the experience-level column only refines a plain 'mid' title."""
    level_seniority = LEVEL_SENIORITY.get((level or "").strip().lower())
    if title_seniority == "senior" or level_seniority == "senior":
        return "senior"
    if title_seniority == "mid" and level_seniority:
        return level_seniority
    return title_seniority


# ── Region (for the JD-bias report) ────────────────────────────────────────
REGIONS = ["Malaysia", "other APAC", "remote", "other"]
MALAYSIA_RE = re.compile(
    r"\b(?:malaysia|kuala lumpur|selangor|penang|pulau pinang|johor|johor bahru|petaling jaya|cyberjaya|"
    r"putrajaya|shah alam|subang|puchong|klang|bangsar|mont kiara|sabah|kota kinabalu|sarawak|kuching|"
    r"melaka|malacca|perak|ipoh|kedah|negeri sembilan|seremban|pahang|kuantan|terengganu|kelantan|"
    r"perlis|labuan)\b", re.I)
APAC_RE = re.compile(
    r"\b(?:apac|asia|asia pacific|singapore|indonesia|jakarta|thailand|bangkok|vietnam|viet nam|hanoi|"
    r"ho chi minh|philippines|manila|cebu|india|bangalore|bengaluru|mumbai|new delhi|gurgaon|gurugram|noida|"
    r"hyderabad|pune|chennai|kolkata|china|shanghai|beijing|shenzhen|guangzhou|hong kong|taiwan|taipei|"
    r"japan|tokyo|osaka|korea|seoul|australia|sydney|new zealand|auckland|sri lanka|"
    r"colombo|bangladesh|dhaka|pakistan|karachi|lahore|nepal|cambodia|myanmar|brunei|macau|mongolia)\b", re.I)
REMOTE_RE = re.compile(r"\b(?:remote|anywhere|worldwide|work from home|wfh)\b", re.I)
# Cities that are also US towns (Melbourne, Brisbane, Delhi) are left out of APAC_RE;
# "Sydney, NS"-style locations end in a two-letter region code and count as other.
US_RE = re.compile(r"\bunited states\b|\busa?\b|,\s*[A-Z]{2}(?:\s+\d{5})?\s*$")


def region_of(location):
    """Malaysia / other APAC / remote / other, from the location text only.
    A Malaysian or APAC place wins over "remote" ("Remote, Malaysia" is Malaysia)."""
    loc = location or ""
    if MALAYSIA_RE.search(loc):
        return "Malaysia"
    if APAC_RE.search(loc) and not US_RE.search(loc):
        return "other APAC"
    if REMOTE_RE.search(loc):
        return "remote"
    return "other"


# ── Cleaning ───────────────────────────────────────────────────────────────
# "jobs@acme.example", and a bare e-mail domain ("only from @acme.example addresses")
EMAIL_RE = re.compile(r"(?:[\w.+-]+)?@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"(?:https?:?\s?//|www\.)\S+", re.I)
# Social-media handles ("follow @AcmeCorp") name the employer.
HANDLE_RE = re.compile(r"(?<![\w.\[])@[A-Za-z_]\w{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,4}\d{3,4}(?!\w)")


# "<Capitalised words> Sdn Bhd / Berhad / Pte Ltd / Ltd / Inc / Corp"
COMPANY_SUFFIX_RE = re.compile(
    r"\b(?:[A-Z][\w&.'-]*\s+){1,5}(?:Sdn\.?\s*Bhd\.?|Berhad|Bhd\.?|Pte\.?\s*Ltd\.?|Ltd\.?|Inc\.?|Corp(?:oration)?\.?)(?!\w)")
LEGAL_SUFFIX_RE = re.compile(
    r"[\s,]*\b(?:Sdn\.?\s*Bhd\.?|Berhad|Bhd\.?|P[ty][ey]\.?\s*Ltd\.?|Ltd\.?|Inc\.?|Corp(?:oration)?\.?|LLC|PLC)\s*$", re.I)

# Employer blurb ("About the company" / "About us"), usually the last section of
# JobStreet postings. It names the employer and lists no job requirements, so it
# is removed up to the next "Perks and benefits:" / "Key Highlights" line or the end.
ABOUT_COMPANY_RE = re.compile(
    r"(?ims)^[ \t]*about (?:the company|our company|us)[ \t]*:?[ \t]*\r?\n"
    r".*?(?=^[ \t]*(?:perks and benefits:|key highlights\b)|\Z)")


def company_variants(name):
    """The name plus its core form, e.g. "DXC Technology Malaysia Sdn Bhd." ->
    {"DXC Technology Malaysia Sdn Bhd.", "DXC Technology Malaysia", "DXC Technology"}."""
    name = (name or "").strip()
    core = re.sub(r"\([^)]*\)", " ", name)  # "(M)", "(Malaysia)", "(Gen Digital Inc.)"
    prev = None
    while prev != core:
        prev = core
        core = LEGAL_SUFFIX_RE.sub("", core).strip(" ,.")
    core = re.sub(r"\s+", " ", core)
    short = re.sub(r"\s+(?:Malaysia|Group)$", "", core, flags=re.I)
    return {v for v in (name, core, short) if len(v) >= 3}


# Words that appear in many employer names but say nothing about the employer
# (or are skills / job words), so brand_words() never masks them on their own.
GENERIC_NAME_WORDS = set("""
the and of at for a an by on in to inc llc ltd corp corporation company companies co cie et group holdings
international global worldwide systems solutions services service technologies technology tech consulting
consultants partners partner health healthcare medical hospital insurance life financial finance bank
banking credit union energy resources resource university college school institute state county city
department national american america north south east west new york united states u.s us usa federal
career careers connections staffing recruiting recruitment talent network job jobs search products product
business process research laboratory laboratories lab media studios pictures entertainment express
aviation risk wealth court superior family region fleet readiness first true red blue green applied
digital management data cloud software security marketing analytics engineering design creative
professional professionals productions equipment diagnostics construction line association division
community mobility capital office retail logistics manufacturing industries industry enterprises
enterprise agency foundation trust care home homes center centre labs ventures innovation innovations
government public private people human hr it ai of
""".split())


def brand_words(name):
    """Distinctive single words of an employer name, e.g. "Apex Systems" -> {"Apex"},
    "Alaska Native Tribal Health Consortium (ANTHC)" -> {"Alaska", "Native", "Tribal",
    "Consortium", "ANTHC"}. Used for Kaggle rows, whose texts often use the short brand."""
    words = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9&'+]*[A-Za-z0-9]", name or ""):
        if len(w) >= 3 and w[0].isupper() and w.lower().strip("'") not in GENERIC_NAME_WORDS:
            words.add(w)
    return words


def mask_words(text, words):
    """Replace each word (case-sensitive, whole word) with [COMPANY]."""
    for w in sorted(words, key=len, reverse=True):
        text = re.sub(r"(?<![\w\[])" + re.escape(w) + r"(?![\w\]])", "[COMPANY]", text)
    return text


def mask_companies(text, companies=()):
    """Replace every known company name (longest first) with [COMPANY]."""
    t = text
    for company in sorted({c.strip() for c in companies if c and len(c.strip()) >= 3}, key=len, reverse=True):
        if company.lower() != "anonymised":
            t = re.sub(r"(?<!\w)" + re.escape(company) + r"(?!\w)", "[COMPANY]", t, flags=re.I)
    return t


def clean_text(text, companies=()):
    """Strip HTML, drop the employer blurb and remove emails, URLs, phone numbers
    and company names.

    `companies` is every company name known in the batch, so a company named in
    one posting is also removed from its re-posts that lack the company field.
    """
    t = html.unescape(text or "")
    t = re.sub(r"(?i)<\s*(br|/p|/li|/div|/h\d)\s*/?>", "\n", t)
    t = re.sub(r"(?i)<\s*li[^>]*>", "\n- ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = ABOUT_COMPANY_RE.sub("", t)
    t = EMAIL_RE.sub("[EMAIL]", t)
    t = re.sub(r"(?:\[EMAIL\])+", "[EMAIL]", t)
    t = URL_RE.sub("[URL]", t)
    t = HANDLE_RE.sub("[URL]", t)
    t = PHONE_RE.sub(lambda m: "[PHONE]" if sum(c.isdigit() for c in m.group()) >= 8 else m.group(), t)
    t = mask_companies(t, companies)
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
