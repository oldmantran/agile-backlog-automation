@echo off
setlocal enabledelayedexpansion

:: Ensure the window stays open if there's an error
if "%1" neq "internal" (
    echo Running setup script...
    cmd /k "%~f0" internal
    exit /b
)

echo ===============================================
echo  Agile Backlog Automation - Setup Assistant
echo ===============================================
echo.

echo Current directory: %CD%
echo.

echo Step 1: Installing Python dependencies...
if not exist requirements.txt (
    echo [ERROR] requirements.txt not found in current directory
    echo Please make sure you're running this from the project root
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Check if virtual environment exists
if exist .venv\Scripts\python.exe (
    echo [OK] Found virtual environment
    set PYTHON_CMD=.venv\Scripts\python.exe
    set PIP_CMD=.venv\Scripts\pip.exe
) else (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        echo Using system Python instead
        set PYTHON_CMD=python
        set PIP_CMD=pip
    ) else (
        echo [OK] Virtual environment created
        set PYTHON_CMD=.venv\Scripts\python.exe
        set PIP_CMD=.venv\Scripts\pip.exe
    )
)

%PIP_CMD% install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    echo Please check your Python installation
    echo Error code: %errorlevel%
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

echo.
echo Step 2: Checking Node.js installation...

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js found
    goto :check_npm
) else (
    echo [ERROR] Node.js not found
    goto :install_nodejs
)

:check_npm
:: Check if npm is available
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] npm found
    goto :setup_frontend
) else (
    echo [ERROR] npm not found, but Node.js is installed
    goto :install_nodejs
)

:install_nodejs
echo.
echo Node.js is required for the frontend but was not found.
echo.
echo Please install Node.js:
echo 1. Go to https://nodejs.org/
echo 2. Download the LTS version
echo 3. Install with default settings
echo 4. Restart this command prompt
echo 5. Run this script again
echo.
echo For now, we'll start the backend API server only.
echo You can access the API documentation at http://localhost:8000/docs
echo.
goto :start_backend_only

:setup_frontend
echo.
echo Step 3: Setting up frontend...
if not exist frontend (
    echo [ERROR] Frontend directory not found
    echo Please make sure you're running this from the project root
    pause
    exit /b 1
)

cd frontend
if not exist package.json (
    echo [ERROR] package.json not found in frontend directory
    echo There might be an issue with the frontend setup
    cd ..
    pause
    exit /b 1
)

if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install frontend dependencies
        echo Error code: !errorlevel!
        echo Starting backend only...
        cd ..
        pause
        goto :start_backend_only
    )
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies already installed
)
cd ..

echo.
echo Step 4: Starting both servers...
echo Backend API: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.

if not exist api_server.py (
    echo [ERROR] api_server.py not found
    echo Please make sure you're running this from the project root
    pause
    exit /b 1
)

echo Starting backend server...
start "Backend API Server" cmd /k "%PYTHON_CMD% api_server.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting frontend server...
start "Frontend Dev Server" cmd /k "cd frontend && npm start"

echo.
echo [OK] Both servers are starting in separate windows
echo - Backend API: http://localhost:8000
echo - Frontend UI: http://localhost:3000
echo - API Documentation: http://localhost:8000/docs
echo.
echo You can close this window now.
echo The servers are running in separate windows.
pause
exit /b 0

:start_backend_only
echo.
echo Starting backend API server only...
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Note: Install Node.js to use the frontend interface
echo.

if not exist api_server.py (
    echo [ERROR] api_server.py not found
    echo Please make sure you're running this from the project root
    pause
    exit /b 1
)

echo Press Ctrl+C to stop the server when you're done testing...
%PYTHON_CMD% api_server.py
pause
