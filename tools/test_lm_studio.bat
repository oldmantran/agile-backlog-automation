@echo off
echo ========================================
echo    LM Studio 70B Model Testing
echo ========================================
echo.

echo Testing Epic Generation...
python tools/test_lm_studio_epic.py

echo.
echo ========================================
echo.

echo Testing Feature Decomposition...
python tools/test_lm_studio_feature.py

echo.
echo ========================================
echo Testing completed!
pause 