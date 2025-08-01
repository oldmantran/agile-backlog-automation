@echo off

REM Agile Backlog Automation - Quick Start
REM This script starts both backend and frontend, and opens the browser

echo ========================================
echo Agile Backlog Automation - Quick Start
echo ========================================
echo.

REM Change to the project root directory
cd /d "%~dp0.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    pushd frontend
    npm install
    popd
)

REM Start the frontend in a new window (it will open browser automatically)
start "Frontend Server" cmd /k "cd frontend && npm start"

REM Wait a moment for frontend to start
ping 127.0.0.1 -n 6 >nul

echo Starting Unified API Server...
echo Backend will be available at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo.
python unified_api_server.py

pause 