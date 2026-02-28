@echo off
REM IDX Stock Screener — Start API + Web (Windows)
REM Usage: start.bat

echo Starting IDX Stock Screener...
echo.

REM Start API (FastAPI) in new window
echo Starting API server (port 8000)...
start "IDX-API" cmd /k "cd /d %~dp0api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for API to start
timeout /t 2 /nobreak >nul

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
