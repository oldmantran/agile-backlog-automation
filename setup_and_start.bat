@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo  Agile Backlog Automation - Setup Assistant
echo ===============================================
echo.

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    echo Please check your Python installation
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

echo.
echo Step 2: Checking Node.js installation...

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Node.js found
    goto :check_npm
) else (
    echo ❌ Node.js not found
    goto :install_nodejs
)

:check_npm
:: Check if npm is available
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ npm found
    goto :setup_frontend
) else (
    echo ❌ npm not found, but Node.js is installed
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
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
    if !errorlevel! neq 0 (
        echo ❌ Failed to install frontend dependencies
        echo Starting backend only...
        cd ..
        goto :start_backend_only
    )
    echo ✅ Frontend dependencies installed
) else (
    echo ✅ Frontend dependencies already installed
)
cd ..

echo.
echo Step 4: Starting both servers...
echo 📡 Backend API: http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Starting backend server...
start "Backend API Server" cmd /k "python api_server.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting frontend server...
start "Frontend Dev Server" cmd /k "cd frontend && npm start"

echo.
echo ✅ Both servers are starting in separate windows
echo Close this window or press any key to continue...
pause >nul
exit /b 0

:start_backend_only
echo.
echo Starting backend API server only...
echo 📡 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Note: Install Node.js to use the frontend interface
echo.
python api_server.py
pause
