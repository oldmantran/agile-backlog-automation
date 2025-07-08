@echo off
echo =====================================
echo  Node.js Installation Helper
echo =====================================
echo.

echo This script will help you install Node.js for the frontend.
echo.

:: Check if Node.js is already installed
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo [OK] Node.js is already installed: !NODE_VERSION!
    
    npm --version >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
        echo [OK] npm is available: !NPM_VERSION!
        echo.
        echo You're all set! Run setup_and_start.bat to start the application.
    ) else (
        echo [ERROR] npm not found, but Node.js is installed
        echo There might be an issue with your Node.js installation.
    )
    pause
    exit /b 0
)

echo Node.js is not installed or not in your PATH.
echo.
echo Would you like to:
echo 1. Open the Node.js download page (recommended)
echo 2. Get installation instructions
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo Opening Node.js download page...
    start https://nodejs.org/
    echo.
    echo Installation instructions:
    echo 1. Download the LTS version (recommended)
    echo 2. Run the installer with default settings
    echo 3. Restart your command prompt
    echo 4. Run setup_and_start.bat
    echo.
    pause
) else if "%choice%"=="2" (
    echo.
    echo === Node.js Installation Instructions ===
    echo.
    echo 1. Go to https://nodejs.org/
    echo 2. Click "Download Node.js (LTS)" - the green button
    echo 3. Run the downloaded installer (.msi file)
    echo 4. Follow the installation wizard:
    echo    - Accept the license agreement
    echo    - Choose installation location (default is fine)
    echo    - Select components (default is fine)
    echo    - The installer will add Node.js to PATH automatically
    echo 5. Click "Install" and wait for completion
    echo 6. Restart your command prompt
    echo 7. Test by typing: node --version
    echo 8. Run setup_and_start.bat to start the application
    echo.
    echo Note: The LTS (Long Term Support) version is recommended
    echo for stability and compatibility.
    echo.
    pause
) else (
    echo Exiting...
    exit /b 0
)

echo.
echo After installing Node.js, run setup_and_start.bat to start the application.
pause
