$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot "backend/.env"
$databaseUrl = "sqlite:///./.tmp/ecommerce-agent-dev.db"

if (-not (Test-Path $envPath)) {
  throw "Missing backend/.env. Prepare the backend environment file first."
}

$lines = Get-Content -Path $envPath -Encoding UTF8
$updated = $false

for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^DATABASE_URL=') {
    $lines[$i] = "DATABASE_URL=$databaseUrl"
    $updated = $true
    break
  }
}

if (-not $updated) {
  $lines += "DATABASE_URL=$databaseUrl"
}

Set-Content -Path $envPath -Value $lines -Encoding UTF8
Write-Output "Switched backend/.env to SQLite: $databaseUrl"
