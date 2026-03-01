#!/usr/bin/env bash
# Start both the dashboard backend and frontend for development.
#
# Usage:
#   ./run.sh           # Start dashboard (API + React)
#   ./run.sh lookup    # Start local vector DB lookup tool

set -e

if [ "$1" = "lookup" ]; then
    echo "Starting Logian Vector DB Lookup..."
    source venv/bin/activate 2>/dev/null || true
    python src/lookup.py
    exit 0
fi

echo "Starting Logian Sentiment Dashboard..."
echo ""

# Start backend
source venv/bin/activate 2>/dev/null || true
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
cd dashboard && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000  (PID $BACKEND_PID)"
echo "  Frontend: http://localhost:5173  (PID $FRONTEND_PID)"
echo ""
echo "  Press Ctrl+C to stop both"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
