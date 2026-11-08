@echo off
setlocal
echo ==========================================================
echo    TravelSenseAI - Fast Submission Packaging Tool
echo ==========================================================
echo.
echo Packaging project code, database, tests, and documentation...
echo (Excluding temporary virtual environments and node_modules)
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\package_submission.ps1"

echo.
pause

