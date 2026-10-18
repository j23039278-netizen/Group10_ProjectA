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
    @pytest.mark.parametrize("path", ["/api/admin/users", "/api/admin/audit-log", "/api/admin/skills",
                                      "/api/admin/resources"])
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


    def test_seed_resource_locked_admin_resource_editable(self, env, admin):
        c = env["client"]
        listed = c.get("/api/admin/resources", headers=admin)
        assert listed.status_code == 200 and len(listed.json()) > 0
        seed = next(r for r in listed.json() if r["source"] == "seed")
        assert c.patch(f"/api/admin/resources/{seed['resource_id']}", json={"cost": "$1"}, headers=admin).status_code == 400

        tableau = env["conn"].execute("SELECT skill_id::text FROM skills_library WHERE skill_name='Tableau'").fetchone()[0]
        body = {"skill_id": tableau, "resource_title": "Tableau Dashboards 101", "resource_type": "course",
                "provider": "Tableau", "url": "https://www.tableau.com/learn", "duration_hours": 6}
        new = c.post("/api/admin/resources", headers=admin, json=body)
        assert new.status_code == 201 and new.json()["source"] == "admin" and new.json()["skill_name"] == "Tableau"
        assert c.post("/api/admin/resources", headers=admin, json=body).status_code == 400   # same title, same skill
        rid = new.json()["resource_id"]
        upd = c.patch(f"/api/admin/resources/{rid}", headers=admin, json={"difficulty": "intermediate", "cost": "$20"})
        assert upd.status_code == 200 and upd.json()["difficulty"] == "intermediate" and upd.json()["cost"] == "$20"
        assert c.patch(f"/api/admin/resources/{rid}", headers=admin, json={"resource_type": None}).status_code == 400

        # Deactivating any resource (seed ones too) stops it being recommended
        off = c.patch(f"/api/admin/resources/{seed['resource_id']}", json={"is_active": False}, headers=admin)
        assert off.status_code == 200 and off.json()["is_active"] is False
        assert c.patch(f"/api/admin/resources/{seed['resource_id']}", json={"is_active": True}, headers=admin).status_code == 200
        actions = {r[0] for r in env["conn"].execute("SELECT DISTINCT action FROM audit_log").fetchall()}
        assert {"admin.resource_create", "admin.resource_update"} <= actions


# ── Advisor ──────────────────────────────────────────────────
class TestAdvisor:
    def test_profiles_complete_counts_complete_profiles_only(self, env, advisor, bob):
        c = env["client"]
        expected = lambda: env["conn"].execute(
            "SELECT count(*) FROM student_profiles sp JOIN users u USING (user_id) "
            "WHERE sp.is_complete AND u.role='student' AND u.is_active").fetchone()[0]
        complete = lambda: env["conn"].execute("SELECT is_complete FROM student_profiles WHERE profile_id = %s",
                                               (env["ids"]["bob"][1],)).fetchone()[0]
        # Bob has a skill but only a target role: not complete until the academic fields are filled in
        assert complete() is False
        before = c.get("/api/advisor/cohort/overview", headers=advisor).json()["profiles_complete"]
        assert before == expected()
        full = {"programme": "BCS", "university": "Swinburne", "year_of_study": 2, "target_role": "Data Analyst"}
        assert c.put("/api/students/profile", json=full, headers=bob).status_code == 200
        assert complete() is True
        assert c.get("/api/advisor/cohort/overview", headers=advisor).json()["profiles_complete"] == before + 1
        # Without any skill the profile is incomplete again
        java = env["conn"].execute("SELECT skill_id::text FROM skills_library WHERE skill_name='Java'").fetchone()[0]
        assert c.delete(f"/api/students/skills/{java}", headers=bob).status_code == 200
        assert complete() is False
        assert c.post("/api/students/skills", json={"skill_id": java}, headers=bob).status_code == 201
        assert complete() is True

    def test_student_detail(self, env, advisor, alice):
        c = env["client"]
        run(env, alice, role_id=env["da"])
        r = c.get(f"/api/advisor/students/{env['ids']['alice'][0]}", headers=advisor)
        assert r.status_code == 200
        d = r.json()
        assert {"student", "assessment", "skills", "skill_gaps", "history", "projects",
                "certifications", "progress"} <= d.keys()
        assert d["assessment"]["role_name"] == "Data Analyst" and len(d["history"]) >= 1
        assert d["history"] == sorted(d["history"], key=lambda h: h["created_at"])   # oldest first, for the chart
        assert any(g.get("reason") for g in d["skill_gaps"])
        # Only students have a record here; malformed ids are 404 like the other ID routes
        assert c.get(f"/api/advisor/students/{env['ids']['advisor']}", headers=advisor).status_code == 404
        assert c.get("/api/advisor/students/not-a-uuid", headers=advisor).status_code == 404
        assert c.get(f"/api/advisor/students/{env['ids']['alice'][0]}", headers=alice).status_code == 403


# ── Student projects and certifications: edit and delete ─────
class TestProfileRecords:
    def test_project_edit_delete_and_ownership(self, env, bob, alice):
        c = env["client"]
        assert c.post("/api/students/projects", headers=bob, json={"project_title": "Bot", "project_type": "personal"}).status_code == 201
        pid = next(p for p in c.get("/api/students/projects", headers=bob).json() if p["project_title"] == "Bot")["project_id"]
        upd = {"project_title": "Chat Bot", "technologies": ["Python"], "project_type": "internship", "year_completed": 2026}
        assert c.put(f"/api/students/projects/{pid}", headers=alice, json=upd).status_code == 404   # not hers
        assert c.delete(f"/api/students/projects/{pid}", headers=alice).status_code == 404
        assert c.put(f"/api/students/projects/{pid}", headers=bob, json={"project_title": ""}).status_code == 422
        assert c.put(f"/api/students/projects/{pid}", headers=bob, json=upd).status_code == 200
        row = next(p for p in c.get("/api/students/projects", headers=bob).json() if p["project_id"] == pid)
        assert row["project_title"] == "Chat Bot" and row["technologies"] == ["Python"]
        counts = lambda: env["conn"].execute("SELECT project_count, internship_count FROM student_profiles "
                                             "WHERE profile_id = %s", (env["ids"]["bob"][1],)).fetchone()
        assert counts()[0] >= 1 and counts()[1] >= 1   # internship-type project counts as an internship
        n = counts()[0]
        assert c.delete(f"/api/students/projects/{pid}", headers=bob).status_code == 200
        assert counts()[0] == n - 1
        assert c.delete(f"/api/students/projects/{pid}", headers=bob).status_code == 404

    def test_certification_edit_delete_and_ownership(self, env, bob, alice):
        c = env["client"]
        assert c.post("/api/students/certifications", headers=bob, json={"cert_name": "AZ-900"}).status_code == 201
        cid = next(x for x in c.get("/api/students/certifications", headers=bob).json() if x["cert_name"] == "AZ-900")["cert_id"]
        upd = {"cert_name": "AZ-900 Azure Fundamentals", "issuer": "Microsoft", "issue_date": "2026-05-01"}
        assert c.put(f"/api/students/certifications/{cid}", headers=alice, json=upd).status_code == 404
        assert c.put(f"/api/students/certifications/{cid}", headers=bob, json=upd).status_code == 200
        row = next(x for x in c.get("/api/students/certifications", headers=bob).json() if x["cert_id"] == cid)
        assert row["issuer"] == "Microsoft" and row["issue_date"] == "2026-05-01"
        certs = lambda: env["conn"].execute("SELECT certification_count FROM student_profiles WHERE profile_id = %s",
                                            (env["ids"]["bob"][1],)).fetchone()[0]
        n = certs()
        assert c.delete(f"/api/students/certifications/{cid}", headers=alice).status_code == 404
        assert c.delete(f"/api/students/certifications/{cid}", headers=bob).status_code == 200
        assert certs() == n - 1


    def test_evidence_files(self, env, alice, bob, advisor):
        c = env["client"]
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        pdf = b"%PDF-1.4\n" + b"x" * 100
        # The create response carries the new id, so the page can attach files straight away
        pid = c.post("/api/students/projects", headers=alice, json={"project_title": "Evidence demo"}).json()["project_id"]
        assert any(p["project_id"] == pid for p in c.get("/api/students/projects", headers=alice).json())
        up = lambda h, data, name="proof.png", url=f"/api/students/projects/{pid}/files": \
            c.post(url, headers=h, files={"file": (name, data, "image/png")})

        # Type comes from the content, not the name or the browser's Content-Type
        assert up(alice, b"<svg onload=alert(1)></svg>", "evil.png").status_code == 400
        assert up(alice, b"", "empty.png").status_code == 400
        assert up(alice, b"\x89PNG\r\n\x1a\n" + b"\x00" * (5 * 1024 * 1024)).status_code == 413
        first = up(alice, pdf, "..\\..\\cert")
        assert first.status_code == 201
        assert first.json()["content_type"] == "application/pdf" and first.json()["file_name"] == "cert.pdf"
        assert "data" not in first.json()
        assert up(bob, png).status_code == 404                                   # not Bob's project
        for _ in range(4):
            assert up(alice, png).status_code == 201
        assert up(alice, png).status_code == 400                                 # 6th file: limit is 5

        files = next(p for p in c.get("/api/students/projects", headers=alice).json() if p["project_id"] == pid)["files"]
        assert len(files) == 5 and all("data" not in f for f in files)
        fid = first.json()["file_id"]
        got = c.get(f"/api/students/files/{fid}", headers=alice)
        assert got.status_code == 200 and got.content == pdf
        assert got.headers["x-content-type-options"] == "nosniff" and got.headers["content-disposition"].startswith("attachment")
        assert c.get(f"/api/students/files/{fid}", headers=bob).status_code == 404
        assert c.get(f"/api/students/files/{fid}", headers=advisor).status_code == 200
        assert env["conn"].execute("SELECT count(*) FROM audit_log WHERE action='advisor.view_file' AND target_id=%s",
                                   (fid,)).fetchone()[0] == 1
        assert c.get("/api/students/files/not-a-uuid", headers=alice).status_code == 404
        detail = c.get(f"/api/advisor/students/{env['ids']['alice'][0]}", headers=advisor).json()
        assert len(next(p for p in detail["projects"] if p["project_id"] == pid)["files"]) == 5

        assert c.delete(f"/api/students/files/{fid}", headers=bob).status_code == 404
        assert c.delete(f"/api/students/files/{fid}", headers=alice).status_code == 200
        assert c.get(f"/api/students/files/{fid}", headers=alice).status_code == 404

        # Certifications take files too, and files go with their project when it is deleted
        cid = c.post("/api/students/certifications", headers=bob, json={"cert_name": "CCNA"}).json()["cert_id"]
        assert up(bob, png, url=f"/api/students/certifications/{cid}/files").status_code == 201
        assert len(next(x for x in c.get("/api/students/certifications", headers=bob).json()
                        if x["cert_id"] == cid)["files"]) == 1
        assert c.delete(f"/api/students/projects/{pid}", headers=alice).status_code == 200
        assert env["conn"].execute("SELECT count(*) FROM student_evidence_files WHERE project_id=%s",
                                   (pid,)).fetchone()[0] == 0


# ── Development progress ─────────────────────────────────────
class TestProgress:
    def test_give_up_unfinished_activity_only(self, env, alice, bob):
        c = env["client"]
        aid = run(env, alice, role_id=env["da"]).json()["assessment_id"]
        rid, rid2 = [r[0] for r in env["conn"].execute(
            "SELECT resource_id::text FROM recommendations_library ORDER BY resource_title LIMIT 2").fetchall()]

        assert c.post(f"/api/progress/{rid}/start?assessment_id={aid}", headers=alice).status_code == 201
        mine = c.get("/api/progress/my", headers=alice).json()["progress"]
        assert next(p for p in mine if p["resource_id"] == rid)["assessment_id"] == aid   # for "View in Recommendations"

        assert c.delete(f"/api/progress/{rid}", headers=bob).status_code == 404           # Bob never started it
        assert c.delete(f"/api/progress/{rid}", headers=alice).status_code == 200
        assert all(p["resource_id"] != rid for p in c.get("/api/progress/my", headers=alice).json()["progress"])
        assert c.delete(f"/api/progress/{rid}", headers=alice).status_code == 404         # already gone
        assert c.delete("/api/progress/not-a-uuid", headers=alice).status_code == 404

        # Completed activities stay on the record
        c.post(f"/api/progress/{rid2}/start?assessment_id={aid}", headers=alice)
        assert c.post(f"/api/progress/{rid2}/complete", headers=alice, json={"status": "completed"}).status_code == 200
        assert c.delete(f"/api/progress/{rid2}", headers=alice).status_code == 404


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
