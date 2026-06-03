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

function Resolve-EnvValue {
  param(
    [hashtable]$Map,
    [string[]]$Keys,
    [string]$Default = ""
  )
  foreach ($k in $Keys) {
    if ($Map.ContainsKey($k) -and $Map[$k]) { return $Map[$k] }
  }
  return $Default
}

function Invoke-Kcadm {
  param([string[]]$KcadmArgs)
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $output = (& docker exec $script:KeycloakContainer /opt/keycloak/bin/kcadm.sh @KcadmArgs 2>$null | Out-String).Trim()
  }
  finally {
    $ErrorActionPreference = $previousPreference
  }
  if ($LASTEXITCODE -ne 0) {
    throw "kcadm failed: $($KcadmArgs -join ' ')`n$output"
  }
  return $output
}

function Get-ClientUuid {
  param([string]$ClientId)
  $json = Invoke-Kcadm -KcadmArgs @("get", "clients?clientId=$ClientId", "-r", $script:AppRealm)
  $parsed = $json | ConvertFrom-Json
  if ($parsed -and $parsed.Count -gt 0) { return $parsed[0].id }
  return $null
}

function Assert-RoleInMappings {
  param(
    [object[]]$Mappings,
    [string]$RoleName,
    [string]$ErrorPrefix
  )
  if ($Mappings | Where-Object { $_.name -eq $RoleName }) {
    Write-Host "OK: $ErrorPrefix '$RoleName'"
    return $true
  }
  Write-Host "FAIL: $ErrorPrefix '$RoleName'"
  return $false
}

function Test-WeakSecret {
  param([string]$Value)
  $resolved = if ($null -eq $Value) { "" } else { $Value }
  $normalized = (($resolved).Trim().ToLowerInvariant() -replace "\s", "")
  if (-not $normalized) { return $true }
  if ($normalized -in @("change-me", "changeme", "change_me", "top-secret", "top_secret", "secret", "password", "admin", "test", "example")) { return $true }
  if ($normalized.StartsWith("change_me") -or $normalized.StartsWith("change-me") -or $normalized.EndsWith("example")) { return $true }
  return $false
}

$EnvFile = if ($env:ENV_FILE) { $env:ENV_FILE } else { ".env.prod-like" }
$script:KeycloakContainer = if ($env:KEYCLOAK_CONTAINER) { $env:KEYCLOAK_CONTAINER } else { "keycloak" }
$InternalServerUrl = if ($env:KEYCLOAK_INTERNAL_SERVER_URL) { $env:KEYCLOAK_INTERNAL_SERVER_URL } else { "http://localhost:8080/iam" }
$MasterRealm = if ($env:KEYCLOAK_MASTER_REALM) { $env:KEYCLOAK_MASTER_REALM } else { "master" }

$running = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $script:KeycloakContainer }
if (-not $running) {
  throw "Container '$script:KeycloakContainer' is not running"
}

$envMap = Get-EnvMap -Path $EnvFile
$script:AppRealm = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_REALM") -Default "acom-offerdesk"
$WebClientId = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_WEB_CLIENT_ID", "KEYCLOAK_CLIENT_ID") -Default "acom-web"
$ApiClientId = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_API_CLIENT_ID") -Default "acom-api"
$AdminServiceClientId = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_ADMIN_CLIENT_ID") -Default "acom-admin-service"
$AdminServiceClientSecret = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_ADMIN_CLIENT_SECRET")
$BootstrapUsername = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_BOOTSTRAP_APP_USERNAME") -Default "superadmin"
$AdminUsername = Resolve-EnvValue -Map $envMap -Keys @("KC_BOOTSTRAP_ADMIN_USERNAME", "KEYCLOAK_ADMIN_USERNAME")
$AdminPassword = Resolve-EnvValue -Map $envMap -Keys @("KC_BOOTSTRAP_ADMIN_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD")
$AppEnv = (Resolve-EnvValue -Map $envMap -Keys @("APP_ENV", "ENVIRONMENT") -Default "development").Trim().ToLowerInvariant()
$KeycloakPublicBaseUrl = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_PUBLIC_BASE_URL")
$KeycloakIssuerUrl = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_ISSUER_URL")
$KcHostname = Resolve-EnvValue -Map $envMap -Keys @("KC_HOSTNAME")
$KeycloakVerifyEmail = Resolve-EnvValue -Map $envMap -Keys @("KEYCLOAK_VERIFY_EMAIL")

if (-not $AdminUsername -or -not $AdminPassword) {
  throw "Missing admin credentials in $EnvFile (need KC_BOOTSTRAP_ADMIN_USERNAME/KC_BOOTSTRAP_ADMIN_PASSWORD or KEYCLOAK_ADMIN_USERNAME/KEYCLOAK_ADMIN_PASSWORD)"
}

$RoleNames = @(
  "users.read","users.create","users.status.update","users.role.update_any","users.role.update_economy","users.login.update","users.password.update","users.manager.update",
  "profile.manage_own","profile.manage_any","company_contacts.manage_own","company_contacts.manage_any",
  "requests.read","requests.amounts.read","requests.create","requests.update","requests.pricing.update","requests.deadline.update","requests.status.update","requests.owner.change",
  "requests.files.upload","requests.files.delete","requests.open.read","requests.offered.read","requests.contractor_view.read","requests.email_notifications.send","requests.deleted_alerts.mark_viewed",
  "offers.create","offers.manual.create","offers.workspace.read","offers.update","offers.amount.update","offers.details.update","offers.status.update","offers.files.upload","offers.files.delete","offers.contractor_info.read",
  "chat.read","chat.message.send","chat.message.attach","chat.receipts.mark_received","chat.receipts.mark_read",
  "feedback.read","feedback.create","dashboard.process.read","dashboard.savings.read","dashboard.plans.read",
  "normative_files.read","normative_files.create","normative_files.manage","normative_files.status.update","files.download",
  "unavailability.manage_all","unavailability.manage_own","unavailability.manage_subordinate","contractors.manual.create","contractors.manual.manage",
  "app.superadmin","app.admin","app.project_manager","app.lead_economist","app.economist","app.operator","app.contractor"
)

$fail = $false

if (Test-WeakSecret -Value $AdminServiceClientSecret) {
  Write-Host "FAIL: KEYCLOAK_ADMIN_CLIENT_SECRET is missing or looks like a placeholder"
  $fail = $true
}

if ($AppEnv -eq "production") {
  foreach ($requiredHttps in @($KeycloakPublicBaseUrl, $KeycloakIssuerUrl, $KcHostname)) {
    if (-not $requiredHttps -or -not $requiredHttps.StartsWith("https://")) {
      Write-Host "FAIL: production requires https values for KEYCLOAK_PUBLIC_BASE_URL, KEYCLOAK_ISSUER_URL and KC_HOSTNAME"
      $fail = $true
      break
    }
  }
  if ($KeycloakVerifyEmail -ne "true") {
    Write-Host "FAIL: production requires KEYCLOAK_VERIFY_EMAIL=true"
    $fail = $true
  }
}

Write-Host "Authenticating kcadm..."
Invoke-Kcadm -KcadmArgs @("config", "credentials", "--server", $InternalServerUrl, "--realm", $MasterRealm, "--user", $AdminUsername, "--password", $AdminPassword) | Out-Null

Write-Host "Checking realm security settings..."
$realmJson = Invoke-Kcadm -KcadmArgs @("get", "realms/$script:AppRealm")
$realm = $realmJson | ConvertFrom-Json
if ($realm.sslRequired -ne "external") {
  Write-Host "FAIL: realm sslRequired must be 'external'"
  $fail = $true
} else {
  Write-Host "OK: realm sslRequired is external"
}
if (-not $realm.bruteForceProtected) {
  Write-Host "FAIL: realm bruteForceProtected must be true"
  $fail = $true
} else {
  Write-Host "OK: realm bruteForceProtected is true"
}
if ($AppEnv -eq "production") {
  if (-not $realm.verifyEmail) {
    Write-Host "FAIL: production realm verifyEmail must be true"
    $fail = $true
  } else {
    Write-Host "OK: production realm verifyEmail is true"
  }
}

Write-Host "Checking clients..."
$webClientUuid = Get-ClientUuid -ClientId $WebClientId
$apiClientUuid = Get-ClientUuid -ClientId $ApiClientId
$adminServiceClientUuid = Get-ClientUuid -ClientId $AdminServiceClientId

if (-not $webClientUuid) { Write-Host "FAIL: missing client '$WebClientId'"; $fail = $true } else { Write-Host "OK: client '$WebClientId'" }
if (-not $apiClientUuid) { Write-Host "FAIL: missing client '$ApiClientId'"; $fail = $true } else { Write-Host "OK: client '$ApiClientId'" }
if (-not $adminServiceClientUuid) { Write-Host "FAIL: missing client '$AdminServiceClientId'"; $fail = $true } else { Write-Host "OK: client '$AdminServiceClientId'" }

if ($apiClientUuid) {
  Write-Host "Checking roles in '$ApiClientId'..."
  foreach ($roleName in $RoleNames) {
    try {
      Invoke-Kcadm -KcadmArgs @("get", "clients/$apiClientUuid/roles/$roleName", "-r", $script:AppRealm) | Out-Null
      Write-Host "OK: role '$roleName'"
    } catch {
      Write-Host "FAIL: missing role '$roleName'"
      $fail = $true
    }
  }

  Write-Host "Checking app.economist composites..."
  $economistCompositesJson = Invoke-Kcadm -KcadmArgs @("get", "clients/$apiClientUuid/roles/app.economist/composites", "-r", $script:AppRealm)
  $economistComposites = $economistCompositesJson | ConvertFrom-Json
  if (-not (Assert-RoleInMappings -Mappings $economistComposites -RoleName "dashboard.plans.read" -ErrorPrefix "app.economist includes")) {
    $fail = $true
  }

  Write-Host "Checking optional delegation roles (non-blocking)..."
  foreach ($optionalRole in @("delegation.user-manager", "delegation.request-deleter")) {
    try {
      Invoke-Kcadm -KcadmArgs @("get", "clients/$apiClientUuid/roles/$optionalRole", "-r", $script:AppRealm) | Out-Null
      Write-Host "WARN: optional role '$optionalRole' exists"
    } catch {
      Write-Host "OK: optional role '$optionalRole' is absent"
    }
  }

  Write-Host "Checking bootstrap user binding..."
  $bootstrapUsersJson = Invoke-Kcadm -KcadmArgs @("get", "users?username=$BootstrapUsername&exact=true", "-r", $script:AppRealm)
  $bootstrapUsers = $bootstrapUsersJson | ConvertFrom-Json
  if (-not $bootstrapUsers -or $bootstrapUsers.Count -eq 0) {
    Write-Host "FAIL: bootstrap user '$BootstrapUsername' not found"
    $fail = $true
  } else {
    $bootstrapUserId = $bootstrapUsers[0].id
    $mappingsJson = Invoke-Kcadm -KcadmArgs @("get", "users/$bootstrapUserId/role-mappings/clients/$apiClientUuid", "-r", $script:AppRealm)
    $mappings = $mappingsJson | ConvertFrom-Json
    if (-not (Assert-RoleInMappings -Mappings $mappings -RoleName "app.superadmin" -ErrorPrefix "bootstrap user has")) {
      $fail = $true
    }
  }
}

Write-Host "Checking admin service account realm-management bindings..."
$realmMgmtUuid = Get-ClientUuid -ClientId "realm-management"
if (-not $realmMgmtUuid) {
  Write-Host "FAIL: missing client 'realm-management'"
  $fail = $true
} else {
  $serviceAccountUsername = "service-account-$AdminServiceClientId"
  $serviceUsersJson = Invoke-Kcadm -KcadmArgs @("get", "users?username=$serviceAccountUsername&exact=true", "-r", $script:AppRealm)
  $serviceUsers = $serviceUsersJson | ConvertFrom-Json
  if (-not $serviceUsers -or $serviceUsers.Count -eq 0) {
    Write-Host "FAIL: missing service account '$serviceAccountUsername'"
    $fail = $true
  } else {
    $serviceUserId = $serviceUsers[0].id
    $serviceMappingsJson = Invoke-Kcadm -KcadmArgs @("get", "users/$serviceUserId/role-mappings/clients/$realmMgmtUuid", "-r", $script:AppRealm)
    $serviceMappings = $serviceMappingsJson | ConvertFrom-Json
    foreach ($requiredRole in @("query-users", "view-users", "manage-users")) {
      if (-not (Assert-RoleInMappings -Mappings $serviceMappings -RoleName $requiredRole -ErrorPrefix "service account has")) {
        $fail = $true
      }
    }
  }
}

if ($fail) {
  Write-Host "Keycloak bootstrap check: FAILED"
  exit 1
}

Write-Host "Keycloak bootstrap check: PASSED"
