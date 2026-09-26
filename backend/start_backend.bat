@echo off
REM ============================================================
REM SEAGAS - one-click local setup + start backend (Windows)
REM Double-click this file. Safe to run again: every step checks first.
REM   1. create seagas_db if missing
REM   2. run database\schema.sql if tables are missing
REM   3. load 5000 synthetic students if none are loaded
REM   4. install Python packages and start FastAPI
REM Requires: PostgreSQL 17 (postgres password = postgres123), Python 3.10+
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".env" (
    echo Creating backend\.env with the team's local settings ...
    > ".env" echo DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/seagas_db
    >> ".env" echo SECRET_KEY=seagas_super_secret_key_change_in_production_2026
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

echo [3/4] Checking synthetic students ...
set "SYN=0"
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM users WHERE email LIKE '%%@synthetic.example.com'"`) do set "SYN=%%i"
if "%SYN%"=="0" (
    echo       loading 5000 students, please wait ...
    psql -d seagas_db -q -v ON_ERROR_STOP=1 -f "..\data\output\seed_synthetic_students.sql"
    if errorlevel 1 goto :fail
) else (
    echo       %SYN% synthetic students already loaded
)
for /f "usebackq delims=" %%i in (`psql -d seagas_db -tAc "SELECT count(*) FROM users"`) do echo       users in database: %%i

echo [4/4] Installing Python packages ...
%PY% -m pip install -q -r requirements.txt "psycopg[binary]" "pydantic[email]" python-multipart
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  Backend starting at http://127.0.0.1:8000/docs
echo  Test login:  student0001@synthetic.example.com / Seagas@2026
echo  Press Ctrl+C in this window to stop the server.
echo ============================================================
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000/docs"
%PY% -m uvicorn main:app --reload
goto :end

:fail
echo.
echo Setup stopped because of the error above.

:end
pause
