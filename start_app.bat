@echo off
title HomePageScan Launcher
echo ==========================================
echo Starting HomePageScan Services...
echo ==========================================

:: Start Backend in a new window
echo Starting Backend (FastAPI)...
start "HomePageScan Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000"

:: Start Frontend in a new window
echo Starting Frontend (Vue)...
start "HomePageScan Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo Services are launching!
echo ------------------------------------------
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:5173
echo ==========================================
echo.
echo You can close this window if you want, 
echo but the other two windows must remain open.
pause
