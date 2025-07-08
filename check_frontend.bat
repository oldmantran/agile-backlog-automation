@echo off
echo ========================================
echo  Frontend Diagnostic Check
echo ========================================
echo.

cd frontend

echo Checking if frontend server is running...
netstat -an | findstr ":3000"
if %errorlevel% equ 0 (
    echo [OK] Something is listening on port 3000
) else (
    echo [ERROR] Nothing is listening on port 3000
)

echo.
echo Checking for common build issues...
if exist build (
    echo [INFO] Build directory exists
) else (
    echo [INFO] No build directory (normal for dev mode)
)

if exist node_modules (
    echo [OK] node_modules directory exists
) else (
    echo [ERROR] node_modules directory missing
)

if exist src\App.tsx (
    echo [OK] App.tsx exists
) else (
    echo [ERROR] App.tsx missing
)

if exist public\index.html (
    echo [OK] index.html exists
) else (
    echo [ERROR] index.html missing
)

echo.
echo Try these troubleshooting steps:
echo 1. Check the Frontend Dev Server window for errors
echo 2. Press Ctrl+F5 in your browser to hard refresh
echo 3. Try opening http://localhost:3000 in an incognito window
echo 4. Check browser console (F12) for JavaScript errors
echo.
pause
