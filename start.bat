@echo off
title AutoInspect AI - Launcher
echo ========================================================
echo         AutoInspect AI Full-Stack Launcher              
echo ========================================================
echo.

:: Add portable dev_tools to PATH if present
set "PATH=C:\Users\VISHNU\dev_tools\node-v20.18.0-win-x64;C:\Users\VISHNU\dev_tools\python311;C:\Users\VISHNU\dev_tools\python311\Scripts;%PATH%"

:: 1. Launch FastAPI Backend
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "AutoInspect AI - Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 2. Launch React Frontend
echo [2/2] Starting React + Vite Frontend on http://127.0.0.1:5173 ...
start "AutoInspect AI - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 127.0.0.1 --port 5173"

:: 3. Open Web Browser
timeout /t 3 /nobreak >nul
echo Opening web browser to http://localhost:5173 ...
start http://localhost:5173

echo.
echo ========================================================
echo  AutoInspect AI is now live!
echo  Web UI:   http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ========================================================
echo.
pause
