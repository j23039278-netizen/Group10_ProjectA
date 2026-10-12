"""
Load data/jd_dataset/jd_dataset.csv into the job_descriptions table.

  source = 'scraped', profile_id = NULL, role_id looked up by role_code,
  company = 'Anonymised', nlp_status = 'pending'.

Idempotent: a JD is skipped if a 'scraped' row with the same md5(raw_text)
already exists (job_descriptions has no jd_ref column and schema.sql is not
changed). Runs in one transaction; any error rolls everything back.

The connection string is read from $DATABASE_URL or backend/.env and is
never printed.

Usage (from repo root):
    python data/jd_dataset/load_jds.py
    python data/jd_dataset/load_jds.py --dry-run          # load, report, roll back
    python data/jd_dataset/load_jds.py --csv data/jd_dataset/samples/jd_dataset_sample.csv --dry-run
"""

import argparse
import os
import re
import sys

import psycopg

from jd_common import DATASET_PATH, REPO_ROOT, read_dataset

INSERT_SQL = """
INSERT INTO job_descriptions (profile_id, role_id, title, company, raw_text, source)
SELECT NULL, jr.role_id, %(title)s, %(company)s, %(raw_text)s, 'scraped'
FROM job_roles jr
WHERE jr.role_code = %(role_code)s
  AND NOT EXISTS (SELECT 1 FROM job_descriptions jd
                  WHERE jd.source = 'scraped' AND md5(jd.raw_text) = md5(%(raw_text)s))
"""


def database_url(override=None):
    if override:
        return override
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    env = REPO_ROOT / "backend" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+?)\s*$", line)
            if m:
                return m.group(1).strip("'\"")
    raise SystemExit("DATABASE_URL not set and not found in backend/.env")


def main():
    ap = argparse.ArgumentParser(description="Load JD dataset into job_descriptions")
    ap.add_argument("--csv", default=str(DATASET_PATH))
    ap.add_argument("--db-url", help="override connection string (default: backend/.env)")
    ap.add_argument("--dry-run", action="store_true", help="roll back at the end")
    args = ap.parse_args()

    rows = read_dataset(args.csv)
    url = re.sub(r"^postgresql\+\w+://", "postgresql://", database_url(args.db_url))
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            codes = {r[0] for r in cur.execute("SELECT role_code FROM job_roles").fetchall()}
            unknown = sorted({r["role_code"] for r in rows} - codes)
            if unknown:
                conn.rollback()
                sys.exit(f"Unknown role_code(s) in {args.csv}: {unknown}")
            inserted = 0
            for r in rows:
                cur.execute(INSERT_SQL, r)
                inserted += cur.rowcount
            summary = cur.execute("""
                SELECT jr.role_code, COUNT(*) FROM job_descriptions jd JOIN job_roles jr USING (role_id)
                WHERE jd.source = 'scraped' GROUP BY 1 ORDER BY 1""").fetchall()
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    print(f"{'[DRY RUN, rolled back] ' if args.dry_run else ''}"
          f"{len(rows)} JDs in CSV, {inserted} inserted, {len(rows) - inserted} already present")
    for code, n in summary:
        print(f"  {code:<16} {n}")


if __name__ == "__main__":
    main()
