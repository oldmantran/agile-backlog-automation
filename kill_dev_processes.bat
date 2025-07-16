@echo off
setlocal enabledelayedexpansion
REM Kill Development Processes Script
REM Kills all processes running on ports 8000 and 3000

echo.
echo [INFO] Scanning for processes on ports 8000 and 3000...
echo.

REM Kill processes on port 8000
echo Checking port 8000...
set "found_8000=false"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo   [KILL] Killing process with PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [SUCCESS] Process killed successfully
        set "found_8000=true"
    ) else (
        echo   [ERROR] Failed to kill process %%a
    )
)
if "!found_8000!"=="false" (
    echo   [INFO] No processes found on port 8000
)

REM Kill processes on port 3000
echo Checking port 3000...
set "found_3000=false"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    echo   [KILL] Killing process with PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [SUCCESS] Process killed successfully
        set "found_3000=true"
    ) else (
        echo   [ERROR] Failed to kill process %%a
    )
)
if "!found_3000!"=="false" (
    echo   [INFO] No processes found on port 3000
)

REM Additional cleanup
echo.
echo [INFO] Additional cleanup - killing common development processes...

REM Kill Python processes (be careful not to kill system Python)
tasklist | findstr /i "python.exe" >nul
if !errorlevel! equ 0 (
    echo   [KILL] Killing Python processes...
    taskkill /f /im python.exe >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [SUCCESS] Python processes killed
    ) else (
        echo   [WARNING] Some Python processes may still be running
    )
) else (
    echo   [INFO] No Python processes found
)

REM Kill Node processes (be careful not to kill system Node)
tasklist | findstr /i "node.exe" >nul
if !errorlevel! equ 0 (
    echo   [KILL] Killing Node processes...
    taskkill /f /im node.exe >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [SUCCESS] Node processes killed
    ) else (
        echo   [WARNING] Some Node processes may still be running
    )
) else (
    echo   [INFO] No Node processes found
)

echo.
echo [SUCCESS] Port cleanup complete!
echo Ports 8000 and 3000 should now be free for fresh testing.
echo.
pause
