@echo off
echo ========================================
echo   Astrology AI - API Server Startup
echo ========================================
echo.

echo [1/3] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo.

echo [2/3] Creating admin user (if not exists)...
python create_admin.py
echo.

echo [3/3] Starting API server...
echo.
echo API will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python api.py
