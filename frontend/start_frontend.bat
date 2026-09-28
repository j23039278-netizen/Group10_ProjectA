@echo off
echo ============================================
echo  SEAGAS Frontend Starting...
echo  React + Vite
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Checking node_modules...
if not exist "node_modules" (
    echo node_modules not found. Installing...
    npm install
) else (
    echo node_modules already exists.
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