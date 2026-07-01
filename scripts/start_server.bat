@echo off
echo ===============================================
echo       ML Server for Renal Care Management
echo ===============================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Running Django migrations...
python manage.py migrate
if errorlevel 1 (
    echo Error: Migration failed
    pause
    exit /b 1
)

echo.
echo Starting ML Server on port 8001...
echo Server will be available at: http://localhost:8001
echo.
echo Available endpoints:
echo   - Health Check: http://localhost:8001/health/
echo   - ML Health: http://localhost:8001/api/ml/health/
echo   - Models Info: http://localhost:8001/api/ml/models/
echo   - Dry Weight Prediction: http://localhost:8001/api/ml/predict/dry-weight/
echo   - URR Prediction: http://localhost:8001/api/ml/predict/urr/
echo   - Hb Prediction: http://localhost:8001/api/ml/predict/hb/
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver 8001
