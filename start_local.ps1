Write-Host "Starting GeoSentinel AI Locally (Without Docker)" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan

# Check if Python venv exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating Python Virtual Environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Installing/Updating Backend Dependencies..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

Write-Host "Starting FastAPI Backend on Port 8000..." -ForegroundColor Green
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --env-file .env" -WindowStyle Normal

Write-Host "Installing/Updating Frontend Dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install

Write-Host "Starting Next.js Frontend on Port 3000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -Command `"cd '$PWD'; npm run dev`"" -WindowStyle Normal
Set-Location ..

Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "Success! The backend and frontend are starting up in separate windows." -ForegroundColor Green
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan
