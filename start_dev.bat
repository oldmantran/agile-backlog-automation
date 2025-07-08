@echo off
echo Starting Agile Backlog Automation Development Servers
echo ====================================================

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Checking for Node.js and npm...

:: Try to find npm
where npm >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Found npm in PATH
    set NPM_CMD=npm
    goto :start_servers
)

:: Try common npm locations
if exist "%APPDATA%\npm\npm.cmd" (
    echo ✅ Found npm at %APPDATA%\npm\npm.cmd
    set NPM_CMD=%APPDATA%\npm\npm.cmd
    goto :start_servers
)

if exist "C:\Program Files\nodejs\npm.cmd" (
    echo ✅ Found npm at C:\Program Files\nodejs\npm.cmd
    set NPM_CMD=C:\Program Files\nodejs\npm.cmd
    goto :start_servers
)

if exist "C:\Program Files (x86)\nodejs\npm.cmd" (
    echo ✅ Found npm at C:\Program Files (x86)\nodejs\npm.cmd
    set NPM_CMD=C:\Program Files (x86)\nodejs\npm.cmd
    goto :start_servers
)

echo ❌ npm not found. Please install Node.js from https://nodejs.org/
echo    Make sure to restart your command prompt after installation.
pause
exit /b 1

:start_servers
echo.
echo Installing frontend dependencies...
cd frontend
"%NPM_CMD%" install
if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo ✅ Starting development servers...
echo 📡 Backend will be available at: http://localhost:8000
echo 🌐 Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the servers
echo.

cd ..
python start_dev_servers.py

pause
