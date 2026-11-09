"""
Tests for the learning-resource links: data/check_resource_links.py and the dead-link
fixes in the seed files and database/migrate_existing_db.sql.

No test uses the network. The database tests create their own database
(seagas_test_links_<pid>) and drop it at the end; they are skipped when PostgreSQL is
not reachable. TEST_PG_URL works as in tests/test_backend_api.py.

    python -m pytest tests/test_resource_links.py -q
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
import check_resource_links as links  # noqa: E402

SEED_FILES = ["database/seed_recommendations_library_final.sql", "database/seed_business_skills.sql"]
SQL_FILES = ["database/schema.sql", "database/migrate_existing_db.sql",
             "database/seed_skills_library_v2.sql", "database/seed_job_role_skills.sql",
             "database/seed_recommendations_library_final.sql", "database/seed_business_skills.sql"]
RERUN = SQL_FILES[1:]   # what start_backend.bat runs on every start

# Returned 404 on 4 and 9 November 2026 and were replaced.
OLD_DEAD_URLS = [
    "https://learn.microsoft.com/en-us/training/paths/windows-server-fundamentals-getting-started/",
    "https://pecb.com/en/education-and-training-for-iso-iec-27001",
    "https://scikit-learn.org/stable/tutorial/index.html",
    "https://skillshop.withgoogle.com/googleanalytics",
    "https://www.coursera.org/learn/adaptability",
    "https://www.coursera.org/learn/everyday-leadership-new",
    "https://www.coursera.org/learn/feature-engineering",
    "https://www.coursera.org/learn/financial-analysis",
    "https://www.coursera.org/learn/google-cloud-iam",
    "https://www.coursera.org/learn/how-to-write-a-research-paper",
    "https://www.coursera.org/learn/inspire-motivate",
    "https://www.coursera.org/learn/network-security-firewalls-vpns",
    "https://www.coursera.org/learn/risk-management-project",
    "https://www.coursera.org/learn/site-reliability-engineering-slos",
    "https://www.coursera.org/learn/technical-writing-101",
    "https://www.coursera.org/learn/wharton-decision-making",
    "https://www.cybrary.it/course/network-security-fundamentals/",
    "https://www.cybrary.it/course/security-monitoring-and-siem/",
    "https://www.cybrary.it/course/snort/",
    "https://www.cybrary.it/course/vpn-fundamentals/",
    "https://www.iiba.org/certification/entry-certificate-in-business-analysis/",
    "https://www.kaggle.com/learn/numpy",
    "https://www.kaggle.com/learn/r",
    "https://www.linkedin.com/learning/improving-your-attention-to-detail",
    "https://www.mongodb.com/developer/languages/javascript/",
    "https://www.tenable.com/education/nessus",
]


# ── classify: one answer -> class, no network ────────────────

@pytest.mark.parametrize("status", [404, 410])
def test_classify_dead(status):
    assert links.classify(status)[0] == "dead"


@pytest.mark.parametrize("status", [401, 403, 429, 500, 502, 503, 400, 999])
def test_classify_blocked_or_unknown(status):
    assert links.classify(status)[0] == "blocked"


def test_classify_no_response():
    cls, reason = links.classify(None, error="timed out")
    assert cls == "no_response" and "timed out" in reason


@pytest.mark.parametrize("status", [200, 203])
def test_classify_ok(status):
    page = "<html><head><title>Python for Everybody | Coursera</title></head><body><h1>Python</h1></body></html>"
    assert links.classify(status, page)[0] == "ok"


@pytest.mark.parametrize("page", [
    "<html><head><title>Page Not Found | Example Academy</title></head></html>",
    "<title>Example</title><h1 class='x'>Sorry, this page <b>does not exist</b></h1>",
    "<title>404 - Example</title>",
])
def test_classify_soft_404_is_checked_by_hand_not_dead(page):
    cls, reason = links.classify(200, page)
    assert cls == "check_by_hand" and "page says" in reason


def test_classify_deep_link_redirected_home_is_checked_by_hand():
    home = lambda url, final: links.classify(200, "<title>Example</title>", url=url, final_url=final)[0]
    assert home("https://example.com/course/abc", "https://example.com/") == "check_by_hand"
    # a redirect to another deep page is fine, and so is a home page link
    assert home("https://example.com/a", "https://example.com/b") == "ok"
    assert home("https://example.com/", "https://www.example.com/") == "ok"


def test_classify_text_404_in_body_only_is_ok():
    """Only the <title> and first <h1> count, so a footer link to a 404 page does not"""
    page = "<title>NumPy exercises</title><h1>100 exercises</h1><footer><a href='/404'>404</a> not found</footer>"
    assert links.classify(200, page)[0] == "ok"


# ── collecting rows, checking, exit code ─────────────────────

def test_parse_seed_rows_reads_skill_title_and_url():
    text = ("-- ('Comment', 'not a row', 'https://comment.example')\n"
            "('Python', 'Automate the Boring Stuff', 'course', 'Udemy', 'https://www.udemy.com/course/automate/', 10, 'Free', 'beginner', 'Python''s basics.'),\n"
            "('Payroll', 'Employer''s Guide', 'course', 'KWSP', 'https://www.kwsp.gov.my/', 3, 'Free', 'beginner', 'x')\n")
    rows = links.parse_seed_rows(text, "f.sql")
    assert [(r["skill"], r["title"], r["url"], r["line"]) for r in rows] == [
        ("Python", "Automate the Boring Stuff", "https://www.udemy.com/course/automate/", 2),
        ("Payroll", "Employer's Guide", "https://www.kwsp.gov.my/", 3)]


def test_collect_rows_covers_both_seed_files():
    rows = links.collect_rows()
    assert {r["file"] for r in rows} == {Path(f).name for f in SEED_FILES}
    assert len(rows) > 300 and all(r["url"].startswith("http") for r in rows)


def test_check_urls_uses_the_fetcher_once_per_url():
    calls = []
    answers = {"https://a.example/x": (404, "", None, "https://a.example/x"),
               "https://a.example/y": (200, "<title>Y</title>", None, "https://a.example/y"),
               "https://b.example/": (None, "", "timed out", "https://b.example/")}

    def fake_fetch(url):
        calls.append(url)
        return answers[url]

    results = links.check_urls(list(answers), workers=2, fetcher=fake_fetch)
    assert sorted(calls) == sorted(answers)
    assert {u: c for u, (c, _) in results.items()} == {
        "https://a.example/x": "dead", "https://a.example/y": "ok", "https://b.example/": "no_response"}


def test_main_exit_code_and_report(monkeypatch, capsys, tmp_path):
    rows = [{"file": "f.sql", "line": 1, "skill": "R", "title": "Old R course", "url": "https://x.example/r"},
            {"file": "f.sql", "line": 2, "skill": "SQL", "title": "SQL", "url": "https://x.example/sql"}]
    monkeypatch.setattr(links, "collect_rows", lambda: rows)
    monkeypatch.setattr(links, "check_urls", lambda urls, workers: {
        "https://x.example/r": ("dead", "HTTP 404"), "https://x.example/sql": ("ok", "HTTP 200")})
    out_csv = tmp_path / "links.csv"
    assert links.main(["--csv", str(out_csv)]) == 1
    out = capsys.readouterr().out
    assert "Dead links (1)" in out and "R -- Old R course" in out
    assert out_csv.read_text(encoding="utf-8").splitlines()[1].startswith("dead,HTTP 404,x.example,https://x.example/r")

    monkeypatch.setattr(links, "check_urls", lambda urls, workers: {u: ("ok", "HTTP 200") for u in urls})
    assert links.main([]) == 0


def test_old_dead_urls_are_gone_from_the_seed_files():
    text = "\n".join((ROOT / f).read_text(encoding="utf-8") for f in SEED_FILES)
    still = [u for u in OLD_DEAD_URLS if f"'{u}'" in text]
    assert still == []


def test_migrate_fixes_every_replaced_url():
    """Each replaced URL has an UPDATE in migrate_existing_db.sql, so existing databases get it"""
    migrate = (ROOT / "database/migrate_existing_db.sql").read_text(encoding="utf-8")
    missing = [u for u in OLD_DEAD_URLS if f"r.url = '{u}'" not in migrate]
    assert missing == []


# ── Database: fresh and existing databases ───────────────────

def run_sql_file(conn, path):
    # psql meta-commands (\set ...) are not SQL; the files are otherwise plain SQL
    sql = "\n".join(l for l in (ROOT / path).read_text(encoding="utf-8").splitlines()
                    if not l.lstrip().startswith("\\"))
    conn.execute(sql)


def snapshot(conn):
    return conn.execute(
        "SELECT resource_id::text, skill_id::text, resource_title, resource_type, provider, url, duration_hours, "
        "cost, difficulty, description, is_active, source, created_at FROM recommendations_library "
        "ORDER BY resource_id").fetchall()


def seed_row(conn, skill, title):
    return conn.execute(
        "SELECT r.resource_id::text, r.resource_title, r.provider, r.url, r.duration_hours, r.cost, r.difficulty, "
        "r.description FROM recommendations_library r JOIN skills_library sl USING (skill_id) "
        "WHERE sl.skill_name = %s AND r.resource_title = %s", (skill, title)).fetchone()


@pytest.fixture(scope="module")
def db():
    psycopg = pytest.importorskip("psycopg")
    pg_url = os.environ.get("TEST_PG_URL", "postgresql://postgres:postgres123@localhost:5432/postgres")
    name = f"seagas_test_links_{os.getpid()}"
    try:
        admin = psycopg.connect(pg_url, autocommit=True, connect_timeout=3)
    except Exception as e:
        pytest.skip(f"PostgreSQL not reachable ({e})")
    admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = psycopg.connect(pg_url.rsplit("/", 1)[0] + "/" + name, autocommit=True)
    for f in SQL_FILES:
        run_sql_file(conn, f)
    yield conn
    conn.close()
    admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    admin.close()


def test_fresh_database_has_the_new_urls(db):
    urls = {u for (u,) in db.execute("SELECT url FROM recommendations_library")}
    assert not urls & set(OLD_DEAD_URLS)
    row = seed_row(db, "Network Security", "Connect and Protect: Networks and Network Security")
    assert row and row[3] == "https://www.coursera.org/learn/networks-and-network-security"


def test_running_migrate_and_seeds_again_changes_nothing(db):
    before = snapshot(db)
    for f in RERUN:
        run_sql_file(db, f)
    assert snapshot(db) == before
    dupes = db.execute("SELECT count(*) - count(DISTINCT (skill_id, resource_title)) FROM recommendations_library")
    assert dupes.fetchone()[0] == 0


def test_existing_database_with_old_urls_is_fixed_in_place(db):
    """A database seeded before the fix: its rows get the new values, keep their resource_id
    and progress rows, and the seeds add no second copy"""
    expected = {k: seed_row(db, *k) for k in [
        ("Network Security", "Connect and Protect: Networks and Network Security"),
        ("Interpersonal Skills", "Inspiring and Motivating Individuals"),
        ("Machine Learning", "Build an ML Classification Model Project"),
        ("Scikit-learn", "Scikit-learn Official Tutorials")]}
    count = db.execute("SELECT count(*) FROM recommendations_library").fetchone()[0]

    # Put the old seed values back, as an existing database still has them
    ns_id = expected[("Network Security", "Connect and Protect: Networks and Network Security")][0]
    db.execute("UPDATE recommendations_library SET resource_title = 'Cybrary Network Security Fundamentals', "
               "provider = 'Cybrary', url = 'https://www.cybrary.it/course/network-security-fundamentals/', "
               "duration_hours = 10, cost = 'Free', description = 'Free network security fundamentals course on Cybrary.' "
               "WHERE resource_id = %s", (ns_id,))
    db.execute("UPDATE recommendations_library SET url = 'https://www.coursera.org/learn/inspire-motivate', "
               "duration_hours = 6 WHERE resource_id = %s",
               (expected[("Interpersonal Skills", "Inspiring and Motivating Individuals")][0],))
    for k in [("Machine Learning", "Build an ML Classification Model Project"),
              ("Scikit-learn", "Scikit-learn Official Tutorials")]:
        db.execute("UPDATE recommendations_library SET url = 'https://scikit-learn.org/stable/tutorial/index.html' "
                   "WHERE resource_id = %s", (expected[k][0],))

    # A student has saved the old Network Security resource
    uid = db.execute("INSERT INTO users (email, password_hash, role, full_name) VALUES "
                     "('links@student.newinti.edu.my', 'x', 'student', 'Link Tester') RETURNING user_id").fetchone()[0]
    pid = db.execute("INSERT INTO student_profiles (user_id, target_role) VALUES (%s, 'Data Analyst') "
                     "RETURNING profile_id", (uid,)).fetchone()[0]
    db.execute("INSERT INTO student_resource_progress (profile_id, resource_id, skill_id, status) "
               "SELECT %s, resource_id, skill_id, 'in_progress' FROM recommendations_library WHERE resource_id = %s",
               (pid, ns_id))

    for f in RERUN:
        run_sql_file(db, f)

    for k, row in expected.items():
        assert seed_row(db, *k) == row, k
    assert db.execute("SELECT count(*) FROM recommendations_library").fetchone()[0] == count
    assert db.execute("SELECT count(*) FROM recommendations_library WHERE resource_title = "
                      "'Cybrary Network Security Fundamentals'").fetchone()[0] == 0
    progress = db.execute("SELECT resource_id::text, status FROM student_resource_progress WHERE profile_id = %s",
                          (pid,)).fetchall()
    assert progress == [(ns_id, "in_progress")]


def test_new_title_taken_keeps_old_title_but_fixes_the_link(db):
    """If another resource of the skill already has the new title (uq_resource_skill),
    the old row keeps its title and still gets the working link"""
    old = seed_row(db, "VPN", "Securing the Network")
    db.execute("UPDATE recommendations_library SET resource_title = 'VPN Fundamentals', "
               "url = 'https://www.cybrary.it/course/vpn-fundamentals/' WHERE resource_id = %s", (old[0],))
    db.execute("INSERT INTO recommendations_library (skill_id, resource_title, resource_type, url, source) "
               "SELECT skill_id, 'Securing the Network', 'course', 'https://example.org/admin-copy', 'admin' "
               "FROM skills_library WHERE skill_name = 'VPN'")

    for f in RERUN:
        run_sql_file(db, f)

    fixed = seed_row(db, "VPN", "VPN Fundamentals")
    assert fixed[0] == old[0] and fixed[3] == old[3]
    assert seed_row(db, "VPN", "Securing the Network")[3] == "https://example.org/admin-copy"
