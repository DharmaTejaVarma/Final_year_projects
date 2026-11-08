# ============================================================
# TravelSenseAI — Start Both Servers (PowerShell)
# Usage: Right-click > Run with PowerShell  OR  .\start.ps1
# ============================================================

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TravelSenseAI — Starting Development Servers" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend  -> http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend -> http://localhost:5173" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Press Ctrl+C in each window to stop." -ForegroundColor Yellow
Write-Host ""

# Start Backend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$RootDir\backend';
    Write-Host '--- TravelSenseAI Backend (FastAPI) ---' -ForegroundColor Cyan;
    Write-Host 'API Docs: http://localhost:8000/docs' -ForegroundColor Green;
    Write-Host '';
    .\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"

# Small delay so backend starts first
Start-Sleep -Seconds 2

# Start Frontend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$RootDir\frontend';
    Write-Host '--- TravelSenseAI Frontend (React + Vite) ---' -ForegroundColor Magenta;
    Write-Host 'App: http://localhost:5173' -ForegroundColor Green;
    Write-Host '';
    npm run dev
"

Write-Host "Both servers are launching in separate windows." -ForegroundColor Green
Write-Host "Open http://localhost:5173 in your browser." -ForegroundColor Cyan
Write-Host ""

