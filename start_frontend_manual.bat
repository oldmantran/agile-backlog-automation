@echo off
echo Manual Frontend Startup Script
echo ==============================

echo.
echo This script helps start the frontend when automatic detection fails.
echo.

cd frontend

echo Checking for Node.js installation...

:: Try different npm commands
echo Trying: npm --version
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ npm found in PATH
    set NPM_CMD=npm
    goto :install_deps
)

echo Trying: npm.cmd --version
npm.cmd --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ npm.cmd found in PATH
    set NPM_CMD=npm.cmd
    goto :install_deps
)

echo Trying: node --version
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Node.js found, trying to use npx
    set NPM_CMD=npx npm
    goto :install_deps
)

echo.
echo ❌ Could not find npm or Node.js
echo.
echo Please ensure Node.js is installed:
echo 1. Download from https://nodejs.org/
echo 2. Install with default options
echo 3. Restart your command prompt
echo 4. Try running this script again
echo.
pause
exit /b 1

:install_deps
echo.
echo Installing dependencies with: %NPM_CMD%
%NPM_CMD% install
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    echo.
    echo Try these troubleshooting steps:
    echo 1. Delete the node_modules folder
    echo 2. Delete package-lock.json
    echo 3. Run: npm cache clean --force
    echo 4. Try again
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Dependencies installed successfully
echo.
echo Starting development server...
echo The frontend will open in your browser at http://localhost:3000
echo Press Ctrl+C to stop the server
echo.

%NPM_CMD% start

pause
