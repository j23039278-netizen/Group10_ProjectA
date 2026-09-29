@echo off
REM ============================================================
REM SEAGAS - one-click start: backend + frontend (Windows)
REM Double-click this file. It opens two windows:
REM   "SEAGAS Backend"  -> backend\start_backend.bat  (http://127.0.0.1:8000)
REM   "SEAGAS Frontend" -> frontend\start_frontend.bat (http://localhost:5173)
REM Close those windows (or press Ctrl+C in them) to stop the servers.
REM ============================================================
setlocal
cd /d "%~dp0"

set "SEAGAS_NO_DOCS=1"

echo Starting backend ...
start "SEAGAS Backend" /D "%~dp0backend" cmd /c start_backend.bat

echo Starting frontend ...
start "SEAGAS Frontend" /D "%~dp0frontend" cmd /c start_frontend.bat

echo Waiting for backend (first run may take a few minutes to load data) ...
set /a TRIES=0
:wait_backend
curl -s -o nul http://127.0.0.1:8000/docs && goto :wait_frontend
set /a TRIES+=1
if %TRIES% GEQ 300 (
    echo [WARN] Backend not responding yet - check the "SEAGAS Backend" window.
    goto :wait_frontend
)
timeout /t 2 /nobreak >nul
goto :wait_backend

:wait_frontend
echo Waiting for frontend ...
set /a TRIES=0
:wait_frontend_loop
curl -s -o nul http://localhost:5173 && goto :open
set /a TRIES+=1
if %TRIES% GEQ 150 (
    echo [WARN] Frontend not responding yet - check the "SEAGAS Frontend" window.
    goto :end
)
timeout /t 2 /nobreak >nul
goto :wait_frontend_loop

:open
start http://localhost:5173
echo.
echo ============================================================
echo  SEAGAS is running
echo    Frontend: http://localhost:5173
echo    Backend : http://127.0.0.1:8000/docs
echo  Test login: student0001@synthetic.example.com / Seagas@2026
echo  To stop: close the "SEAGAS Backend" and "SEAGAS Frontend" windows.
echo ============================================================

:end
echo.
echo This window can be closed.
pause
