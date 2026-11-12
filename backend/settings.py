"""
SEAGAS — System settings (FR-16): values an admin can change in Admin → System Settings

Stored in the system_settings table (key -> JSON value); a key that is not stored
uses its default here. Mail-server settings and passwords stay in backend/.env and
are never stored or shown here.

Used by: students.py (semester start dates for the GPA / CGPA reminder),
advisor.py and student_status.py (readiness bands and who needs support),
evidence.py and cv.py (upload limits).
"""

import re

from fastapi import HTTPException
from sqlalchemy import text

# The database caps evidence files and CVs at 5 MB (chk_evidence_kind, student_cvs),
# so the upload limit can only be lowered.
HARD_MAX_MB = 5
MMDD = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")

DEFINITIONS = {
    "semester_starts": {
        "default": ["01-01", "05-01", "09-01"],
        "label": "Semester start dates",
        "help": "Month-day (MM-DD) of each intake. From these dates students are reminded to update their GPA and CGPA.",
    },
    "readiness_on_track": {
        "default": 70, "min": 1, "max": 100,
        "label": "On Track from (readiness %), Year 4 and above",
        "help": "Year 4+ students (and students without a year) whose latest readiness score is at least this are On Track.",
    },
    "readiness_needs_support": {
        "default": 40, "min": 0, "max": 99,
        "label": "Below expected under (readiness %), Year 4 and above",
        "help": "Year 4+ students below this score are below the expected level. Between the two limits: Developing.",
    },
    "year_expectations": {
        "default": {"1": [45, 20], "2": [55, 30], "3": [65, 35]},
        "label": "Expected readiness by year of study",
        "help": "On Track from / below-expected limit for Years 1 to 3. New students naturally have fewer skills, "
                "so they are compared with what is expected for their year.",
    },
    "support_active_days": {
        "default": 30, "min": 7, "max": 180,
        "label": "Counts as improving for (days)",
        "help": "A student below the expected level is shown as Improving, not Needs Support, if they worked on a "
                "recommended activity or raised their score within this many days.",
    },
    "new_student_days": {
        "default": 120, "min": 0, "max": 365,
        "label": "New student period (days)",
        "help": "A Year 1 student whose account is younger than this is shown as Getting Started, not Needs Support "
                "(about one semester). 0 turns this off.",
    },
    "max_upload_mb": {
        "default": 5, "min": 1, "max": HARD_MAX_MB,
        "label": "Largest upload (MB)",
        "help": f"Largest evidence file or CV a student can upload (at most {HARD_MAX_MB} MB).",
    },
    "max_evidence_per_item": {
        "default": 5, "min": 1, "max": 10,
        "label": "Evidence per item",
        "help": "Most files and links a student can attach to one project, certification or activity.",
    },
}


def get_all(db):
    """Every setting: the stored value, or the default"""
    values = {k: d["default"] for k, d in DEFINITIONS.items()}
    for r in db.execute(text("SELECT key, value FROM system_settings")).fetchall():
        if r.key in values:
            values[r.key] = r.value
    return values


def get(db, key):
    return get_all(db)[key]


def max_upload_bytes(db):
    return int(get(db, "max_upload_mb")) * 1024 * 1024


def semester_starts(db):
    """((month, day), ...) in calendar order"""
    return tuple(sorted(tuple(int(x) for x in s.split("-")) for s in get(db, "semester_starts")))


def validate(changes, current):
    """Checked new values (400 with the reason otherwise)"""
    out = {}
    for key, value in changes.items():
        d = DEFINITIONS.get(key)
        if d is None:
            raise HTTPException(status_code=400, detail=f"Unknown setting: {key}")
        if key == "year_expectations":
            if not isinstance(value, dict) or set(value) != {"1", "2", "3"}:
                raise HTTPException(status_code=400, detail="Give the expected readiness for Years 1, 2 and 3.")
            years = {}
            for y in ("1", "2", "3"):
                pair = value[y]
                if (not isinstance(pair, list) or len(pair) != 2
                        or any(isinstance(n, bool) or not isinstance(n, (int, float)) or int(n) != n for n in pair)):
                    raise HTTPException(status_code=400, detail=f"Year {y}: give two whole numbers (On Track from, below-expected under).")
                on, need = int(pair[0]), int(pair[1])
                if not (0 <= need < on <= 100):
                    raise HTTPException(status_code=400, detail=f"Year {y}: the lower limit must be below the On Track limit (0-100).")
                years[y] = [on, need]
            out[key] = years
            continue
        if key == "semester_starts":
            if not isinstance(value, list) or not 1 <= len(value) <= 6:
                raise HTTPException(status_code=400, detail="Give between 1 and 6 semester start dates.")
            days = sorted({str(v).strip() for v in value})
            for v in days:
                if not MMDD.match(v) or v in ("02-30", "02-31", "04-31", "06-31", "09-31", "11-31"):
                    raise HTTPException(status_code=400, detail=f"{v} is not a date in MM-DD form, e.g. 09-01.")
            out[key] = days
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
                raise HTTPException(status_code=400, detail=f"{d['label']} must be a whole number.")
            if not d["min"] <= value <= d["max"]:
                raise HTTPException(status_code=400, detail=f"{d['label']} must be between {d['min']} and {d['max']}.")
            out[key] = int(value)
    merged = {**current, **out}
    if merged["readiness_needs_support"] >= merged["readiness_on_track"]:
        raise HTTPException(status_code=400, detail="The below-expected limit must be lower than the On Track limit.")
    return out
