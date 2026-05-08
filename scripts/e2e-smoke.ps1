param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [Parameter(Mandatory=$false)]
  [string]$BaseUrl = "",
  [switch]$StrictCredentials,
  [switch]$Headed,
  [switch]$ProvisionUsers,
  [switch]$KeepProvisionedUsers
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$env:PYTHONPATH = "$RootDir/backend"
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
$PythonCmd = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

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

function Normalize-AsyncDatabaseUrl {
  param([string]$Url)
  if (-not $Url) { return $Url }
  if ($Url.StartsWith("postgresql://")) {
    return "postgresql+asyncpg://" + $Url.Substring("postgresql://".Length)
  }
  return $Url
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

$resolvedEnvFile = if ([System.IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $RootDir $EnvFile }
$envMap = Get-EnvMap -Path $resolvedEnvFile

if ($BaseUrl) {
  $env:E2E_BASE_URL = $BaseUrl
} elseif (-not $env:E2E_BASE_URL) {
  $derivedBaseUrl = (Get-MapValue -Map $envMap -Key "WEB_BASE_URL").Trim()
  if (-not $derivedBaseUrl) {
    $derivedBaseUrl = (Get-MapValue -Map $envMap -Key "PUBLIC_BACKEND_BASE_URL").Trim()
  }
  if ($derivedBaseUrl) {
    $env:E2E_BASE_URL = $derivedBaseUrl
    Write-Host "Using E2E_BASE_URL=$derivedBaseUrl from $EnvFile"
  }
}
if ($StrictCredentials) {
  $env:E2E_STRICT_CREDENTIALS = "true"
}

$provisionStateFile = ""
if ($ProvisionUsers) {
  $env:KEYCLOAK_HTTP_TIMEOUT_SECONDS = "30"

  $internalBase = (Get-MapValue -Map $envMap -Key "KEYCLOAK_INTERNAL_BASE_URL").Trim()
  $publicBase = (Get-MapValue -Map $envMap -Key "KEYCLOAK_PUBLIC_BASE_URL").Trim()
  $realm = (Get-MapValue -Map $envMap -Key "KEYCLOAK_REALM").Trim()
  if (-not $realm) {
    $realm = "acom-offerdesk"
  }
  if ($publicBase -and $internalBase -match "://keycloak(:\d+)?/") {
    $localKeycloakBase = "http://127.0.0.1:8080/iam"
    $localRealmUrl = "$localKeycloakBase/realms/$realm"
    $useLocalKeycloak = $false
    try {
      $localProbe = Invoke-WebRequest -Uri $localRealmUrl -UseBasicParsing -TimeoutSec 5
      if ($localProbe.StatusCode -ge 200 -and $localProbe.StatusCode -lt 500) {
        $useLocalKeycloak = $true
      }
    } catch {
      $useLocalKeycloak = $false
    }

    if ($useLocalKeycloak) {
      $env:KEYCLOAK_INTERNAL_BASE_URL = $localKeycloakBase
      Write-Host "Using local KEYCLOAK_INTERNAL_BASE_URL=$localKeycloakBase for provisioning"
    } else {
      $env:KEYCLOAK_INTERNAL_BASE_URL = $publicBase
      Write-Host "Using host-accessible KEYCLOAK_INTERNAL_BASE_URL=$publicBase for provisioning"
    }
  }

  $databaseOverride = (Get-MapValue -Map $envMap -Key "SMOKE_DATABASE_URL").Trim()
  if (-not $databaseOverride) {
    $databaseRaw = (Get-MapValue -Map $envMap -Key "DATABASE_URL").Trim()
    if ($databaseRaw -match "@order-database-postgres:") {
      $databaseOverride = $databaseRaw -replace "@order-database-postgres:", "@127.0.0.1:"
    }
  }
  if ($databaseOverride) {
    $env:DATABASE_URL = Normalize-AsyncDatabaseUrl -Url $databaseOverride
    Write-Host "Using host-accessible DATABASE_URL for provisioning"
  }

  $provisionJson = & $PythonCmd -m app.scripts.e2e_provision_users provision --env-file $EnvFile --state-dir ".tmp/e2e"
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  $provision = $provisionJson | ConvertFrom-Json
  $provisionStateFile = $provision.state_file
  foreach ($user in $provision.users) {
    Set-Item -Path "env:$($user.prefix)_USERNAME" -Value $user.username
    Set-Item -Path "env:$($user.prefix)_PASSWORD" -Value $user.password
  }
  $env:E2E_STRICT_CREDENTIALS = "true"
}

$cmd = @("--prefix", "web", "exec", "--", "playwright", "test", "--config", "web/playwright.config.ts", "--grep", "@smoke")
if ($Headed) {
  $cmd += "--headed"
}

$testExitCode = 1
try {
  npm @cmd
  $testExitCode = $LASTEXITCODE
} finally {
  if ($ProvisionUsers -and -not $KeepProvisionedUsers -and $provisionStateFile) {
    & $PythonCmd -m app.scripts.e2e_provision_users cleanup --env-file $EnvFile --state-file $provisionStateFile
    if ($LASTEXITCODE -ne 0 -and $testExitCode -eq 0) {
      $testExitCode = $LASTEXITCODE
    }
  } elseif ($ProvisionUsers -and $KeepProvisionedUsers -and $provisionStateFile) {
    Write-Host "Provisioned E2E users were kept. State file: $provisionStateFile"
  }
}

exit $testExitCode
