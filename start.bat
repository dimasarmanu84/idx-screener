@echo off
REM IDX Stock Screener — Start API + Web (Windows)
REM Usage: double-click start.bat or run from cmd

echo Starting IDX Stock Screener...
echo.

REM Check required .env files
if not exist "%~dp0api\.env" (
    echo [WARNING] api\.env not found!
    echo   Copy api\.env.example to api\.env and fill in your values.
    echo.
)
if not exist "%~dp0web\.env" (
    echo [WARNING] web\.env not found!
    echo   Copy web\.env.example to web\.env and fill in your Google Client ID.
    echo.
)

REM Start API (FastAPI) in new window
echo Starting API server (port 8000)...
start "IDX-API" cmd /k "cd /d %~dp0api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for API to start
timeout /t 3 /nobreak >nul

REM Start Web (SvelteKit) in new window
echo Starting Web server (port 5173)...
start "IDX-Web" cmd /k "cd /d %~dp0web && npm run dev"

echo.
echo ==================================
echo   IDX Stock Screener Running
echo   Web:  http://localhost:5173
echo   API:  http://localhost:8000
echo   Close the CMD windows to stop
echo ==================================
echo.
