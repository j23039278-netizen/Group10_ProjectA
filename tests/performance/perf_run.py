"""
SEAGAS - performance test (Sprint 3, S3-06-01 / S3-06-03 / S3-06-04)

Measures response times of the real backend on the full dataset, against the target
that an assessment returns within 5 seconds.

    python tests/performance/perf_run.py            # from the repository root

What it does:
1. Copies the local database seagas_db to a temporary database (CREATE DATABASE ...
   TEMPLATE seagas_db), so seagas_db itself is never changed. The backend must be
   stopped while it runs (PostgreSQL cannot copy a database that has open connections).
2. Starts the backend (uvicorn) on port 8765 against the copy and times the start-up,
   which includes loading the NLP model.
3. Times each request over HTTP: student sign-in, assessments (keyword and hybrid),
   recommendations, a pasted job description, a CV upload, the student pages, the
   advisor pages over all students, and 10 hybrid assessments at the same time.
4. Writes docs/report_drafts/performance_results.md and .json, stops the backend and
   drops the copy.

Synthetic students only (NFR-05). Passwords: the synthetic accounts share the demo
password; one advisor and the admin get a temporary password in the copy only.
"""

import concurrent.futures as cf
import io
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

import psycopg
import requests

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}/api"
TARGET_S = 5.0
DEMO_PASSWORD = "Seagas@2026"          # every synthetic account (data/generate_synthetic_data.py)
STAFF_PASSWORD = "PerfTest#2026"       # set in the copy only
N = 20                                 # timed requests per endpoint
PARALLEL = 10                          # hybrid assessments at the same time


def env_value(key):
    for line in (BACKEND / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(key + "="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"{key} not found in backend/.env")


RAW_URL = env_value("DATABASE_URL").split("?", 1)[0]
DB_URL = "postgresql://" + RAW_URL.split("://", 1)[1]       # psycopg wants the plain scheme
SOURCE_DB = DB_URL.rsplit("/", 1)[1]
COPY_DB = f"seagas_perf_{os.getpid()}"
COPY_URL = RAW_URL.rsplit("/", 1)[0] + "/" + COPY_DB       # backend: same driver as before
COPY_PG = DB_URL.rsplit("/", 1)[0] + "/" + COPY_DB
ADMIN_URL = DB_URL.rsplit("/", 1)[0] + "/postgres"


def cv_docx(text):
    """A small Word file with one paragraph per sentence (same idea as the CV tests)"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml",
                   '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
                   + "".join(f"<w:p><w:r><w:t>{s}</w:t></w:r></w:p>" for s in text.split(". "))
                   + "</w:body></w:document>")
    return buf.getvalue()


CV_TEXT = ("Final-year Computer Science student. Built a REST API with Python, FastAPI and PostgreSQL. "
           "Used Git, Docker and Linux in a team project. Data analysis with Pandas, NumPy and SQL. "
           "Created dashboards in Power BI and Tableau. Strong communication, teamwork and problem solving. "
           "Internship: supported a cloud migration on AWS. Familiar with JavaScript, React, HTML and CSS")
JD_TEXT = ("We are hiring a Junior Data Analyst. You will clean and analyse data with SQL and Python, build "
           "dashboards in Power BI or Tableau, and present findings to stakeholders. Requirements: degree in "
           "Computer Science or related field; experience with Excel, statistics and data visualisation; good "
           "communication and problem-solving skills; knowledge of machine learning is a plus.")


def summary(times):
    times = sorted(times)
    p95 = times[min(len(times) - 1, int(round(0.95 * (len(times) - 1))))]
    return {"n": len(times), "mean_s": round(statistics.mean(times), 3), "median_s": round(statistics.median(times), 3),
            "p95_s": round(p95, 3), "max_s": round(max(times), 3)}


def timed(fn):
    t = time.perf_counter()
    r = fn()
    return time.perf_counter() - t, r


def main():
    results = {"measured_at": datetime.now().isoformat(timespec="seconds"), "target_s": TARGET_S, "rows": []}
    admin = psycopg.connect(ADMIN_URL, autocommit=True)
    open_conns = admin.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = %s", (SOURCE_DB,)).fetchone()[0]
    if open_conns:
        raise SystemExit(f"{open_conns} connection(s) to {SOURCE_DB} are open: stop the backend first.")
    print(f"Copying {SOURCE_DB} to {COPY_DB} ...")
    t = time.perf_counter()
    admin.execute(f'CREATE DATABASE "{COPY_DB}" TEMPLATE "{SOURCE_DB}"')
    results["copy_db_s"] = round(time.perf_counter() - t, 1)
    server = None
    try:
        # Accounts in the copy: a Dean of Computing and the admin get a known password
        sys.path.insert(0, str(BACKEND))
        os.environ["DATABASE_URL"] = COPY_URL
        import bcrypt
        pw = bcrypt.hashpw(STAFF_PASSWORD.encode(), bcrypt.gensalt()).decode()
        with psycopg.connect(COPY_PG, autocommit=True) as conn:
            advisor = conn.execute("""SELECT u.email FROM users u WHERE u.role = 'advisor' AND u.is_active
                                      AND u.advisor_position = 'dean' ORDER BY u.staff_number LIMIT 1""").fetchone()[0]
            admin_email = conn.execute("SELECT email FROM users WHERE role = 'admin' AND is_active LIMIT 1").fetchone()[0]
            conn.execute("UPDATE users SET password_hash = %s, must_change_password = FALSE WHERE email IN (%s, %s)",
                         (pw, advisor, admin_email))
            students = conn.execute("""
                SELECT u.email, u.student_number, jr.role_id::text
                FROM users u JOIN student_profiles sp ON sp.user_id = u.user_id
                JOIN job_roles jr ON jr.role_name = sp.target_role AND u.course = ANY(jr.courses)
                WHERE u.role = 'student' AND u.is_active AND u.email LIKE '%%@synthetic.example.com'
                  AND NOT COALESCE(u.must_change_password, FALSE)
                ORDER BY u.email LIMIT %s""", (N + PARALLEL,)).fetchall()
            counts = conn.execute("""SELECT (SELECT count(*) FROM users WHERE role = 'student'),
                                            (SELECT count(*) FROM assessments),
                                            (SELECT count(*) FROM skill_match_results),
                                            (SELECT count(*) FROM skills_library WHERE is_active),
                                            (SELECT count(*) FROM job_descriptions)""").fetchone()
        results["data"] = dict(zip(["students", "assessments", "skill_match_rows", "skills", "job_descriptions"], counts))

        # Start the backend against the copy
        print("Starting the backend (loads the NLP model) ...")
        env = {**os.environ, "DATABASE_URL": COPY_URL, "SEAGAS_NO_DOCS": "0", "SMTP_HOST": ""}
        t = time.perf_counter()
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", str(PORT), "--log-level", "warning"],
                                  cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while True:
            try:
                if requests.get(f"http://127.0.0.1:{PORT}/docs", timeout=2).status_code == 200:
                    break
            except requests.RequestException:
                pass
            if server.poll() is not None or time.perf_counter() - t > 300:
                raise SystemExit("The backend did not start.")
            time.sleep(0.5)
        results["startup_s"] = round(time.perf_counter() - t, 1)

        def login(email, password, sid=None):
            data = {"username": email, "password": password}
            if sid:
                data["student_id"] = sid
            r = requests.post(f"{BASE}/auth/login", data=data, timeout=60)
            r.raise_for_status()
            return {"Authorization": "Bearer " + r.json()["access_token"]}

        def add(name, group, times, note=""):
            row = {"name": name, "group": group, **summary(times), "note": note}
            row["meets_target"] = row["p95_s"] <= TARGET_S
            results["rows"].append(row)
            print(f"  {name:55s} mean {row['mean_s']:.3f}s  p95 {row['p95_s']:.3f}s")

        # Cold start: the backend loads the NLP model in a background thread after it starts, so
        # a hybrid request sent straight after start-up waits for it. Timed and reported on its own.
        h0 = login(students[0][0], DEMO_PASSWORD, students[0][1])
        def cold():
            r = requests.post(f"{BASE}/jobs/descriptions", json={"title": "Cold start probe", "raw_text": JD_TEXT}, headers=h0, timeout=60)
            r.raise_for_status()
            requests.post(f"{BASE}/jobs/descriptions/{r.json()['jd_id']}/analyse?method=hybrid", headers=h0, timeout=180).raise_for_status()
        dt, _ = timed(cold)
        results["cold_first_hybrid_s"] = round(dt, 2)
        results["model_ready_after_start_s"] = round(time.perf_counter() - t, 1)
        print(f"  First hybrid request right after start-up: {dt:.2f} s")
        requests.post(f"{BASE}/assessments/run", json={"role_id": students[0][2], "matching_method": "hybrid"}, headers=h0, timeout=120)

        # Student requests, one student after another
        heads, t_login = [], []
        for email, sid, _ in students[:N]:
            dt, h = timed(lambda: login(email, DEMO_PASSWORD, sid))
            t_login.append(dt); heads.append(h)
        add("Sign in (student)", "Student", t_login)

        ids, method_used = {}, {}
        for method in ("keyword", "hybrid"):
            tt = []
            for (email, sid, role_id), h in zip(students[:N], heads):
                dt, r = timed(lambda: requests.post(f"{BASE}/assessments/run", json={"role_id": role_id, "matching_method": method},
                                                    headers=h, timeout=120))
                r.raise_for_status()
                tt.append(dt); ids.setdefault(method, []).append(r.json()["assessment_id"])
                method_used[method] = r.json().get("matching_method")
            add(f"Run assessment, role template ({method})", "Assessment", tt,
                f"method used: {method_used[method]}")

        tt = []
        for aid, h in zip(ids["hybrid"], heads):
            dt, r = timed(lambda: requests.get(f"{BASE}/assessments/{aid}/recommendations", headers=h, timeout=60))
            r.raise_for_status(); tt.append(dt)
        add("Recommendations for an assessment", "Assessment", tt)

        tt_jd, tt_jd_run = [], []
        for h in heads[:10]:
            def jd():
                r = requests.post(f"{BASE}/jobs/descriptions", json={"title": "Junior Data Analyst", "raw_text": JD_TEXT}, headers=h, timeout=60)
                r.raise_for_status()
                jd_id = r.json()["jd_id"]
                requests.post(f"{BASE}/jobs/descriptions/{jd_id}/analyse?method=hybrid", headers=h, timeout=120).raise_for_status()
                return jd_id
            dt, jd_id = timed(jd); tt_jd.append(dt)
            dt, r = timed(lambda: requests.post(f"{BASE}/assessments/run", json={"jd_id": jd_id, "matching_method": "hybrid"},
                                                headers=h, timeout=120))
            r.raise_for_status(); tt_jd_run.append(dt)
        add("Paste a job description and extract its skills (hybrid)", "Job description", tt_jd)
        add("Run assessment against the pasted job description (hybrid)", "Job description", tt_jd_run)

        tt = []
        docx = cv_docx(CV_TEXT)
        for h in heads[:10]:
            dt, r = timed(lambda: requests.post(f"{BASE}/students/cv?method=hybrid", headers=h, timeout=120,
                                                files={"file": ("cv.docx", docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}))
            r.raise_for_status(); tt.append(dt)
        add("Upload a CV and extract its skills (hybrid)", "CV", tt)

        for name, path in (("Student profile", "/students/profile"), ("Assessment history", "/assessments/my/history"),
                           ("Learning progress", "/progress/my"), ("Career paths (all roles of the course)", "/students/career-paths")):
            tt = []
            for h in heads:
                dt, r = timed(lambda: requests.get(BASE + path, headers=h, timeout=60))
                r.raise_for_status(); tt.append(dt)
            add(name, "Student pages", tt)

        # Advisor pages over all students of the Dean's courses
        ha = login(advisor, STAFF_PASSWORD)
        for name, path in (("Cohort overview (status of every student)", "/advisor/cohort/overview"),
                           ("Student list (all students of the courses)", "/advisor/students"),
                           ("Skill gaps (latest assessment of every student)", "/advisor/cohort/skill-gaps"),
                           ("MQF clusters (every skill result)", "/advisor/cohort/mqf-clusters"),
                           ("Learning progress (cohort)", "/advisor/cohort/progress")):
            tt = []
            for _ in range(10):
                dt, r = timed(lambda: requests.get(BASE + path, headers=ha, timeout=120))
                r.raise_for_status(); tt.append(dt)
            add(name, "Advisor pages", tt)

        # Several students at once: 10 hybrid assessments in parallel
        par = students[N:N + PARALLEL]
        par_heads = [login(e, DEMO_PASSWORD, s) for e, s, _ in par]

        def one(i):
            e, s, role_id = par[i]
            dt, r = timed(lambda: requests.post(f"{BASE}/assessments/run", json={"role_id": role_id, "matching_method": "hybrid"},
                                                headers=par_heads[i], timeout=180))
            r.raise_for_status()
            return dt
        t = time.perf_counter()
        with cf.ThreadPoolExecutor(PARALLEL) as ex:
            tt = list(ex.map(one, range(PARALLEL)))
        wall = time.perf_counter() - t
        add(f"{PARALLEL} hybrid assessments at the same time", "Concurrency", tt, f"all {PARALLEL} done in {wall:.2f} s")
    finally:
        if server:
            server.terminate()
            try:
                server.wait(15)
            except subprocess.TimeoutExpired:
                server.kill()
        admin.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()", (COPY_DB,))
        admin.execute(f'DROP DATABASE IF EXISTS "{COPY_DB}"')
        admin.close()

    results["environment"] = {"os": f"{platform.system()} {platform.release()}", "python": platform.python_version(),
                              "cpu": platform.processor(), "cpu_count": os.cpu_count(),
                              "setup": "backend (uvicorn, 1 worker) and PostgreSQL 17 on the same laptop; requests over HTTP on localhost"}
    out = ROOT / "docs" / "report_drafts"
    (out / "performance_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_markdown(results, out / "performance_results.md")
    print("Written:", out / "performance_results.md")


def write_markdown(res, path):
    d, e = res["data"], res["environment"]
    lines = [
        "# Performance test results (S3-06)",
        "",
        f"Measured {res['measured_at']} with `tests/performance/perf_run.py` on a copy of the local database.",
        f"Target: an assessment returns within **{res['target_s']:g} s** (the S3-06 response-time target).",
        "",
        f"**Data:** {d['students']:,} students, {d['assessments']:,} assessments, {d['skill_match_rows']:,} skill results, "
        f"{d['skills']} skills, {d['job_descriptions']} job descriptions.  ",
        f"**Machine:** {e['os']}, {e['cpu_count']} logical CPUs ({e['cpu']}), Python {e['python']}; {e['setup']}.  ",
        f"**Backend start-up:** the API answers {res['startup_s']} s after it is started. The NLP model then loads in a "
        f"background thread; a hybrid request sent at once waited **{res['cold_first_hybrid_s']} s** for it, and the model "
        f"was ready {res['model_ready_after_start_s']} s after start. This happens once per start (e.g. after a deployment); "
        "every request below was timed after that.",
        "",
        "| Request | Group | n | Mean (s) | Median (s) | P95 (s) | Max (s) | Within 5 s | Note |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in res["rows"]:
        lines.append(f"| {r['name']} | {r['group']} | {r['n']} | {r['mean_s']:.3f} | {r['median_s']:.3f} | {r['p95_s']:.3f} | "
                     f"{r['max_s']:.3f} | {'Yes' if r['meets_target'] else '**No**'} | {r['note']} |")
    slow = max(res["rows"], key=lambda r: r["p95_s"])
    lines += [
        "",
        f"All {len(res['rows'])} measured requests meet the 5 s target at P95: "
        + ("yes." if all(r["meets_target"] for r in res["rows"]) else "**no** (see the rows marked No)."),
        f"The slowest is \"{slow['name']}\" (P95 {slow['p95_s']:.2f} s).",
        "",
        "Notes: times are measured by the client over HTTP on the same machine, so network delay to a real",
        "server is not included. Each request is timed separately after one warm-up assessment; the start-up",
        "time is reported on its own because the model is loaded only once when the backend starts.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
