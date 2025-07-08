@echo off
echo ===========================================
echo  Quick Diagnostic Check
echo ===========================================
echo.

echo Current directory: %CD%
echo.

echo Checking Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found or not working
) else (
    echo [OK] Python is working
)

echo.
echo Checking Node.js...
node --version
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found or not working
) else (
    echo [OK] Node.js is working
)

echo.
echo Checking npm...
npm --version
if %errorlevel% neq 0 (
    echo [ERROR] npm not found or not working
) else (
    echo [OK] npm is working
)

echo.
echo Checking required files...
if exist requirements.txt (
    echo [OK] requirements.txt found
) else (
    echo [ERROR] requirements.txt not found
)

if exist api_server.py (
    echo [OK] api_server.py found
) else (
    echo [ERROR] api_server.py not found
)

if exist frontend\package.json (
    echo [OK] frontend\package.json found
) else (
    echo [ERROR] frontend\package.json not found
)

echo.
echo Press any key to test starting the backend server...
pause

echo.
echo Testing backend server startup...
python api_server.py
