# Runs all Milestone quality gates: backend tests, frontend tests, lint, build.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\run-all-checks.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "unitrack-backend"
$frontend = Join-Path $root "unitrack-frontend"
$py = Join-Path $backend "venv\Scripts\python.exe"

Write-Host "==> Backend tests (unitrack-backend)" -ForegroundColor Cyan
if (Test-Path $py) {
    Push-Location $backend
    try { & $py manage.py test; if ($LASTEXITCODE -ne 0) { throw "Backend tests failed" } }
    finally { Pop-Location }
} else {
    throw "venv python not found at $py. Create it with: python -m venv venv"
}

Write-Host "==> Frontend tests (unitrack-frontend)" -ForegroundColor Cyan
Push-Location $frontend
try { & npm test; if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed" } }
finally { Pop-Location }

Write-Host "==> Frontend lint" -ForegroundColor Cyan
Push-Location $frontend
try { & npm run lint; if ($LASTEXITCODE -ne 0) { throw "Lint failed" } }
finally { Pop-Location }

Write-Host "==> Frontend build" -ForegroundColor Cyan
Push-Location $frontend
try { & npm run build; if ($LASTEXITCODE -ne 0) { throw "Build failed" } }
finally { Pop-Location }

Write-Host "All quality gates passed." -ForegroundColor Green