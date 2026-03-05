#!/bin/bash
set -e
echo "Starting PM Launch Agent..."

cd "$(dirname "$0")/backend"
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!

echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop"
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
