param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$composePath = Join-Path $repoRoot "docker-compose.postgres-local.yml"

if (-not (Test-Path $composePath)) {
  throw "Missing docker-compose.postgres-local.yml."
}

$command = "docker compose -f `"$composePath`" down"

if ($DryRun) {
  Write-Output "[DryRun] $command"
  exit 0
}

docker compose -f $composePath down
