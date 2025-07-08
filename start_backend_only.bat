@echo off
echo Starting Backend API Server Only
echo =================================

echo.
echo Installing Python dependencies...

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
    echo Please check your Python installation and try again
    pause
    exit /b 1
)

echo.
echo [OK] Starting FastAPI backend server...
echo API will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

%PYTHON_CMD% api_server.py

pause
