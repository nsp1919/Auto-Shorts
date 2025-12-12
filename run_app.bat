@echo off
echo Starting Auto Shorts Generator...

:: Start Backend
echo Starting Backend (FastAPI)...
start "AutoShorts Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn main:app --reload"

:: Wait a moment for backend to init
timeout /t 3 /nobreak >nul

:: Start Frontend
echo Starting Frontend (Next.js)...
start "AutoShorts Frontend" cmd /k "cd frontend && npm run dev"

echo Done! Services are starting in new windows.
echo - Frontend: http://localhost:3000
echo - Backend: http://localhost:8000/docs
pause
