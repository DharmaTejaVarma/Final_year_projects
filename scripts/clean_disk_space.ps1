<#
.SYNOPSIS
    Cleans up all temporary cache directories across TravelSenseAI without losing any code.
    Frees up several hundred megabytes instantly.
#>

$root = Resolve-Path "."
Write-Host "Cleaning up temporary cache files across TravelSenseAI..." -ForegroundColor Cyan

# 1. Purge all __pycache__ folders
$pycaches = Get-ChildItem -Path $root -Recurse -Force -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$count = $pycaches.Count
$pycaches | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  Removed $count __pycache__ directories." -ForegroundColor Green

# 2. Purge .pytest_cache
Get-ChildItem -Path $root -Recurse -Force -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  Removed .pytest_cache directories." -ForegroundColor Green

# 3. Clean Vite build cache in node_modules if present
if (Test-Path "$root\frontend\node_modules\.vite") {
    Remove-Item -Path "$root\frontend\node_modules\.vite" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed frontend/.vite cache." -ForegroundColor Green
}

# 4. Clean pip cache
try {
    & "$root\backend\.venv\Scripts\python.exe" -m pip cache purge 2>$null
    Write-Host "  Purged pip wheel cache." -ForegroundColor Green
} catch {}

# 5. Calculate new total size
$totalSize = (Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
$totalMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "`nCleanup Complete! Current local folder size: $totalMB MB" -ForegroundColor Yellow

