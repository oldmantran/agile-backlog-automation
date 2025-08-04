@echo off
REM Regression test runner - Run this before any major changes
echo.
echo ============================================================
echo REGRESSION TEST SUITE - Preventing Core Functionality Breaks
echo ============================================================
echo.

REM Change to project directory
cd /d "%~dp0\.."

echo Step 1: Running Pre-commit Checks...
echo ------------------------------------------------------------
python tools\pre_commit_check.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ PRE-COMMIT CHECKS FAILED - CRITICAL ISSUES DETECTED
    echo.
    pause
    exit /b 1
)

echo.
echo Step 2: Running Core Smoke Tests...
echo ------------------------------------------------------------
python tests\test_core_smoke.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ SMOKE TESTS FAILED - BASIC FUNCTIONALITY BROKEN
    echo.
    pause
    exit /b 1
)

echo.
echo Step 3: Running Vision Integration Tests...
echo ------------------------------------------------------------
python tests\test_vision_integration.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ INTEGRATION TESTS FAILED - VISION PROCESSING BROKEN
    echo.
    pause
    exit /b 1
)

echo.
echo Step 4: Quick API Server Validation...
echo ------------------------------------------------------------
python -c "
try:
    from unified_api_server import app
    from supervisor.supervisor import WorkflowSupervisor
    from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
    print('✅ All core imports successful')
except Exception as e:
    print(f'❌ Import failure: {e}')
    exit(1)
"
if %ERRORLEVEL% neq 0 (
    echo ❌ CRITICAL IMPORT FAILURES DETECTED
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ ALL REGRESSION TESTS PASSED
echo ============================================================
echo The application core functionality is verified and safe.
echo You can proceed with confidence that basic features work.
echo.
pause