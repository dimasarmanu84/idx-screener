#!/bin/bash
# IDX Stock Screener — Start API + Web
# Usage: ./start.sh

ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $API_PID $WEB_PID 2>/dev/null
    wait $API_PID $WEB_PID 2>/dev/null
    echo "Done."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Detect Python command (python3 for macOS/Linux, python for Windows)
if command -v python3 &>/dev/null; then
    PY=python3
else
    PY=python
fi

# Start API (FastAPI)
echo "Starting API server (port 8000)..."
cd "$ROOT/api"
$PY -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start Web (SvelteKit)
echo "Starting Web server (port 5173)..."
cd "$ROOT/web"
npm run dev &
WEB_PID=$!

echo ""
echo "=================================="
echo "  IDX Stock Screener Running"
echo "  Web:  http://localhost:5173"
echo "  API:  http://localhost:8000"
echo "  Ctrl+C to stop"
echo "=================================="
echo ""

wait
