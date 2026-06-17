param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [switch]$StrictUnknownAtomic,
  [switch]$Repair
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

function Import-EnvFileToProcess {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    throw "Env file not found: $Path"
  }

  $importedKeys = New-Object System.Collections.Generic.List[string]
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

    $existingValue = [Environment]::GetEnvironmentVariable($key, "Process")
    if (-not [string]::IsNullOrEmpty($existingValue)) {
      continue
    }

    [Environment]::SetEnvironmentVariable($key, $value, "Process")
    $importedKeys.Add($key)
  }

  return $importedKeys
}

$env:PYTHONPATH = "$RootDir/backend"
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
$PythonCmd = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

$resolvedEnvFile = if ([System.IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $RootDir $EnvFile }
$importedEnvKeys = Import-EnvFileToProcess -Path $resolvedEnvFile

$argsList = @("-m", "app.scripts.check_keycloak_permission_model", "--env-file", $EnvFile)
if ($StrictUnknownAtomic) {
  $argsList += "--strict-unknown-atomic"
}
if ($Repair) {
  $argsList += "--repair"
}

try {
  & $PythonCmd @argsList
  exit $LASTEXITCODE
} finally {
  foreach ($key in $importedEnvKeys) {
    Remove-Item "Env:$key" -ErrorAction SilentlyContinue
  }
}
