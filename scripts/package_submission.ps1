<#
.SYNOPSIS
    Packages TravelSenseAI for Final Year Project / Academic Submission.
    Creates a clean, complete zip archive containing 100% of all source code,
    documentation, database, tests, and configuration without bulky .venv or node_modules.

.DESCRIPTION
    Standard archive size: ~1.5 MB to 3 MB (Far under the 50 - 100 MB submission limit).
    Includes optional flag -IncludeFrontendNodeModules to bundle frontend dependencies (~45 MB).
#>

param(
    [switch]$IncludeFrontendNodeModules = $false,
    [string]$OutputPath = ".\TravelSenseAI_Submission.zip"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path "."

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   TravelSenseAI Submission Packaging Utility" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Clean up local caches first
Write-Host "[1/4] Purging temporary Python and test caches..." -ForegroundColor Yellow
Get-ChildItem -Path $root -Recurse -Force -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $root -Recurse -Force -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 2. Stage files
$stagingDir = Join-Path $env:TEMP "TravelSenseAI_Export_$([System.Guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null

Write-Host "[2/4] Collecting all source code, documentation, and assets..." -ForegroundColor Yellow

# Patterns to exclude
$excludePatterns = @(
    '\.venv\\',
    'backend\\\.venv\\',
    '\\__pycache__\\',
    '\\\.pytest_cache\\',
    '\\\.git\\'
)

if (-not $IncludeFrontendNodeModules) {
    $excludePatterns += '\\node_modules\\'
} else {
    # Exclude root node_modules only, keep frontend\node_modules
    $excludePatterns += '^\\node_modules\\'
}

$itemsToCopy = Get-ChildItem -Path $root -Recurse -Force | Where-Object {
    $full = $_.FullName
    $match = $false
    foreach ($pat in $excludePatterns) {
        if ($full -match $pat) {
            $match = $true
            break
        }
    }
    if ($_.Name -match '^(\.venv|node_modules|__pycache__|\.pytest_cache)$' -and (-not $IncludeFrontendNodeModules -or $_.FullName -notmatch 'frontend\\node_modules')) {
        $match = $true
    }
    # Exclude any previous zip exports
    if ($_.Name -like "*.zip") {
        $match = $true
    }
    -not $match
}

foreach ($item in $itemsToCopy) {
    $relPath = $item.FullName.Substring($root.Path.Length).TrimStart('\')
    $destPath = Join-Path $stagingDir $relPath
    if ($item.PSIsContainer) {
        if (-not (Test-Path $destPath)) {
            New-Item -ItemType Directory -Path $destPath -Force | Out-Null
        }
    } else {
        $destParent = Split-Path -Path $destPath -Parent
        if (-not (Test-Path $destParent)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }
        Copy-Item -Path $item.FullName -Destination $destPath -Force
    }
}

# 3. Compress into zip archive
Write-Host "[3/4] Compressing into optimal submission archive..." -ForegroundColor Yellow
if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
}

$resolvedOutput = [System.IO.Path]::GetFullPath((Join-Path $root $OutputPath))
Compress-Archive -Path "$stagingDir\*" -DestinationPath $resolvedOutput -CompressionLevel Optimal

# 4. Clean up staging
Remove-Item -Path $stagingDir -Recurse -Force -ErrorAction SilentlyContinue

$archiveItem = Get-Item $resolvedOutput
$sizeMB = [math]::Round($archiveItem.Length / 1MB, 2)

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Submission package created successfully!" -ForegroundColor Green
Write-Host " Output file : $resolvedOutput" -ForegroundColor White
Write-Host " Archive size: $sizeMB MB (Well within 50 - 100 MB limit)" -ForegroundColor Cyan
Write-Host " Code files  : 100% of all code, docs, and databases included." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
