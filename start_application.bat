@echo off
echo ==========================================
echo  Agile Backlog Automation Startup Script
echo ==========================================
echo.

echo Checking virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at .venv\Scripts\activate.bat
    echo Please ensure you have set up the Python virtual environment first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting Backend API Server...
echo Backend will be available at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo.

echo Choose which server to start:
echo 1. Main API Server (api_server.py)
echo 2. Tron API Server (tron_api_server.py) - includes frontend
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo Starting Main API Server...
    python api_server.py
) else if "%choice%"=="2" (
    echo Starting Tron API Server...
    python tron_api_server.py
) else (
    echo Invalid choice. Starting Tron API Server by default...
    python tron_api_server.py
)

echo.
echo Server stopped.
pause
