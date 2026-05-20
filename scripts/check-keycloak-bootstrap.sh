#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.prod-like}"
KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
INTERNAL_SERVER_URL="${KEYCLOAK_INTERNAL_SERVER_URL:-http://localhost:8080/iam}"
MASTER_REALM="${KEYCLOAK_MASTER_REALM:-master}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "FAIL: env file not found: $ENV_FILE"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: docker is not installed"
  exit 1
fi

if ! docker ps --format '{{.Names}}' | rg -x "$KEYCLOAK_CONTAINER" >/dev/null 2>&1; then
  echo "FAIL: container '$KEYCLOAK_CONTAINER' is not running"
  exit 1
fi

# Load env contract for expected Keycloak IDs and bootstrap credentials.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

APP_REALM="${KEYCLOAK_REALM:-acom-offerdesk}"
WEB_CLIENT_ID="${KEYCLOAK_WEB_CLIENT_ID:-${KEYCLOAK_CLIENT_ID:-acom-web}}"
API_CLIENT_ID="${KEYCLOAK_API_CLIENT_ID:-acom-api}"
ADMIN_SERVICE_CLIENT_ID="${KEYCLOAK_ADMIN_CLIENT_ID:-acom-admin-service}"
ADMIN_SERVICE_CLIENT_SECRET="${KEYCLOAK_ADMIN_CLIENT_SECRET:-}"
BOOTSTRAP_USERNAME="${KEYCLOAK_BOOTSTRAP_APP_USERNAME:-superadmin}"
KC_ADMIN_USERNAME="${KC_BOOTSTRAP_ADMIN_USERNAME:-${KEYCLOAK_ADMIN_USERNAME:-}}"
KC_ADMIN_PASSWORD="${KC_BOOTSTRAP_ADMIN_PASSWORD:-${KEYCLOAK_ADMIN_PASSWORD:-}}"
APP_ENV_NORMALIZED="$(printf '%s' "${APP_ENV:-development}" | tr '[:upper:]' '[:lower:]')"
KEYCLOAK_PUBLIC_BASE_URL="${KEYCLOAK_PUBLIC_BASE_URL:-}"
KEYCLOAK_ISSUER_URL="${KEYCLOAK_ISSUER_URL:-}"
KC_HOSTNAME="${KC_HOSTNAME:-}"
KEYCLOAK_VERIFY_EMAIL="${KEYCLOAK_VERIFY_EMAIL:-}"

if [[ -z "$KC_ADMIN_USERNAME" || -z "$KC_ADMIN_PASSWORD" ]]; then
  echo "FAIL: missing admin credentials in env ($ENV_FILE). Expected KC_BOOTSTRAP_ADMIN_USERNAME/KC_BOOTSTRAP_ADMIN_PASSWORD or KEYCLOAK_ADMIN_USERNAME/KEYCLOAK_ADMIN_PASSWORD."
  exit 1
fi

ROLE_NAMES=$(cat <<'EOF'
users.read
users.create
users.status.update
users.role.update_any
users.role.update_economy
users.login.update
users.password.update
users.manager.update
profile.manage_own
profile.manage_any
company_contacts.manage_own
company_contacts.manage_any
requests.read
requests.amounts.read
requests.create
requests.update
requests.pricing.update
requests.deadline.update
requests.status.update
requests.owner.change
requests.files.upload
requests.files.delete
requests.open.read
requests.offered.read
requests.contractor_view.read
requests.email_notifications.send
requests.deleted_alerts.mark_viewed
offers.create
offers.manual.create
offers.workspace.read
offers.update
offers.amount.update
offers.details.update
offers.status.update
offers.files.upload
offers.files.delete
offers.contractor_info.read
chat.read
chat.message.send
chat.message.attach
chat.receipts.mark_received
chat.receipts.mark_read
feedback.read
feedback.create
dashboard.process.read
dashboard.savings.read
dashboard.plans.read
normative_files.read
normative_files.create
normative_files.manage
files.download
unavailability.manage_all
unavailability.manage_own
unavailability.manage_subordinate
contractors.manual.create
contractors.manual.manage
app.superadmin
app.admin
app.project_manager
app.lead_economist
app.economist
app.operator
app.contractor
EOF
)

fail=0

is_weak_secret() {
  local normalized
  normalized="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  [[ -z "$normalized" ]] && return 0
  case "$normalized" in
    change-me|changeme|change_me|top-secret|top_secret|secret|password|admin|test|example)
      return 0
      ;;
    change_me*|change-me*|*example)
      return 0
      ;;
  esac
  return 1
}

if is_weak_secret "$ADMIN_SERVICE_CLIENT_SECRET"; then
  echo "FAIL: KEYCLOAK_ADMIN_CLIENT_SECRET is missing or looks like a placeholder"
  fail=1
fi

if [[ "$APP_ENV_NORMALIZED" == "production" ]]; then
  for required_https_value in "$KEYCLOAK_PUBLIC_BASE_URL" "$KEYCLOAK_ISSUER_URL" "$KC_HOSTNAME"; do
    if [[ -z "$required_https_value" || "$required_https_value" != https://* ]]; then
      echo "FAIL: production requires https values for KEYCLOAK_PUBLIC_BASE_URL, KEYCLOAK_ISSUER_URL and KC_HOSTNAME"
      fail=1
      break
    fi
  done
  if [[ "$KEYCLOAK_VERIFY_EMAIL" != "true" ]]; then
    echo "FAIL: production requires KEYCLOAK_VERIFY_EMAIL=true"
    fail=1
  fi
fi

docker_exec() {
  docker exec "$KEYCLOAK_CONTAINER" "$@"
}

extract_first_json_id() {
  tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1 | tr -d '\r'
}

contains_role_name() {
  local role_name="$1"
  rg -o "\"name\"[[:space:]]*:[[:space:]]*\"$role_name\"" >/dev/null 2>&1
}

echo "Authenticating kcadm in container '$KEYCLOAK_CONTAINER'..."
if ! docker_exec /opt/keycloak/bin/kcadm.sh config credentials \
  --server "$INTERNAL_SERVER_URL" \
  --realm "$MASTER_REALM" \
  --user "$KC_ADMIN_USERNAME" \
  --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; then
  echo "FAIL: unable to authenticate to Keycloak admin API"
  exit 1
fi

get_client_uuid() {
  local client_id="$1"
  docker_exec /opt/keycloak/bin/kcadm.sh get "clients?clientId=$client_id" -r "$APP_REALM" | extract_first_json_id
}

echo "Checking realm security settings..."
realm_payload="$(docker_exec /opt/keycloak/bin/kcadm.sh get "realms/$APP_REALM")"
if ! printf '%s' "$realm_payload" | rg -q '"sslRequired"[[:space:]]*:[[:space:]]*"external"'; then
  echo "FAIL: realm sslRequired must be 'external'"
  fail=1
else
  echo "OK: realm sslRequired is external"
fi
if ! printf '%s' "$realm_payload" | rg -q '"bruteForceProtected"[[:space:]]*:[[:space:]]*true'; then
  echo "FAIL: realm bruteForceProtected must be true"
  fail=1
else
  echo "OK: realm bruteForceProtected is true"
fi
if [[ "$APP_ENV_NORMALIZED" == "production" ]]; then
  if ! printf '%s' "$realm_payload" | rg -q '"verifyEmail"[[:space:]]*:[[:space:]]*true'; then
    echo "FAIL: production realm verifyEmail must be true"
    fail=1
  else
    echo "OK: production realm verifyEmail is true"
  fi
fi

echo "Checking required clients..."
WEB_CLIENT_UUID="$(get_client_uuid "$WEB_CLIENT_ID")"
API_CLIENT_UUID="$(get_client_uuid "$API_CLIENT_ID")"
ADMIN_SERVICE_CLIENT_UUID="$(get_client_uuid "$ADMIN_SERVICE_CLIENT_ID")"

if [[ -z "$WEB_CLIENT_UUID" ]]; then
  echo "FAIL: missing client '$WEB_CLIENT_ID'"
  fail=1
else
  echo "OK: client '$WEB_CLIENT_ID' exists"
fi

if [[ -z "$API_CLIENT_UUID" ]]; then
  echo "FAIL: missing client '$API_CLIENT_ID'"
  fail=1
else
  echo "OK: client '$API_CLIENT_ID' exists"
fi

if [[ -z "$ADMIN_SERVICE_CLIENT_UUID" ]]; then
  echo "FAIL: missing client '$ADMIN_SERVICE_CLIENT_ID'"
  fail=1
else
  echo "OK: client '$ADMIN_SERVICE_CLIENT_ID' exists"
fi

if [[ -n "$API_CLIENT_UUID" ]]; then
  echo "Checking roles in '$API_CLIENT_ID'..."
  while IFS= read -r role_name; do
    [[ -z "$role_name" ]] && continue
    if docker_exec /opt/keycloak/bin/kcadm.sh get "clients/$API_CLIENT_UUID/roles/$role_name" -r "$APP_REALM" >/dev/null 2>&1; then
      echo "OK: role '$role_name'"
    else
      echo "FAIL: missing role '$role_name'"
      fail=1
    fi
  done <<<"$ROLE_NAMES"

  echo "Checking app.economist composites..."
  economist_composites="$(docker_exec /opt/keycloak/bin/kcadm.sh get "clients/$API_CLIENT_UUID/roles/app.economist/composites" -r "$APP_REALM")"
  if printf '%s' "$economist_composites" | contains_role_name "dashboard.plans.read"; then
    echo "OK: app.economist includes dashboard.plans.read"
  else
    echo "FAIL: app.economist is missing dashboard.plans.read"
    fail=1
  fi

  echo "Checking optional delegation roles (non-blocking)..."
  for optional_role in delegation.user-manager delegation.request-deleter; do
    if docker_exec /opt/keycloak/bin/kcadm.sh get "clients/$API_CLIENT_UUID/roles/$optional_role" -r "$APP_REALM" >/dev/null 2>&1; then
      echo "WARN: optional role '$optional_role' exists"
    else
      echo "OK: optional role '$optional_role' is absent"
    fi
  done
fi

if [[ -n "$API_CLIENT_UUID" ]]; then
  echo "Checking bootstrap user role binding..."
  if docker_exec /opt/keycloak/bin/kcadm.sh get "users?username=$BOOTSTRAP_USERNAME&exact=true" -r "$APP_REALM" | extract_first_json_id | rg -q '.'; then
    bootstrap_user_id="$(docker_exec /opt/keycloak/bin/kcadm.sh get "users?username=$BOOTSTRAP_USERNAME&exact=true" -r "$APP_REALM" | extract_first_json_id)"
    mapped_roles="$(docker_exec /opt/keycloak/bin/kcadm.sh get "users/$bootstrap_user_id/role-mappings/clients/$API_CLIENT_UUID" -r "$APP_REALM")"
    if printf '%s' "$mapped_roles" | contains_role_name "app.superadmin"; then
      echo "OK: '$BOOTSTRAP_USERNAME' has app.superadmin"
    else
      echo "FAIL: '$BOOTSTRAP_USERNAME' is missing app.superadmin"
      fail=1
    fi
  else
    echo "FAIL: bootstrap user '$BOOTSTRAP_USERNAME' not found"
    fail=1
  fi
fi

echo "Checking admin service account role bindings..."
realm_mgmt_uuid="$(get_client_uuid "realm-management")"
if [[ -z "$realm_mgmt_uuid" ]]; then
  echo "FAIL: realm-management client not found"
  fail=1
else
  service_account_username="service-account-$ADMIN_SERVICE_CLIENT_ID"
  service_account_id="$(docker_exec /opt/keycloak/bin/kcadm.sh get "users?username=$service_account_username&exact=true" -r "$APP_REALM" | extract_first_json_id)"
  if [[ -z "$service_account_id" ]]; then
    echo "FAIL: service account user '$service_account_username' not found"
    fail=1
  else
    service_account_mappings="$(docker_exec /opt/keycloak/bin/kcadm.sh get "users/$service_account_id/role-mappings/clients/$realm_mgmt_uuid" -r "$APP_REALM")"
    for required_role in query-users view-users manage-users; do
      if printf '%s' "$service_account_mappings" | contains_role_name "$required_role"; then
        echo "OK: service account has '$required_role'"
      else
        echo "FAIL: service account missing '$required_role'"
        fail=1
      fi
    done
  fi
fi

if [[ $fail -ne 0 ]]; then
  echo "Keycloak bootstrap check: FAILED"
  exit 1
fi

echo "Keycloak bootstrap check: PASSED"
