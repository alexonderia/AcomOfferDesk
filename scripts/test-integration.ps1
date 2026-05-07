$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$env:PYTHONPATH = "$RootDir/backend"

python -m pytest backend/tests/integration -q