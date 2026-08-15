#!/bin/bash
echo "========================================================"
echo "        AutoInspect AI Full-Stack Launcher (Unix)       "
echo "========================================================"
echo ""

# 1. Start Backend in background
echo "[1/2] Starting FastAPI Backend on port 8000..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 2. Start Frontend
echo "[2/2] Starting Vite Frontend on port 5173..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
cd ..

echo ""
echo "AutoInspect AI is running!"
echo "Web UI: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
