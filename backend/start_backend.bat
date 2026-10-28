@echo off
REM ============================================================
REM SEAGAS - one-click local setup + start backend (Windows)
REM Double-click this file. Safe to run again: every step checks first.
REM   1. create seagas_db if missing
REM   2. run database\schema.sql if tables are missing,
REM      then migrate_existing_db.sql, seed_skills_library_v2.sql,
REM      seed_job_role_skills.sql, seed_recommendations_library_final.sql
REM      and seed_business_skills.sql
REM   3. load 5000 synthetic students if none are loaded
REM      (old data with repeated student names is replaced)
REM   4. install Python packages, load the JD dataset (if present), offer to create
REM      the first admin, start FastAPI
REM Requires: PostgreSQL 17 (postgres password = postgres123), Python 3.10+
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".env" (
    echo Creating backend\.env with the team's local settings ...
    > ".env" echo DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/seagas_db
    >> ".env" echo ALGORITHM=HS256
    >> ".env" echo ACCESS_TOKEN_EXPIRE_MINUTES=30
)

set "PATH=C:\Program Files\PostgreSQL\17\bin;%PATH%"
set "PGPASSWORD=postgres123"
set "PGCLIENTENCODING=UTF8"
set "PGHOST=localhost"
set "PGUSER=postgres"

REM Find a real Python (the Microsoft Store "python" alias does not count)
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
    echo [ERROR] Python is not installed.
    echo         Install Python 3.12 from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" on the first install screen.
    echo         Then close this window and double-click start_backend.bat again.
    goto :fail
)

REM Login tokens are signed with SECRET_KEY: give .env a private random one
%PY% ensure_secret_key.py
if errorlevel 1 goto :fail

where psql >nul 2>&1
if errorlevel 1 (
    echo [ERROR] psql not found. Is PostgreSQL 17 installed in C:\Program Files\PostgreSQL\17 ?
    goto :fail
)


echo.
echo [1/4] Checking database seagas_db ...
set "DBEXISTS="
for /f "usebackq delims=" %%i in (`psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='seagas_db'"`) do set "DBEXISTS=%%i"
if "%DBEXISTS%"=="1" (
    echo       already exists
) else (
    psql -d postgres -c "CREATE DATABASE seagas_db;"
    if errorlevel 1 (
        echo [ERROR] Could not connect/create database. Check the postgres password is postgres123.
        goto :fail
    )
)

echo [2/4] Checking tables ...
set "HASTABLES="
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT to_regclass('public.users') IS NOT NULL"`) do set "HASTABLES=%%i"
if "%HASTABLES%"=="t" (
    echo       tables already exist
) else (
    psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\database\schema.sql"
    if errorlevel 1 goto :fail
    echo       schema.sql loaded
)
REM Brings databases created from an older schema.sql up to date (idempotent).
psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\database\migrate_existing_db.sql"
if errorlevel 1 goto :fail

REM Both seeds are idempotent (upsert), so they always run: this also brings
REM older local databases up to the latest skills library v2 and role mappings.
echo [2b/4] Loading skills library v2 ...
psql -d seagas_db -q -v ON_ERROR_STOP=1 -o NUL -f "..\database\seed_skills_library_v2.sql"
if errorlevel 1 goto :fail
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM skills_library"`) do echo       skills_library: %%i skills

echo [2c/4] Loading job role skills ...
psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\database\seed_job_role_skills.sql"
if errorlevel 1 goto :fail
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM job_role_skills"`) do echo       job_role_skills: %%i entries

REM Needs the skills library above. ON CONFLICT DO NOTHING on uq_resource_skill,
REM so running it on every start never adds duplicates.
echo [2d/4] Loading recommendations library ...
psql -d seagas_db -q -v ON_ERROR_STOP=1 -o NUL -f "..\database\seed_recommendations_library_final.sql"
if errorlevel 1 goto :fail
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM recommendations_library"`) do echo       recommendations_library: %%i resources

REM Learning resources for the Business skills, and which courses see each skill.
echo [2e/4] Loading Business learning resources ...
psql -d seagas_db -q -v ON_ERROR_STOP=1 -o NUL -f "..\database\seed_business_skills.sql"
if errorlevel 1 goto :fail
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM recommendations_library r JOIN skills_library sl USING (skill_id) WHERE sl.source = 'v3'"`) do echo       Business learning resources: %%i

echo [3/4] Checking synthetic students ...
set "SYN=0"
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM users WHERE email LIKE '%%@synthetic.example.com'"`) do set "SYN=%%i"
REM Students loaded before the unique-names fix have repeated names: replace them
set "DUPNAMES=0"
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) - count(DISTINCT full_name) FROM users WHERE email LIKE '%%@synthetic.example.com'"`) do set "DUPNAMES=%%i"
if not "%DUPNAMES%"=="0" (
    echo       old synthetic data found ^(%DUPNAMES% repeated names^), replacing it ...
    psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\data\delete_synthetic_data.sql"
    if errorlevel 1 goto :fail
    set "SYN=0"
)
REM Data from an older generator run (e.g. before the Business students): replace it.
REM ..\data\output\DATA_VERSION is written by data\generate_synthetic_data.py;
REM .synthetic_data_version (not in git) is the version this machine loaded.
set "DATA_VER="
if exist "..\data\output\DATA_VERSION" set /p DATA_VER=<"..\data\output\DATA_VERSION"
set "LOADED_VER=none"
if exist ".synthetic_data_version" set /p LOADED_VER=<".synthetic_data_version"
if defined DATA_VER if not "%SYN%"=="0" if not "%DATA_VER%"=="%LOADED_VER%" (
    echo       synthetic data changed ^(%LOADED_VER% -^> %DATA_VER%^), replacing it ...
    psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\data\delete_synthetic_data.sql"
    if errorlevel 1 goto :fail
    set "SYN=0"
)
if "%SYN%"=="0" (
    echo       loading 5000 students, please wait ...
    psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\data\output\seed_synthetic_students.sql"
    if errorlevel 1 goto :fail
    REM Courses: programme names matching each synthetic student's course (idempotent)
    psql -d seagas_db -q -v ON_ERROR_STOP=1 -o NUL -f "..\database\migrate_existing_db.sql"
    if errorlevel 1 goto :fail
) else (
    echo       %SYN% synthetic students already loaded
)
if defined DATA_VER (>".synthetic_data_version" echo %DATA_VER%)
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM users"`) do echo       users in database: %%i

echo [4/4] Installing Python packages ...
%PY% -m pip install -q -r requirements.txt "psycopg[binary]" "pydantic[email]" python-multipart
if errorlevel 1 goto :fail
REM Semantic / hybrid NLP needs nlp\requirements.txt (torch, ~1 GB). Without it the
REM backend still runs and uses keyword matching, so it is optional here.
%PY% -c "import sentence_transformers, spacy, en_core_web_sm" >nul 2>&1
if errorlevel 1 (
    echo       NLP semantic/hybrid not installed - keyword matching will be used.
    echo       To enable it: %PY% -m pip install -r ..\nlp\requirements.txt
) else (
    echo       NLP semantic/hybrid packages found
)

REM The advisor dashboard needs assessment data: assess the synthetic students
REM (same code as the website). Assesses students with none yet, and every
REM synthetic student once more when the matching rules changed
REM (nlp\config.py MATCH_RULES_VERSION); otherwise it does nothing.
echo [4c/4] Checking synthetic assessments ...
%PY% "..\data\run_assessments.py" --auto
if errorlevel 1 goto :fail

REM Advisor accounts are created by an admin, so the first admin has to exist.
REM create_admin.py asks for the email and password; nothing is hard-coded.
echo [4a/4] Checking admin account ...
set "ADMINS="
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM users WHERE role='admin' AND is_active"`) do set "ADMINS=%%i"
if "%ADMINS%"=="0" (
    echo       no admin account yet - admins create advisor accounts.
    choice /C YN /M "      Create an admin account now"
    if not errorlevel 2 %PY% create_admin.py
) else (
    echo       %ADMINS% admin account^(s^)
)

echo [4b/4] Checking JD dataset ...
if exist "..\data\jd_dataset\jd_dataset.csv" (
    %PY% "..\data\jd_dataset\load_jds.py"
    if errorlevel 1 goto :fail
) else (
    echo       no data\jd_dataset\jd_dataset.csv yet - skipped
)

echo.
echo ============================================================
echo  Backend starting at http://127.0.0.1:8000/docs
echo  Test login:  student0001@synthetic.example.com / ID 900000001 / Seagas@2026
echo  Press Ctrl+C in this window to stop the server.
echo ============================================================
REM start_all.bat sets SEAGAS_NO_DOCS=1 so only the frontend page opens
if not defined SEAGAS_NO_DOCS start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000/docs"
%PY% -m uvicorn main:app --reload
goto :end

:fail
echo.
echo Setup stopped because of the error above.

:end
pause
