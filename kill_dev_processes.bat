@echo off
REM Kill Development Processes Script
REM Kills all processes running on ports 8000 and 3000

echo.
echo 🔍 Scanning for processes on ports 8000 and 3000...
echo.

REM Kill processes on port 8000
echo Checking port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo   🔥 Killing process with PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Process killed successfully
    ) else (
        echo   ❌ Failed to kill process %%a
    )
)

REM Kill processes on port 3000
echo Checking port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    echo   🔥 Killing process with PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Process killed successfully
    ) else (
        echo   ❌ Failed to kill process %%a
    )
)

REM Additional cleanup
echo.
echo 🧹 Additional cleanup - killing common development processes...

REM Kill Python processes (be careful not to kill system Python)
tasklist | findstr /i "python.exe" >nul
if !errorlevel! equ 0 (
    echo   🔥 Killing Python processes...
    taskkill /f /im python.exe >nul 2>&1
)

REM Kill Node processes (be careful not to kill system Node)
tasklist | findstr /i "node.exe" >nul
if !errorlevel! equ 0 (
    echo   🔥 Killing Node processes...
    taskkill /f /im node.exe >nul 2>&1
)

echo.
echo 🎯 Port cleanup complete!
echo Ports 8000 and 3000 should now be free for fresh testing.
echo.
pause
