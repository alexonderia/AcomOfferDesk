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

if ($BaseUrl) {
  $env:E2E_BASE_URL = $BaseUrl
}
if ($StrictCredentials) {
  $env:E2E_STRICT_CREDENTIALS = "true"
}

$provisionStateFile = ""
if ($ProvisionUsers) {
  $provisionJson = python -m app.scripts.e2e_provision_users provision --env-file $EnvFile --state-dir ".tmp/e2e"
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
    python -m app.scripts.e2e_provision_users cleanup --env-file $EnvFile --state-file $provisionStateFile
    if ($LASTEXITCODE -ne 0 -and $testExitCode -eq 0) {
      $testExitCode = $LASTEXITCODE
    }
  } elseif ($ProvisionUsers -and $KeepProvisionedUsers -and $provisionStateFile) {
    Write-Host "Provisioned E2E users were kept. State file: $provisionStateFile"
  }
}

exit $testExitCode
