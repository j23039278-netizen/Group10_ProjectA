"""
SEAGAS — What the order of the recommendations is worth on the Job Readiness Score

Reads the latest role-template assessment of every active student and compares the old
order (gap, developing, skill name) with the order in recommendation/engine.py, and shows
what first_steps offers. Uses the engine's functions, with each student's own completed
resources. Also checks every stored assessment: sum(points x credit) = readiness_score.
Nothing is written. Results and limits: docs/JOB_READINESS_SCORE.md, section 8.

The gains are arithmetic on the score, on synthetic students. They do not show that a
student learned a skill or became more employable.

    python data/rec_order_effect.py

Needs the importance column of skill_match_results: start_backend.bat adds it, or run
database/migrate_existing_db.sql.
"""
import sys
from pathlib import Path
from statistics import mean, median

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import text  # noqa: E402
from database import SessionLocal  # noqa: E402  (reads backend/.env)
from readiness import STATUS_CREDIT, skill_points  # noqa: E402
from recommendation import engine  # noqa: E402

TOLERANCE = 0.02   # readiness_score is stored rounded to 2 decimals
TOP = 3
OLD, NEW = "old order", "new order"


def old_key(skill):
    """The order before importance: gap, developing, then skill name. It came from SQL ORDER BY,
    which here ignores case, so casefold gives the same order for all 172 skills."""
    return engine.GAP_TYPE_PRIORITY[skill["gap_type"]], skill["skill_name"].casefold()


def share(part, whole):
    return 100 * part / whole if whole else 0.0


def reproduces(rows, stored):
    points = skill_points(rows)
    earned = sum(points[r["importance"]] * STATUS_CREDIT[r["match_status"]] for r in rows)
    return abs(earned - float(stored)) <= TOLERANCE


class Order:
    """The figures of one order of the skills, added to one student at a time."""

    def __init__(self):
        self.top = self.top_required = self.students_with_required = self.with_required_on_top = 0
        self.positions, self.strong_gains, self.first_resource_gains = [], [], []

    def add(self, skills, first_resource_gain):
        top = skills[:TOP]
        required_on_top = sum(s["importance"] == "required" for s in top)
        self.top += len(top)
        self.top_required += required_on_top
        positions = [i for i, s in enumerate(skills, start=1) if s["importance"] == "required"]
        if positions:
            self.students_with_required += 1
            self.with_required_on_top += required_on_top > 0
            self.positions.append(positions[0])
        self.strong_gains.append(sum(s["expected_gain"] for s in top))
        self.first_resource_gains.append(sum(first_resource_gain(s) for s in top))

    def lines(self):
        return [
            ("Required share of the first three", f"{share(self.top_required, self.top):.1f}%"),
            ("Students with a required skill to do, one in the first three",
             f"{share(self.with_required_on_top, self.students_with_required):.1f}%"),
            ("Median position of the first required skill", f"{median(self.positions):g}"),
            ("Gain if all three reach Strong, mean / median",
             f"+{mean(self.strong_gains):.1f} / +{median(self.strong_gains):.1f}"),
            ("Gain from completing the first resource of each, mean / median",
             f"+{mean(self.first_resource_gains):.1f} / +{median(self.first_resource_gains):.1f}"),
        ]


def latest_assessments(db):
    """Assessments of active students, newest first per profile"""
    return db.execute(text("""
        SELECT a.assessment_id, a.profile_id, a.role_id, a.jd_id, a.created_at, a.readiness_score, u.is_active
        FROM assessments a
        JOIN student_profiles p ON p.profile_id = a.profile_id
        JOIN users u ON u.user_id = p.user_id
        ORDER BY a.profile_id, a.created_at DESC, a.assessment_id
    """)).fetchall()


def main():
    db = SessionLocal()
    try:
        if not db.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name = 'skill_match_results' "
                               "AND column_name = 'importance'")).first():
            sys.exit("skill_match_results has no importance column yet. Run database/migrate_existing_db.sql first.")

        orders = {OLD: Order(), NEW: Order()}
        steps_shown = steps_required = steps_paid = students = 0
        steps_gains, resources, seen = [], {}, set()
        checked, not_reproduced, null_rows, total_rows = 0, 0, 0, 0

        def active_resources(skill_id):
            if skill_id not in resources:
                resources[skill_id] = engine.ranked_resources(skill_id, db)
            return resources[skill_id]

        def first_resource_gain(skill):
            ranked = active_resources(skill["skill_id"])
            return engine.gain_if_completed(skill["points"], skill["gap_type"], ranked[0]) if ranked else 0

        for a in latest_assessments(db):
            rows = engine.load_match_rows(db, a.assessment_id)
            checked += 1
            not_reproduced += not reproduces(rows, a.readiness_score)
            if not a.role_id or not a.is_active or a.profile_id in seen:
                continue
            seen.add(a.profile_id)
            students += 1
            skills = engine.skills_to_do(rows)
            orders[OLD].add(sorted(skills, key=old_key), first_resource_gain)
            orders[NEW].add(skills, first_resource_gain)
            by_skill = {s["skill_id"]: engine.with_gains(active_resources(s["skill_id"]), s) for s in skills}
            steps = engine.first_steps(skills, by_skill, engine.load_completed(db, a.profile_id), a.created_at)
            steps_shown += len(steps)
            steps_required += sum(s["importance"] == "required" for s in steps)
            steps_paid += sum(s["resource"]["cost_tier"] == "paid" for s in steps)
            steps_gains.append(sum(s["resource"]["gain_if_completed"] for s in steps))

        null_rows, total_rows = db.execute(text(
            "SELECT count(*) FILTER (WHERE importance IS NULL), count(*) FROM skill_match_results")).one()
        completed = db.execute(text("SELECT count(*) FROM student_resource_progress WHERE status = 'completed'")).scalar()
    finally:
        db.close()

    print(f"{students:,} students (latest role-template assessment); {completed:,} completed activities in the database\n")
    width = 66
    print(f"{'':<{width}}{OLD:>16}{NEW:>16}")
    for (name, old), (_, new) in zip(orders[OLD].lines(), orders[NEW].lines()):
        print(f"{name:<{width}}{old:>16}{new:>16}")
    print("\nfirst_steps")
    print(f"  Required share            {share(steps_required, steps_shown):.1f}%")
    print(f"  Gain, mean / median       +{mean(steps_gains):.1f} / +{median(steps_gains):.1f}")
    print(f"  Paid resources shown      {share(steps_paid, steps_shown):.1f}%")
    print(f"\nStored assessments: {checked:,}; sum(points x credit) differs from readiness_score "
          f"by more than {TOLERANCE}: {not_reproduced:,}")
    print(f"Match rows with no stored importance (read through the role template): {null_rows:,} of {total_rows:,}")


if __name__ == "__main__":
    main()
