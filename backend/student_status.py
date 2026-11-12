"""
SEAGAS — Student status on the advisor dashboard (who needs the advisor's attention)

A low readiness score alone does not mean a student needs support: a Year 1 student
naturally has few skills, and a student who is working on recommended activities is
already acting on the result. So the status compares the latest readiness score with
what is expected for the student's year of study, and "Needs Support" is kept for
students who are below that expectation AND have not been active recently.

  On Track         score >= the year's On Track limit
  Developing       between the year's two limits
  Getting Started  below the year's lower limit, but a new Year 1 student (account younger
                   than one semester); older students whose account is new (e.g. when the
                   system is first introduced) are not counted as new
  Improving        below the year's lower limit, but active recently (an activity saved,
                   started or completed, or the score went up at the latest assessment)
  Needs Support    below the year's lower limit, not new and not active recently
  Not Assessed     no assessment yet

The limits per year, the "recently" window and the new-student period are System
Settings (backend/settings.py): year_expectations, support_active_days, new_student_days.
Year 4 and above, and students without a year, use readiness_on_track / readiness_needs_support.
"""

from datetime import datetime, timedelta

import settings

STATUSES = ("on_track", "developing", "getting_started", "improving", "needs_support", "none")


def config(db):
    """The status rules from System Settings"""
    v = settings.get_all(db)
    return {
        "years":       {int(k): (int(on), int(need)) for k, (on, need) in v["year_expectations"].items()},
        "default":     (int(v["readiness_on_track"]), int(v["readiness_needs_support"])),
        "active_days": int(v["support_active_days"]),
        "new_days":    int(v["new_student_days"]),
    }


def public_rules(cfg):
    """The rules as the advisor dashboard shows them"""
    return {"years": {str(y): {"on_track": on, "needs_support": need} for y, (on, need) in sorted(cfg["years"].items())},
            "default": {"on_track": cfg["default"][0], "needs_support": cfg["default"][1]},
            "active_days": cfg["active_days"], "new_days": cfg["new_days"]}


def limits(cfg, year):
    """(On Track from, Needs Support below) for a year of study"""
    try:
        return cfg["years"].get(int(year), cfg["default"]) if year is not None else cfg["default"]
    except (TypeError, ValueError):
        return cfg["default"]


def _year_text(cfg, year):
    if year is None:
        return "students without a year of study"
    y = int(year)
    return f"Year {y}" if y in cfg["years"] else f"Year {y}"


def classify(row, cfg, now=None):
    """(status, reason) for one student. row needs latest_score, year_of_study,
    account_created, last_activity_at, last_assessed and previous_score."""
    now = now or datetime.now()
    score = row.get("latest_score")
    if score is None:
        return "none", "No assessment yet."
    score = float(score)
    year = row.get("year_of_study")
    on, need = limits(cfg, year)
    who = _year_text(cfg, year)
    if score >= on:
        return "on_track", f"At or above the On Track level for {who} ({on}%)."
    if score >= need:
        return "developing", f"Between {need}% and {on}%, the expected range for {who}."

    created = row.get("account_created")
    first_year = year is None or int(year) <= 1
    if first_year and created is not None and created >= now - timedelta(days=cfg["new_days"]):
        return "getting_started", (f"New Year 1 student (account created {created:%d/%m/%Y}): a low score is expected "
                                   f"in the first semester (below {need}% for {who}).")

    recent = now - timedelta(days=cfg["active_days"])
    last_activity = row.get("last_activity_at")
    previous = row.get("previous_score")
    assessed = row.get("last_assessed")
    if previous is not None and float(previous) < score and assessed is not None and assessed >= recent:
        return "improving", (f"Below {need}% (expected for {who}), but the score went up from "
                             f"{float(previous):g}% to {score:g}% at the latest assessment.")
    if last_activity is not None and last_activity >= recent:
        days = max(0, (now - last_activity).days)
        when = "today" if days == 0 else f"{days} day{'' if days == 1 else 's'} ago"
        return "improving", f"Below {need}% (expected for {who}), but working on recommended activities (last {when})."
    return "needs_support", (f"Below {need}% (expected for {who}) and no learning activity "
                             f"in the last {cfg['active_days']} days.")


# Columns the status needs, for a query over users u / student_profiles sp / latest assessment a
STATUS_COLUMNS = """
    u.created_at AS account_created,
    (SELECT MAX(GREATEST(srp.created_at, srp.started_at, srp.completed_at, srp.updated_at))
       FROM student_resource_progress srp WHERE srp.profile_id = sp.profile_id) AS last_activity_at,
    (SELECT prev.readiness_score FROM assessments prev
      WHERE prev.profile_id = sp.profile_id ORDER BY prev.created_at DESC OFFSET 1 LIMIT 1) AS previous_score
"""
