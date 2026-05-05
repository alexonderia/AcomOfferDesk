$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$EnvFile = if ($env:ENV_FILE) { $env:ENV_FILE } else { ".env.prod-like.example" }
$ComposeFiles = if ($env:COMPOSE_FILES) { $env:COMPOSE_FILES -split "\s+" } else { @("docker-compose.yml", "docker-compose.prod.yml") }

$composeArgs = @()
foreach ($f in $ComposeFiles) {
  if ($f) {
    $composeArgs += @("-f", $f)
  }
}

$tmpCfg = New-TemporaryFile
try {
  Write-Host "Rendering compose config..."
  $env:APP_RUNTIME_ENV_FILE = ".env.prod-like.example"
  docker compose --env-file $EnvFile @composeArgs config | Out-File -FilePath $tmpCfg -Encoding utf8

  $fail = $false
  $warn = $false
  $content = Get-Content $tmpCfg -Raw

  foreach ($forbidden in @("8000:", "5672:", "15672:", "9000:", "9001:", "5432:", "5050:")) {
    if ($content -match [regex]::Escape($forbidden)) {
      Write-Host "FAIL: forbidden published host port found in rendered config: $forbidden"
      $fail = $true
    }
  }

  if ($content -match "start-dev") {
    Write-Host "WARN: start-dev detected in rendered config."
    $warn = $true
  }

  foreach ($sample in @(".env.prod-like.example", ".env.example", ".env.dev.example")) {
    if (Test-Path $sample) {
      $sampleContent = Get-Content $sample -Raw
      if ($sampleContent -match "guest:guest|RABBITMQ_DEFAULT_USER=guest|RABBITMQ_DEFAULT_PASS=guest|minioadmin|dev-secret|start-dev") {
        Write-Host "WARN: insecure/dev defaults detected in $sample"
        $warn = $true
      }
      if ($sampleContent -match "(?m)^CHANGE_ME") {
        Write-Host "WARN: CHANGE_ME placeholders exist in $sample (expected for example files, replace in real env files)."
        $warn = $true
      }
    }
  }

  if ($fail) {
    Write-Host "Perimeter check: FAILED"
    exit 1
  }

  if ($warn) {
    Write-Host "Perimeter check: PASSED with warnings"
    exit 0
  }

  Write-Host "Perimeter check: PASSED"
}
finally {
  Remove-Item $tmpCfg -ErrorAction SilentlyContinue
}
