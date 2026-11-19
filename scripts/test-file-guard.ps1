$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir
$PreviousPythonPath = $env:PYTHONPATH
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
$PythonCmd = if (Test-Path $VenvPython) { $VenvPython } else { "python" }
try {
  $env:PYTHONPATH = $RootDir
  & $PythonCmd -m pytest file_guard/tests -q
  $TestExitCode = $LASTEXITCODE
} finally {
  $env:PYTHONPATH = $PreviousPythonPath
}
exit $TestExitCode
