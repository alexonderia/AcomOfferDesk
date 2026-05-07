param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [Parameter(Mandatory=$false)]
  [string]$BaseUrl = "",
  [switch]$IncludeE2E,
  [switch]$StrictE2E,
  [switch]$ProvisionE2EUsers,
  [switch]$KeepProvisionedE2EUsers
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

Write-Host "== [1/6] backend unit tests =="
& "$RootDir/scripts/test-unit.ps1"

Write-Host "== [2/6] backend integration/API contract tests =="
& "$RootDir/scripts/test-integration.ps1"

Write-Host "== [3/6] infrastructure smoke checks =="
if ($BaseUrl) {
  & "$RootDir/scripts/smoke-infra.ps1" -EnvFile $EnvFile -BaseUrl $BaseUrl
} else {
  & "$RootDir/scripts/smoke-infra.ps1" -EnvFile $EnvFile
}

Write-Host "== [4/6] keycloak permission model checks =="
& "$RootDir/scripts/check-keycloak.ps1" -EnvFile $EnvFile

Write-Host "== [5/6] frontend typecheck/build =="
npm --prefix web run build

if ($IncludeE2E) {
  Write-Host "== [6/6] e2e smoke =="
  $e2eArgs = @("-EnvFile", $EnvFile)
  if ($BaseUrl) {
    $e2eArgs += @("-BaseUrl", $BaseUrl)
  }
  if ($StrictE2E) {
    $e2eArgs += "-StrictCredentials"
  }
  if ($ProvisionE2EUsers) {
    $e2eArgs += "-ProvisionUsers"
  }
  if ($KeepProvisionedE2EUsers) {
    $e2eArgs += "-KeepProvisionedUsers"
  }
  & "$RootDir/scripts/e2e-smoke.ps1" @e2eArgs
} else {
  Write-Host "== [6/6] e2e smoke skipped (use -IncludeE2E to enable) =="
}

Write-Host "Release checks completed"
