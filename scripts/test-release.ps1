param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [Parameter(Mandatory=$false)]
  [string]$BaseUrl = "",
  [Parameter(Mandatory=$false)]
  [string]$DatabaseUrl = "",
  [Parameter(Mandatory=$false)]
  [string]$S3Endpoint = "",
  [Parameter(Mandatory=$false)]
  [string]$RabbitmqUrl = "",
  [Parameter(Mandatory=$false)]
  [string]$KeycloakInternalBaseUrl = "",
  [switch]$IncludeE2E,
  [switch]$StrictE2E,
  [switch]$ProvisionE2EUsers,
  [switch]$KeepProvisionedE2EUsers
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

function Assert-StepSucceeded {
  param([string]$StepName)
  if ($LASTEXITCODE -ne 0) {
    Write-Error "$StepName failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
  }
}

Write-Host "== [1/6] backend unit tests =="
& "$RootDir/scripts/test-unit.ps1"
Assert-StepSucceeded -StepName "backend unit tests"

Write-Host "== [2/6] backend integration/API contract tests =="
& "$RootDir/scripts/test-integration.ps1"
Assert-StepSucceeded -StepName "backend integration/API contract tests"

Write-Host "== [3/6] infrastructure smoke checks =="
$smokeParams = @{
  EnvFile = $EnvFile
}
if ($BaseUrl) {
  $smokeParams.BaseUrl = $BaseUrl
}
if ($DatabaseUrl) {
  $smokeParams.DatabaseUrl = $DatabaseUrl
}
if ($S3Endpoint) {
  $smokeParams.S3Endpoint = $S3Endpoint
}
if ($RabbitmqUrl) {
  $smokeParams.RabbitmqUrl = $RabbitmqUrl
}
& "$RootDir/scripts/smoke-infra.ps1" @smokeParams
Assert-StepSucceeded -StepName "infrastructure smoke checks"

Write-Host "== [4/6] keycloak permission model checks =="
$prevKeycloakInternalBaseUrl = [Environment]::GetEnvironmentVariable("KEYCLOAK_INTERNAL_BASE_URL", "Process")
if ($KeycloakInternalBaseUrl) {
  $env:KEYCLOAK_INTERNAL_BASE_URL = $KeycloakInternalBaseUrl
}
try {
  & "$RootDir/scripts/check-keycloak.ps1" -EnvFile $EnvFile
  Assert-StepSucceeded -StepName "keycloak permission model checks"
} finally {
  if ($KeycloakInternalBaseUrl) {
    if ($null -eq $prevKeycloakInternalBaseUrl) {
      Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL -ErrorAction SilentlyContinue
    } else {
      $env:KEYCLOAK_INTERNAL_BASE_URL = $prevKeycloakInternalBaseUrl
    }
  }
}

Write-Host "== [5/6] frontend typecheck/build =="
npm --prefix web run build
Assert-StepSucceeded -StepName "frontend typecheck/build"

if ($IncludeE2E) {
  Write-Host "== [6/6] e2e smoke =="
  $e2eParams = @{
    EnvFile = $EnvFile
  }
  if ($BaseUrl) {
    $e2eParams.BaseUrl = $BaseUrl
  }
  if ($StrictE2E) {
    $e2eParams.StrictCredentials = $true
  }
  $useProvisionE2EUsers = $ProvisionE2EUsers
  if (-not $PSBoundParameters.ContainsKey("ProvisionE2EUsers")) {
    $useProvisionE2EUsers = $true
  }
  if ($useProvisionE2EUsers) {
    $e2eParams.ProvisionUsers = $true
  }
  if ($KeepProvisionedE2EUsers) {
    $e2eParams.KeepProvisionedUsers = $true
  }
  & "$RootDir/scripts/e2e-smoke.ps1" @e2eParams
  Assert-StepSucceeded -StepName "e2e smoke"
} else {
  Write-Host "== [6/6] e2e smoke skipped (use -IncludeE2E to enable) =="
}

Write-Host "Release checks completed"
