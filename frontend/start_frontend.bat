@echo off
echo ============================================
echo  SEAGAS Frontend Starting...
echo  React + Vite
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Installing / updating packages...
REM Runs every time so packages added by teammates (package.json) are installed too;
REM it takes only a few seconds when nothing has changed.
call npm install --no-audit --no-fund
if errorlevel 1 (
    echo [ERROR] npm install failed. Check your internet connection and run it again.
    pause
    exit /b 1
)

echo.
echo [2/2] Starting frontend dev server...
echo.
echo ============================================
echo  Frontend running at http://localhost:5173
echo  Press Ctrl+C to stop the server.
echo ============================================
echo.

npm run dev
pause