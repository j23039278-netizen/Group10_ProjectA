"""
Backend API tests (FastAPI TestClient) for SEAGAS.

Run from the repo root:
    python -m pip install -r tests/requirements.txt
    python -m pytest tests/test_backend_api.py -q

Each run creates its own database (seagas_test_api_<pid>) from database/schema.sql
and the seed files, and drops it at the end; seagas_db is never touched. The tests
are skipped when PostgreSQL is not reachable. Set TEST_PG_URL to point somewhere
else (default: postgresql://postgres:postgres123@localhost:5432/postgres).

Matching uses method="keyword" so results are exact and no NLP model is needed.
"""

import os
import sys
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
bcrypt = pytest.importorskip("bcrypt")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

ROOT = Path(__file__).resolve().parents[1]
PG_URL = os.environ.get("TEST_PG_URL", "postgresql://postgres:postgres123@localhost:5432/postgres")
DB_NAME = f"seagas_test_api_{os.getpid()}"
SQL_FILES = ["database/schema.sql", "database/migrate_existing_db.sql",
             "database/seed_skills_library_v2.sql", "database/seed_job_role_skills.sql",
             "database/seed_recommendations_library_final.sql"]
PASSWORD = "Test#Pass2026"


def run_sql_file(conn, path):
    # psql meta-commands (\set ...) are not SQL; the files are otherwise plain SQL
    sql = "\n".join(l for l in (ROOT / path).read_text(encoding="utf-8").splitlines()
                    if not l.lstrip().startswith("\\"))
    conn.execute(sql)


def db_url(name):
    return PG_URL.rsplit("/", 1)[0] + "/" + name


@pytest.fixture(scope="module")
def env():
    """A fresh database, the app wired to it, and a few accounts"""
    try:
        admin_conn = psycopg.connect(PG_URL, autocommit=True, connect_timeout=3)
    except Exception as e:
        pytest.skip(f"PostgreSQL not reachable ({e})")
    admin_conn.execute(f'DROP DATABASE IF EXISTS "{DB_NAME}"')
    admin_conn.execute(f'CREATE DATABASE "{DB_NAME}"')
    conn = psycopg.connect(db_url(DB_NAME), autocommit=True)
    for f in SQL_FILES:
        run_sql_file(conn, f)

    pw = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

    def user(email, role, name):
        return conn.execute("INSERT INTO users (email, password_hash, role, full_name) VALUES (%s,%s,%s,%s) "
                            "RETURNING user_id::text", (email, pw, role, name)).fetchone()[0]

    def student(email, name, skills):
        uid = user(email, "student", name)
        pid = conn.execute("INSERT INTO student_profiles (user_id, target_role) VALUES (%s,'Data Analyst') "
                           "RETURNING profile_id::text", (uid,)).fetchone()[0]
        for skill, level in skills:
            conn.execute("INSERT INTO student_skills (profile_id, skill_id, proficiency_level) "
                         "SELECT %s, skill_id, %s FROM skills_library WHERE skill_name = %s", (pid, level, skill))
        return uid, pid

    ids = {
        "alice": student("alice@student.newinti.edu.my", "Alice",
                         [("Python", "advanced"), ("SQL", "intermediate"), ("Excel", "beginner")]),
        "bob": student("bob@student.newinti.edu.my", "Bob", [("Java", "intermediate")]),
        "advisor": user("adv@advisor.newinti.edu.my", "advisor", "Advisor A"),
        "admin": user("boss@admin.newinti.edu.my", "admin", "Admin A"),
    }
    da = conn.execute("SELECT role_id::text FROM job_roles WHERE role_name='Data Analyst'").fetchone()[0]

    # the app reads these when it is imported
    os.environ["DATABASE_URL"] = db_url(DB_NAME).replace("postgresql://", "postgresql+psycopg://")
    os.environ["SECRET_KEY"] = "test-" + os.urandom(16).hex()
    sys.path.insert(0, str(ROOT / "backend"))
    from fastapi.testclient import TestClient
    import main
    import database

    client = TestClient(main.app)
    yield {"client": client, "conn": conn, "ids": ids, "da": da}

    client.close()
    database.engine.dispose()
    conn.close()
    admin_conn.execute(f'DROP DATABASE IF EXISTS "{DB_NAME}" WITH (FORCE)')
    admin_conn.close()


def token(env, email, password=PASSWORD):
    r = env["client"].post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture(scope="module")
def alice(env):
    return token(env, "alice@student.newinti.edu.my")


@pytest.fixture(scope="module")
def bob(env):
    return token(env, "bob@student.newinti.edu.my")


@pytest.fixture(scope="module")
def advisor(env):
    return token(env, "adv@advisor.newinti.edu.my")


@pytest.fixture(scope="module")
def admin(env):
    return token(env, "boss@admin.newinti.edu.my")


def run(env, headers, **body):
    body.setdefault("matching_method", "keyword")
    return env["client"].post("/api/assessments/run", json=body, headers=headers)


# ── Authentication ───────────────────────────────────────────
class TestAuth:
    def test_login_returns_role_from_database(self, env):
        r = env["client"].post("/api/auth/login", data={"username": "ADV@advisor.newinti.edu.my", "password": PASSWORD})
        assert r.status_code == 200 and r.json()["role"] == "advisor"   # email is case-insensitive

    def test_wrong_password_and_unknown_email(self, env):
        c = env["client"]
        assert c.post("/api/auth/login", data={"username": "alice@student.newinti.edu.my", "password": "nope-nope"}).status_code == 401
        assert c.post("/api/auth/login", data={"username": "ghost@student.newinti.edu.my", "password": PASSWORD}).status_code == 401

    def test_overlong_password_is_401_not_500(self, env):
        r = env["client"].post("/api/auth/login", data={"username": "alice@student.newinti.edu.my", "password": "x" * 80})
        assert r.status_code == 401

    @pytest.mark.parametrize("email,status", [
        ("new1@student.newinti.edu.my", 201),
        ("new2@gmail.com", 400),
        ("new3@advisor.newinti.edu.my", 400),
        ("new4@fake-student.newinti.edu.my", 400),
    ])
    def test_register_student_email_domain(self, env, email, status):
        r = env["client"].post("/api/auth/register", json={"email": email, "password": "Password1!", "full_name": "N"})
        assert r.status_code == status, r.text

    @pytest.mark.parametrize("password", ["short", "x" * 73, "密码" * 13])
    def test_register_password_rules(self, env, password):
        r = env["client"].post("/api/auth/register", json={
            "email": "pw@student.newinti.edu.my", "password": password, "full_name": "P"})
        assert r.status_code == 400

    def test_register_cannot_choose_staff_role(self, env):
        r = env["client"].post("/api/auth/register", json={
            "email": "x@student.newinti.edu.my", "password": "Password1!", "full_name": "X", "role": "admin"})
        assert r.status_code == 403

    def test_deactivated_account_and_old_token(self, env, admin):
        c = env["client"]
        r = c.post("/api/auth/register", json={"email": "temp@student.newinti.edu.my", "password": "Password1!", "full_name": "T"})
        assert r.status_code == 201
        headers = token(env, "temp@student.newinti.edu.my", "Password1!")
        uid = env["conn"].execute("SELECT user_id::text FROM users WHERE email='temp@student.newinti.edu.my'").fetchone()[0]
        assert c.patch(f"/api/admin/users/{uid}", json={"is_active": False}, headers=admin).status_code == 200
        assert c.post("/api/auth/login", data={"username": "temp@student.newinti.edu.my", "password": "Password1!"}).status_code == 403
        assert c.get("/api/auth/me", headers=headers).status_code == 401


# ── Role-based access ────────────────────────────────────────
class TestRoles:
    @pytest.mark.parametrize("path", ["/api/admin/users", "/api/admin/audit-log", "/api/admin/skills"])
    def test_admin_api_needs_admin(self, env, alice, advisor, path):
        assert env["client"].get(path, headers=alice).status_code == 403
        assert env["client"].get(path, headers=advisor).status_code == 403

    def test_advisor_api_needs_staff(self, env, alice, advisor):
        assert env["client"].get("/api/advisor/cohort/overview", headers=alice).status_code == 403
        assert env["client"].get("/api/advisor/cohort/overview", headers=advisor).status_code == 200

    def test_no_token(self, env):
        assert env["client"].get("/api/students/profile").status_code == 401


# ── Assessments ──────────────────────────────────────────────
class TestAssessment:
    def test_role_template_assessment(self, env, alice):
        r = run(env, alice, role_id=env["da"])
        assert r.status_code == 201, r.text
        body = r.json()
        mr = body["match_results"]
        assert body["matching_method"] == "keyword" and len(mr) == body["skill_summary"]["total"] > 0
        w = {"required": 3, "preferred": 2, "bonus": 1}
        c = {"strong": 1, "developing": .5, "gap": 0}
        expected = round(sum(w[m["importance"]] * c[m["match_status"]] for m in mr)
                         / sum(w[m["importance"]] for m in mr) * 100, 2)
        assert body["readiness_score"] == expected
        sql = next(m for m in mr if m["skill_name"] == "SQL")
        assert sql["match_status"] == "strong" and sql["matched_student_skill"] == "SQL" and sql["reason"]
        excel = next((m for m in mr if m["skill_name"] == "Excel"), None)
        if excel:   # beginner with no evidence
            assert excel["match_status"] == "developing"

    def test_results_stored_with_reason(self, env, alice):
        aid = run(env, alice, role_id=env["da"]).json()["assessment_id"]
        n, with_reason = env["conn"].execute(
            "SELECT count(*), count(reason) FROM skill_match_results WHERE assessment_id=%s", (aid,)).fetchone()
        assert n > 0 and n == with_reason
        g = env["client"].get(f"/api/assessments/{aid}", headers=alice).json()
        assert all("reason" in m for m in g["match_results"])

    def test_history_has_dimension_scores(self, env, alice):
        run(env, alice, role_id=env["da"])
        h = env["client"].get("/api/assessments/my/history", headers=alice).json()[0]
        assert {"score_technical", "score_project_exp", "score_certification"} <= set(h)

    def test_unknown_method_is_400(self, env, alice):
        assert run(env, alice, role_id=env["da"], matching_method="spacy_ner").status_code == 400

    def test_experience_scores_follow_records(self, env, alice):
        c = env["client"]
        before = run(env, alice, role_id=env["da"]).json()["dimension_scores"]
        assert c.post("/api/students/projects", json={"project_title": "Sales dashboard"}, headers=alice).status_code == 201
        assert c.post("/api/students/certifications", json={"cert_name": "PL-300"}, headers=alice).status_code == 201
        after = run(env, alice, role_id=env["da"]).json()["dimension_scores"]
        assert after["project_experience"] > before["project_experience"]
        assert after["certification"] > before["certification"]

    def test_pasted_jd_flow(self, env, alice):
        c = env["client"]
        jd = c.post("/api/jobs/descriptions", headers=alice, json={
            "title": "Junior Data Analyst",
            "raw_text": "Must know SQL and PowerBI; experience with data visualization tools is a plus. "
                        "Good communication skills."}).json()["jd_id"]
        a = c.post(f"/api/jobs/descriptions/{jd}/analyse?method=keyword", headers=alice)
        assert a.status_code == 200
        assert {"SQL", "Power BI", "Data Visualisation", "Communication"} <= {s["skill_name"] for s in a.json()["extracted_skills"]}
        again = c.post(f"/api/jobs/descriptions/{jd}/analyse?method=keyword", headers=alice).json()
        stored = env["conn"].execute("SELECT count(*) FROM jd_extracted_skills WHERE jd_id=%s", (jd,)).fetchone()[0]
        assert stored == again["skill_count"]           # re-analysis replaces, never duplicates
        r = run(env, alice, jd_id=jd)
        assert r.status_code == 201
        assert "PowerBI" not in {m["skill_name"] for m in r.json()["match_results"]}   # canonical names


# ── Record-level access ──────────────────────────────────────
class TestOwnership:
    def test_students_cannot_read_each_others_records(self, env, alice, bob, advisor):
        c = env["client"]
        aid = run(env, alice, role_id=env["da"]).json()["assessment_id"]
        assert c.get(f"/api/assessments/{aid}", headers=bob).status_code == 404
        assert c.get(f"/api/assessments/{aid}/recommendations", headers=bob).status_code == 404
        assert c.get(f"/api/assessments/{aid}", headers=advisor).status_code == 200
        jd = c.post("/api/jobs/descriptions", headers=alice, json={"raw_text": "We need a graduate with SQL and Python skills for reporting work."}).json()["jd_id"]
        assert c.get(f"/api/jobs/descriptions/{jd}", headers=bob).status_code == 404
        assert c.post(f"/api/jobs/descriptions/{jd}/analyse?method=keyword", headers=bob).status_code == 404
        assert run(env, bob, jd_id=jd).status_code == 404

    def test_malformed_id_is_404(self, env, alice):
        assert env["client"].get("/api/assessments/not-a-uuid", headers=alice).status_code == 404


# ── Student profile input ────────────────────────────────────
class TestProfile:
    @pytest.mark.parametrize("body", [{"gpa": 4.5}, {"gpa": -1}, {"year_of_study": 0}, {"year_of_study": 9}])
    def test_profile_limits(self, env, alice, body):
        assert env["client"].put("/api/students/profile", json=body, headers=alice).status_code == 422

    def test_skill_add_validation_and_delete(self, env, alice):
        c = env["client"]
        sid = env["conn"].execute("SELECT skill_id::text FROM skills_library WHERE skill_name='Tableau'").fetchone()[0]
        assert c.post("/api/students/skills", json={"skill_id": sid, "proficiency_level": "expert"}, headers=alice).status_code == 422
        assert c.post("/api/students/skills", json={"skill_id": "nope"}, headers=alice).status_code == 422
        assert c.post("/api/students/skills", json={"skill_id": sid, "proficiency_level": "beginner",
                                                    "evidence_type": ["project"]}, headers=alice).status_code == 201
        row = next(s for s in c.get("/api/students/skills", headers=alice).json() if s["skill_name"] == "Tableau")
        assert c.delete(f"/api/students/skills/{row['skill_id']}", headers=alice).status_code == 200
        assert "Tableau" not in {s["skill_name"] for s in c.get("/api/students/skills", headers=alice).json()}


# ── Admin ────────────────────────────────────────────────────
class TestAdmin:
    def test_create_advisor_needs_advisor_domain(self, env, admin):
        c = env["client"]
        bad = c.post("/api/admin/users", headers=admin, json={"email": "x@gmail.com", "full_name": "X",
                                                              "password": "Advisor#1", "role": "advisor"})
        assert bad.status_code == 400
        ok = c.post("/api/admin/users", headers=admin, json={"email": "lim@advisor.newinti.edu.my", "full_name": "Dr Lim",
                                                             "password": "Advisor#1", "role": "advisor"})
        assert ok.status_code == 201
        assert token(env, "lim@advisor.newinti.edu.my", "Advisor#1")

    def test_seed_skill_locked_admin_skill_editable(self, env, admin):
        c = env["client"]
        excel = env["conn"].execute("SELECT skill_id::text FROM skills_library WHERE skill_name='Excel'").fetchone()[0]
        assert c.patch(f"/api/admin/skills/{excel}", json={"description": "x"}, headers=admin).status_code == 400
        new = c.post("/api/admin/skills", headers=admin, json={"skill_name": "Quantum Computing", "category": "AI_Digital",
                                                               "aliases": ["qc", "QC"]})
        assert new.status_code == 201 and new.json()["source"] == "admin" and new.json()["aliases"] == ["qc"]
        upd = c.patch(f"/api/admin/skills/{new.json()['skill_id']}", json={"description": "Qubits"}, headers=admin)
        assert upd.status_code == 200 and upd.json()["description"] == "Qubits"

    def test_admin_role_with_skills_can_be_assessed(self, env, admin, alice):
        c = env["client"]
        rid = c.post("/api/admin/roles", headers=admin, json={"role_name": "BI Developer"}).json()["role_id"]
        sids = [r[0] for r in env["conn"].execute(
            "SELECT skill_id::text FROM skills_library WHERE skill_name IN ('SQL','Power BI','Communication')").fetchall()]
        r = c.put(f"/api/admin/roles/{rid}/skills", headers=admin,
                  json=[{"skill_id": s, "importance": "required"} for s in sids])
        assert r.status_code == 200 and len(r.json()["skills"]) == 3
        assert run(env, alice, role_id=rid).json()["skill_summary"]["total"] == 3
        assert c.put(f"/api/admin/roles/{env['da']}/skills", headers=admin, json=[]).status_code == 400

    def test_audit_log_records_events(self, env, admin, advisor):
        c = env["client"]
        c.post("/api/auth/login", data={"username": "ghost@student.newinti.edu.my", "password": "whatever1"})
        alice_uid = env["ids"]["alice"][0]
        c.get(f"/api/advisor/students/{alice_uid}", headers=advisor)
        actions = {r[0] for r in env["conn"].execute("SELECT DISTINCT action FROM audit_log").fetchall()}
        assert {"auth.login", "auth.login_failed", "auth.register", "assessment.run", "jd.analyse",
                "advisor.view_student", "admin.user_create", "admin.user_update",
                "admin.skill_create", "admin.role_create"} <= actions
        leaked = env["conn"].execute("SELECT count(*) FROM audit_log WHERE details::text LIKE '%%$2b$%%'").fetchone()[0]
        assert leaked == 0
        page = c.get("/api/admin/audit-log?action=auth.login_failed", headers=admin).json()
        assert page["total"] >= 1 and all(e["action"] == "auth.login_failed" for e in page["entries"])


# ── Batch assessments (data/run_assessments.py uses this) ────
def test_assessment_service_matches_endpoint(env, alice):
    import assessment_service
    from database import SessionLocal
    db = SessionLocal()
    try:
        profile = db.execute(assessment_service.text("SELECT * FROM student_profiles WHERE profile_id = :p"),
                             {"p": env["ids"]["alice"][1]}).fetchone()
        direct = assessment_service.run_for_profile(db, profile, role_id=env["da"], method="keyword")
    finally:
        db.close()
    via_api = run(env, alice, role_id=env["da"]).json()
    assert direct["readiness_score"] == via_api["readiness_score"]
    assert [m["match_status"] for m in direct["match_results"]] == [m["match_status"] for m in via_api["match_results"]]
