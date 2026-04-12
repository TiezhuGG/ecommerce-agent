param(
  [ValidateSet("sqlite", "postgresql")]
  [string]$ExpectBackend = "sqlite"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot "backend/.venv/Scripts/python.exe"
$scriptPath = Join-Path $repoRoot "backend/scripts/verify_database_runtime.py"

if (-not (Test-Path $pythonPath)) {
  throw "Missing backend/.venv/Scripts/python.exe. Prepare the backend virtual environment first."
}

if (-not (Test-Path $scriptPath)) {
  throw "Missing backend/scripts/verify_database_runtime.py."
}

& $pythonPath $scriptPath --expect-backend $ExpectBackend
