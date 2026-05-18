param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [switch]$StrictUnknownAtomic
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$env:PYTHONPATH = "$RootDir/backend"
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
$PythonCmd = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

$argsList = @("-m", "app.scripts.check_keycloak_permission_model", "--env-file", $EnvFile)
if ($StrictUnknownAtomic) {
  $argsList += "--strict-unknown-atomic"
}

& $PythonCmd @argsList
exit $LASTEXITCODE
