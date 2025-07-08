@echo off
echo Starting Backend API Server Only
echo =================================

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    echo Please check your Python installation and try again
    pause
    exit /b 1
)

echo.
echo ✅ Starting FastAPI backend server...
echo 📡 API will be available at: http://localhost:8000
echo 📚 API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python api_server.py

pause
