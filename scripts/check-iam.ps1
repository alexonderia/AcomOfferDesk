param(
  [Parameter(Mandatory=$false)]
  [string]$EnvFile = ".env.dev",
  [Parameter(Mandatory=$false)]
  [switch]$Repair
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

if ($Repair) {
  & docker compose --env-file $EnvFile exec -T backend python -m app.scripts.seed_iam_rbac
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& docker compose --env-file $EnvFile exec -T backend python -m app.scripts.seed_iam_rbac --report
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& docker compose --env-file $EnvFile exec -T backend python -m app.scripts.reconcile_iam_accounts
exit $LASTEXITCODE
