#!/usr/bin/env pwsh
Write-Host "===============================================" -ForegroundColor Green
Write-Host "       ML Server for Renal Care Management" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Checking Python installation..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install requirements" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Running Django migrations..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Migration failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting ML Server on port 8001..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Yellow
Write-Host "  - Health Check: http://localhost:8001/health/" -ForegroundColor White
Write-Host "  - ML Health: http://localhost:8001/api/ml/health/" -ForegroundColor White
Write-Host "  - Models Info: http://localhost:8001/api/ml/models/" -ForegroundColor White
Write-Host "  - Dry Weight Prediction: http://localhost:8001/api/ml/predict/dry-weight/" -ForegroundColor White
Write-Host "  - URR Prediction: http://localhost:8001/api/ml/predict/urr/" -ForegroundColor White
Write-Host "  - Hb Prediction: http://localhost:8001/api/ml/predict/hb/" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python manage.py runserver 8001
