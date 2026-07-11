@echo off
echo Starting GeoSentinel AI Locally (Without Docker)
echo ------------------------------------------------

if not exist "venv\Scripts\python.exe" (
    echo Creating Python Virtual Environment...
    python -m venv venv
)

echo Installing/Updating Backend Dependencies...
call .\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

echo Starting FastAPI Backend on Port 8000...
start "GeoSentinel Backend" .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --env-file .env

echo Installing/Updating Frontend Dependencies...
cd frontend
call npm install

echo Starting Next.js Frontend on Port 3000...
start "GeoSentinel Frontend" cmd /c "npm run dev"
cd ..

echo ------------------------------------------------
echo Success! The backend and frontend are starting up in separate windows.
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo ------------------------------------------------
pause
