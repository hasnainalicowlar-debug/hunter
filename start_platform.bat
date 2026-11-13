@echo off
title Pakistan Food Business Intelligence & POS Platform
color 0A
echo ======================================================================
echo    PAKISTAN FOOD BUSINESS & RESTAURANT POS INTELLIGENCE PLATFORM
echo ======================================================================
echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+.
    pause
    exit /b
)

echo.
echo [1/3] Verifying Database Schema and Initial Seeding...
python database\db_manager.py

echo.
echo [2/3] Verifying Master Excel and CSV Exports...
python exports\export_generator.py

echo.
echo [3/3] Starting Web Server on http://localhost:5000 ...
echo Press Ctrl+C to terminate the server.
echo.
start http://localhost:5000
python api\server.py

pause
