@echo off
echo 🚀 Starting Agile Backlog Automation with SSE Testing
echo ====================================================

echo.
echo 📦 Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo 🔧 Starting API server...
start "API Server" cmd /k "python api_server.py"

echo.
echo ⏳ Waiting for server to start...
timeout /t 5 /nobreak > nul

echo.
echo 🧪 Testing SSE implementation...
python test_sse_implementation.py

echo.
echo 🌐 Opening frontend test page...
start test_sse_frontend.html

echo.
echo ✅ Setup complete! 
echo.
echo 📋 Next steps:
echo    1. Check the API server window for any errors
echo    2. Test SSE functionality in the browser
echo    3. Start your React frontend: cd frontend && npm start
echo.
echo 🔧 If you encounter issues, check the troubleshooting guide:
echo    SSE_TROUBLESHOOTING_GUIDE.md
echo.
pause 