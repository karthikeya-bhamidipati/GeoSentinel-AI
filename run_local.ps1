# run_local.ps1
# Script to run GeoSentinel AI locally without Docker

Write-Host "============================================="
Write-Host "GeoSentinel AI - Local Environment Setup"
Write-Host "============================================="

# 1. Setup Backend
Write-Host "`n[1/2] Setting up Python Backend..."

if (-Not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

Write-Host "Installing Python dependencies (this may take a minute)..."
# Use call operator to run activate script and then pip in same scope,
# or simply use the executable directly:
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

# 2. Setup Frontend
Write-Host "`n[2/2] Setting up Next.js Frontend..."
cd frontend
npm install
cd ..

Write-Host "`n============================================="
Write-Host "Setup Complete! You can now run the servers."
Write-Host "============================================="
Write-Host "`nTo start the BACKEND server, open a new terminal and run:"
Write-Host "  .\venv\Scripts\activate"
Write-Host "  $env:PYTHONPATH='.'"
Write-Host "  uvicorn backend.app.main:app --reload"
Write-Host "`nTo start the FRONTEND server, open another terminal and run:"
Write-Host "  cd frontend"
Write-Host "  npm run dev"
Write-Host "`nThen open http://localhost:3000 in your browser!"
