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
  [string]$RabbitmqUrl = ""
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$env:PYTHONPATH = "$RootDir/backend"
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
$PythonCmd = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

$argsList = @("-m", "app.scripts.smoke_services", "--env-file", $EnvFile)
if ($BaseUrl) {
  $argsList += @("--base-url", $BaseUrl)
}
if ($DatabaseUrl) {
  $argsList += @("--database-url", $DatabaseUrl)
}
if ($S3Endpoint) {
  $argsList += @("--s3-endpoint", $S3Endpoint)
}
if ($RabbitmqUrl) {
  $argsList += @("--rabbitmq-url", $RabbitmqUrl)
}

& $PythonCmd @argsList
exit $LASTEXITCODE
