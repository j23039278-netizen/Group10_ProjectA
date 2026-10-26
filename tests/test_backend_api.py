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

import io
import os
import re
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


def student_number(env, email):
    row = env["conn"].execute("SELECT student_number FROM users WHERE lower(email) = lower(%s)", (email,)).fetchone()
    return row[0] if row else None


def login(env, email, password=PASSWORD, student_id=None):
    """POST /api/auth/login. Students sign in with their student ID too (looked up if not given)."""
    data = {"username": email, "password": password}
    sid = student_id if student_id is not None else student_number(env, email)
    if sid:
        data["student_id"] = sid
    return env["client"].post("/api/auth/login", data=data)


def token(env, email, password=PASSWORD, student_id=None):
    r = login(env, email, password, student_id)
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

    def test_student_login_needs_student_id(self, env):
        c = env["client"]
        sid = student_number(env, "alice@student.newinti.edu.my")
        assert len(sid) == 9 and sid.isdigit()                      # given by the database
        no_id = c.post("/api/auth/login", data={"username": "alice@student.newinti.edu.my", "password": PASSWORD})
        assert no_id.status_code == 401 and "student ID" in no_id.json()["detail"]
        assert login(env, "alice@student.newinti.edu.my", student_id="123456789").status_code == 401
        bobs = student_number(env, "bob@student.newinti.edu.my")
        assert login(env, "alice@student.newinti.edu.my", student_id=bobs).status_code == 401
        assert login(env, "alice@student.newinti.edu.my", student_id=f" {sid} ").status_code == 200
        reasons = {r[0] for r in env["conn"].execute(
            "SELECT details->>'reason' FROM audit_log WHERE action = 'auth.login_failed'").fetchall()}
        assert "wrong or missing student ID" in reasons

    def test_every_student_has_a_student_number(self, env):
        conn = env["conn"]
        assert conn.execute("SELECT count(*) FROM users WHERE role = 'student' AND student_number IS NULL").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM users WHERE role <> 'student' AND student_number IS NOT NULL").fetchone()[0] == 0
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute("INSERT INTO users (email, password_hash, role, full_name, student_number) "
                         "VALUES ('bad@student.newinti.edu.my', 'x', 'student', 'B', '12AB')")
        synthetic = conn.execute("INSERT INTO users (email, password_hash, role, full_name) "
                                 "VALUES ('student0042@synthetic.example.com', 'x', 'student', 'S') "
                                 "RETURNING student_number").fetchone()[0]
        assert synthetic == "900000042"                             # same in every database

    @pytest.mark.parametrize("password", [
        "Sh0rt!",            # under 8 characters
        "nouppercase1!",     # no uppercase
        "NOLOWERCASE1!",     # no lowercase
        "NoDigitsHere!",     # no number
        "NoSymbols123",      # no symbol
        "Aa1!" + "x" * 70,   # over 72 bytes
        "密码Aa1!" * 13,      # over 72 bytes in UTF-8
    ])
    def test_new_password_rules(self, env, bob, password):
        r = env["client"].post("/api/auth/change-password", headers=bob,
                               json={"current_password": PASSWORD, "new_password": password})
        assert r.status_code == 400

    def test_voluntary_change_needs_current_password(self, env, bob):
        # Bob's password is not temporary, so he must prove he knows it
        r = env["client"].post("/api/auth/change-password", headers=bob,
                               json={"current_password": "wrong-one", "new_password": "Brand#New2026"})
        assert r.status_code == 400 and "current password" in r.json()["detail"]

    def test_self_registration_is_gone(self, env):
        r = env["client"].post("/api/auth/register", json={
            "email": "new1@student.newinti.edu.my", "password": "Password1!", "full_name": "N"})
        assert r.status_code in (404, 405)

    def test_deactivated_account_and_old_token(self, env, admin):
        c = env["client"]
        pw = bcrypt.hashpw(b"Password1!", bcrypt.gensalt()).decode()
        uid = env["conn"].execute("INSERT INTO users (email, password_hash, role, full_name) "
                                  "VALUES ('temp@student.newinti.edu.my', %s, 'student', 'T') RETURNING user_id::text",
                                  (pw,)).fetchone()[0]
        headers = token(env, "temp@student.newinti.edu.my", "Password1!")
        assert c.patch(f"/api/admin/users/{uid}", json={"is_active": False}, headers=admin).status_code == 200
        assert login(env, "temp@student.newinti.edu.my", "Password1!").status_code == 403
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
        assert {"auth.login", "auth.login_failed", "assessment.run", "jd.analyse",
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


# ── Recommendations: cost tiers ──────────────────────────────
@pytest.mark.parametrize("cost,tier", [
    ("Free", "free"), (" free ", "free"), (None, "free"),
    ("Free to audit", "free_to_learn"), ("Free tier", "free_to_learn"), ("Free / $14/mo", "free_to_learn"),
    ("Free trial", "paid"), ("Paid ~$15", "paid"), ("$150 USD", "paid"), ("Low cost", "paid"),
])
def test_cost_tier(cost, tier):
    sys.path.insert(0, str(ROOT))
    from recommendation.engine import cost_tier
    assert cost_tier(cost) == tier


def test_recommendations_free_first(env, alice):
    aid = run(env, alice, role_id=env["da"]).json()["assessment_id"]
    recs = env["client"].get(f"/api/assessments/{aid}/recommendations", headers=alice).json()["recommendations"]
    order = {"free": 1, "free_to_learn": 2, "paid": 3}
    tiers = [[r["cost_tier"] for r in rec["resources"]] for rec in recs]
    assert any(tiers)
    assert all(t == sorted(t, key=order.get) for t in tiers)       # within each skill: free first


# ── New student intake: advisor list -> admin accounts -> first login ──
def upload(env, headers, name, content, mime="text/csv"):
    return env["client"].post("/api/intake/batches", headers=headers, files={"file": (name, content, mime)})


class TestIntake:
    CSV = ("Full Name,Phone Number,Personal Email\n"
           "Mei Ling Tan,+60 12-345 6789,meiling.tan@example.com\n"
           "Arjun Nair,0123456780,arjun.nair@example.com\n"
           "No Email,0123,not-an-email\n"
           "Mei Ling Again,012,MEILING.TAN@example.com\n"
           "Siti Aminah,,siti.aminah@example.com\n").encode()

    def test_full_intake_flow(self, env, advisor, admin, alice):
        c, conn = env["client"], env["conn"]

        # 1. The advisor uploads the list; bad rows are skipped and explained
        assert upload(env, alice, "new.csv", self.CSV).status_code == 403          # students cannot
        r = upload(env, advisor, "new.csv", self.CSV)
        assert r.status_code == 201, r.text
        assert r.json()["students"] == 3
        assert [s["line"] for s in r.json()["skipped"]] == [4, 5]                  # bad email, duplicate
        bid = r.json()["batch_id"]
        assert any(b["batch_id"] == bid and b["pending"] == 3 for b in c.get("/api/intake/batches", headers=advisor).json())

        # 2. The admin lets the system suggest IDs and emails, edits one, rejects one
        assert c.post(f"/api/intake/batches/{bid}/assign", headers=advisor).status_code == 403
        rows = c.post(f"/api/intake/batches/{bid}/assign", headers=admin).json()["rows"]
        assert all(len(r["student_number"]) == 9 and r["school_email"] == f"{r['student_number']}@student.newinti.edu.my"
                   for r in rows)
        mei, arjun, siti = rows
        alice_id = student_number(env, "alice@student.newinti.edu.my")
        patch = lambda row, n, e: c.patch(f"/api/intake/rows/{row['row_id']}", headers=admin,
                                          json={"student_number": n, "school_email": e})
        assert patch(mei, "12345", "x@student.newinti.edu.my").status_code == 422           # not 9 digits
        assert patch(mei, "105000001", "mei@gmail.com").status_code == 400                  # wrong domain
        assert patch(mei, alice_id, "mei@student.newinti.edu.my").status_code == 400        # taken
        assert patch(mei, "105000001", "105000001@student.newinti.edu.my").status_code == 200
        assert c.post(f"/api/intake/rows/{siti['row_id']}/reject", headers=admin, json={"note": "duplicate"}).status_code == 200
        assert c.post(f"/api/intake/rows/{siti['row_id']}/reject", headers=admin, json={}).status_code == 404

        # 3. Accounts are created; each student's personal email gets the details
        done = c.post(f"/api/intake/batches/{bid}/create-accounts", headers=admin, json={}).json()
        assert len(done["created"]) == 2 and not done["failed"]
        assert {d["email_status"] for d in done["created"]} == {"not_sent"}               # no mail server in tests
        mail = next(e for e in c.get("/api/intake/outbox", headers=admin).json()["emails"]
                    if e["to_address"] == "meiling.tan@example.com")
        assert "105000001" in mail["body"] and "105000001@student.newinti.edu.my" in mail["body"]
        temp = re.search(r"Temporary password:\s+(\S+)", mail["body"]).group(1)
        assert c.get("/api/intake/outbox", headers=advisor).status_code == 403

        # 4. First sign-in: email + student ID + temporary password, then a new password is required
        r = login(env, "105000001@student.newinti.edu.my", temp, student_id="105000001")
        assert r.status_code == 200 and r.json()["must_change_password"] is True
        h = {"Authorization": "Bearer " + r.json()["access_token"]}
        assert c.get("/api/students/profile", headers=h).status_code == 403              # blocked until changed
        assert c.get("/api/auth/me", headers=h).json()["student_number"] == "105000001"
        # The temporary password is not asked again: the student has just signed in with it
        assert re.search(r"[A-Z]", temp) and re.search(r"[a-z]", temp) and re.search(r"[0-9]", temp)             and re.search(r"[^A-Za-z0-9]", temp)                                       # meets the rules itself
        change = lambda new: c.post("/api/auth/change-password", headers=h, json={"new_password": new})
        assert change("MyOwnPass9").status_code == 400                                   # no symbol
        assert change(temp).status_code == 400                                           # same as temporary
        assert change("MyOwnPass9!").status_code == 200
        assert c.get("/api/students/profile", headers=h).status_code == 404              # allowed now (no profile yet)
        assert login(env, "105000001@student.newinti.edu.my", temp, student_id="105000001").status_code == 401
        assert login(env, "105000001@student.newinti.edu.my", "MyOwnPass9!", student_id="105000001").status_code == 200

        # The same person cannot be put on a new list again
        again = upload(env, advisor, "again.csv", b"Full Name,Personal Email\nMei Ling,meiling.tan@example.com\n")
        assert again.status_code == 400

        # 5. An admin reset makes the password temporary again
        uid = conn.execute("SELECT user_id::text FROM users WHERE student_number = '105000001'").fetchone()[0]
        assert c.post(f"/api/admin/users/{uid}/reset-password", headers=admin, json={"password": "Reset#2026"}).status_code == 200
        r = login(env, "105000001@student.newinti.edu.my", "Reset#2026", student_id="105000001")
        assert r.json()["must_change_password"] is True

        actions = {a[0] for a in conn.execute("SELECT DISTINCT action FROM audit_log").fetchall()}
        assert {"intake.upload", "intake.reject", "intake.accounts_create", "auth.password_change"} <= actions

    def test_xlsx_upload_and_bad_files(self, env, advisor):
        from openpyxl import Workbook
        wb = Workbook()
        wb.active.append(["Name", "Mobile", "Email"])
        wb.active.append(["Lim Wei", 60123456789, "lim.wei@example.com"])        # Excel number for the phone
        buf = io.BytesIO()
        wb.save(buf)
        r = upload(env, advisor, "students.xlsx", buf.getvalue(),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert r.status_code == 201 and r.json()["students"] == 1, r.text
        rows = env["client"].get(f"/api/intake/batches/{r.json()['batch_id']}", headers=advisor).json()["rows"]
        assert rows[0]["phone"] == "60123456789"
        assert upload(env, advisor, "x.xlsx", b"not a zip").status_code == 400
        assert upload(env, advisor, "x.txt", b"a,b").status_code == 400
        assert upload(env, advisor, "x.csv", b"Phone,Address\n1,2\n").status_code == 400  # no name / email column


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
