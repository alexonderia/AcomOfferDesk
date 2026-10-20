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
  [switch]$IncludeE2E,
  [switch]$StrictE2E,
  [switch]$RepairIamRbac
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

Write-Host "== [1/8] backend unit tests =="
& "$RootDir/scripts/test-unit.ps1"
Assert-StepSucceeded -StepName "backend unit tests"

Write-Host "== [2/8] backend integration/API contract tests =="
& "$RootDir/scripts/test-integration.ps1"
Assert-StepSucceeded -StepName "backend integration/API contract tests"

Write-Host "== [3/8] infrastructure smoke checks =="
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

Write-Host "== [4/8] IAM RBAC checks =="
$iamCheckParams = @{ EnvFile = $EnvFile }
$useRepairIamRbac = $RepairIamRbac
if (-not $PSBoundParameters.ContainsKey("RepairIamRbac")) {
  $useRepairIamRbac = $true
}
if ($useRepairIamRbac) {
  $iamCheckParams.Repair = $true
}
& "$RootDir/scripts/check-iam.ps1" @iamCheckParams
Assert-StepSucceeded -StepName "IAM RBAC and account reconciliation checks"

Write-Host "== [5/8] frontend lint =="
npm --prefix web run lint
Assert-StepSucceeded -StepName "frontend lint"

Write-Host "== [6/8] frontend unit/component tests =="
npm --prefix web run test:unit
Assert-StepSucceeded -StepName "frontend unit/component tests"

Write-Host "== [7/8] frontend typecheck/build =="
npm --prefix web run build
Assert-StepSucceeded -StepName "frontend typecheck/build"

if ($IncludeE2E) {
  Write-Host "== [8/8] e2e smoke =="
  $e2eParams = @{
    EnvFile = $EnvFile
  }
  if ($BaseUrl) {
    $e2eParams.BaseUrl = $BaseUrl
  }
  if ($StrictE2E) {
    $e2eParams.StrictCredentials = $true
  }
  & "$RootDir/scripts/e2e-smoke.ps1" @e2eParams
  Assert-StepSucceeded -StepName "e2e smoke"
} else {
  Write-Host "== [8/8] e2e smoke skipped (use -IncludeE2E to enable) =="
}

Write-Host "Release checks completed"
