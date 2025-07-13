@echo off
echo.
echo ====================================================
echo  TRON BACKLOG AUTOMATION - SETUP AND START
echo ====================================================
echo.

:: Set color for Tron theme
color 0B

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo [1/5] Checking Python environment...

:: Install Python dependencies
if not exist venv (
    echo [2/5] Creating Python virtual environment...
    python -m venv venv
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo [3/5] Setting up frontend...
cd frontend

:: Install Node.js dependencies
if not exist node_modules (
    echo [3/5] Installing Node.js dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
)

echo [4/5] Building frontend...
npm run build
if errorlevel 1 (
    echo ERROR: Failed to build frontend
    cd ..
    pause
    exit /b 1
)

cd ..

echo [5/5] Starting Tron Backlog Automation Server...
echo.
echo ====================================================
echo  🎮 TRON INTERFACE READY
echo  🌐 Opening browser to: http://localhost:8000
echo  🔧 API docs available at: http://localhost:8000/docs
echo ====================================================
echo.

:: Start the server and open browser
start http://localhost:8000
python tron_api_server.py

pause
