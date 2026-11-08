@echo off
setlocal
echo Cleaning temporary cache files to reduce project size...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\clean_disk_space.ps1"
echo.
pause

