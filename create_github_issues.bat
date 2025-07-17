@echo off
echo GitHub Issues Bulk Creator for Agile Backlog Automation
echo ======================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if requests module is available
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing required Python packages...
    pip install requests
    if errorlevel 1 (
        echo ERROR: Failed to install requests package
        pause
        exit /b 1
    )
)

echo.
echo Before running this script, please ensure you have:
echo 1. A GitHub Personal Access Token with 'repo' permissions
echo 2. Set the GITHUB_TOKEN environment variable
echo.
echo To set the token, run:
echo   set GITHUB_TOKEN=your_token_here
echo.
echo Or set it permanently in your system environment variables.
echo.

set /p continue="Do you want to continue? (y/N): "
if /i not "%continue%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Running GitHub Issues Creator...
python create_github_issues.py

echo.
pause 