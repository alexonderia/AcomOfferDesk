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
  [switch]$KeepProvisionedE2EUsers,
  [switch]$RepairKeycloak
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

function Get-EnvMap {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    throw "Env file not found: $Path"
  }

  $map = @{}
  foreach ($line in Get-Content $Path) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
    $idx = $trimmed.IndexOf("=")
    if ($idx -lt 1) { continue }
    $key = $trimmed.Substring(0, $idx).Trim()
    $value = $trimmed.Substring($idx + 1).Trim()
    if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
      $value = $value.Substring(1, $value.Length - 2)
    }
    $map[$key] = $value
  }
  return $map
}

function Get-MapValue {
  param(
    [hashtable]$Map,
    [string]$Key
  )
  if ($Map.ContainsKey($Key)) {
    return [string]$Map[$Key]
  }
  return ""
}

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

Write-Host "== [4/8] keycloak permission model checks =="
$prevKeycloakInternalBaseUrl = [Environment]::GetEnvironmentVariable("KEYCLOAK_INTERNAL_BASE_URL", "Process")
$effectiveKeycloakInternalBaseUrl = $KeycloakInternalBaseUrl
if (-not $effectiveKeycloakInternalBaseUrl) {
  $resolvedEnvFile = if ([System.IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $RootDir $EnvFile }
  $envMap = Get-EnvMap -Path $resolvedEnvFile

  $internalBase = (Get-MapValue -Map $envMap -Key "KEYCLOAK_INTERNAL_BASE_URL").Trim()
  $publicBase = (Get-MapValue -Map $envMap -Key "KEYCLOAK_PUBLIC_BASE_URL").Trim()
  $realm = (Get-MapValue -Map $envMap -Key "KEYCLOAK_REALM").Trim()
  if (-not $realm) {
    $realm = "acom-offerdesk"
  }

  if ($publicBase -and $internalBase -match "://keycloak(:\d+)?/") {
    $localKeycloakBase = "http://127.0.0.1:8080/iam"
    $localRealmUrl = "$localKeycloakBase/realms/$realm"
    try {
      $localProbe = Invoke-WebRequest -Uri $localRealmUrl -UseBasicParsing -TimeoutSec 5
      if ($localProbe.StatusCode -ge 200 -and $localProbe.StatusCode -lt 500) {
        $effectiveKeycloakInternalBaseUrl = $localKeycloakBase
      } else {
        $effectiveKeycloakInternalBaseUrl = $publicBase
      }
    } catch {
      $effectiveKeycloakInternalBaseUrl = $publicBase
    }
  }
}
if ($effectiveKeycloakInternalBaseUrl) {
  $env:KEYCLOAK_INTERNAL_BASE_URL = $effectiveKeycloakInternalBaseUrl
  Write-Host "Using KEYCLOAK_INTERNAL_BASE_URL=$effectiveKeycloakInternalBaseUrl for keycloak permission model checks"
}
try {
  $keycloakCheckParams = @{
    EnvFile = $EnvFile
  }
  if ($RepairKeycloak) {
    $keycloakCheckParams.Repair = $true
  }
  & "$RootDir/scripts/check-keycloak.ps1" @keycloakCheckParams
  Assert-StepSucceeded -StepName "keycloak permission model checks"
} finally {
  if ($effectiveKeycloakInternalBaseUrl) {
    if ($null -eq $prevKeycloakInternalBaseUrl) {
      Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL -ErrorAction SilentlyContinue
    } else {
      $env:KEYCLOAK_INTERNAL_BASE_URL = $prevKeycloakInternalBaseUrl
    }
  }
}

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
  Write-Host "== [8/8] e2e smoke skipped (use -IncludeE2E to enable) =="
}

Write-Host "Release checks completed"
