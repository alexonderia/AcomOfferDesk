param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [Parameter(Mandatory=$false)]
  [string]$BaseUrl = "",
  [switch]$StrictCredentials,
  [switch]$Headed
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
  param([hashtable]$Map, [string]$Key)
  if ($Map.ContainsKey($Key)) { return [string]$Map[$Key] }
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

$cmd = @("--prefix", "web", "exec", "--", "playwright", "test", "--config", "web/playwright.config.ts", "--grep", "@smoke")
if ($Headed) {
  $cmd += "--headed"
}

npm @cmd
exit $LASTEXITCODE
