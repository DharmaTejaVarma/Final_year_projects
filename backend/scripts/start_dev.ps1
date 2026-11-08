# PowerShell script to start TravelSenseAI Backend
param(
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8000
)

Write-Host ">>> Starting TravelSenseAI FastAPI Backend on http://$($HostAddress):$($Port)" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\.."

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host ">>> Activating virtual environment..." -ForegroundColor Yellow
    & ".\.venv\Scripts\Activate.ps1"
}

uvicorn app.main:app --host $HostAddress --port $Port --reload

