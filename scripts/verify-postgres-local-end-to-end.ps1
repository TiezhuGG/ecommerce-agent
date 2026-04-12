param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $PSScriptRoot "start-postgres-local.ps1"
$switchScript = Join-Path $PSScriptRoot "set-backend-database-postgres-local.ps1"
$smokeScript = Join-Path $PSScriptRoot "run-backend-database-smoke.ps1"

foreach ($path in @($startScript, $switchScript, $smokeScript)) {
  if (-not (Test-Path $path)) {
    throw "Missing required script: $path"
  }
}

if ($DryRun) {
  & $startScript -DryRun
  Write-Output "[DryRun] & `"$switchScript`""
  Write-Output "[DryRun] Restart backend after DATABASE_URL change."
  Write-Output "[DryRun] & `"$smokeScript`" -ExpectBackend postgresql"
  exit 0
}

& $startScript
& $switchScript
Write-Output "backend/.env switched to local PostgreSQL."
Write-Output "Restart backend before running the smoke check."
& $smokeScript -ExpectBackend postgresql
