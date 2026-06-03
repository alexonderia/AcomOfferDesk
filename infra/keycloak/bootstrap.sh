#!/bin/sh
set -e
set -u

SERVER_URL="${KEYCLOAK_INTERNAL_BASE_URL:-${KEYCLOAK_INTERNAL_URL:-http://keycloak:8080/iam}}"
MASTER_REALM="${KEYCLOAK_MASTER_REALM:-master}"
APP_REALM="${KEYCLOAK_REALM:-acom-offerdesk}"
WEB_CLIENT_ID="${KEYCLOAK_WEB_CLIENT_ID:-${KEYCLOAK_CLIENT_ID:-acom-web}}"
API_CLIENT_ID="${KEYCLOAK_API_CLIENT_ID:-acom-api}"
ADMIN_SERVICE_CLIENT_ID="${KEYCLOAK_ADMIN_CLIENT_ID:-acom-admin-service}"
ADMIN_SERVICE_CLIENT_SECRET="${KEYCLOAK_ADMIN_CLIENT_SECRET:-}"
BACKEND_BASE_URL="${PUBLIC_BACKEND_BASE_URL:-http://localhost:8080}"
WEB_BASE_URL="${WEB_BASE_URL:-http://localhost:8080}"
BOOTSTRAP_USERNAME="${KEYCLOAK_BOOTSTRAP_APP_USERNAME:-superadmin}"
BOOTSTRAP_PASSWORD="${KEYCLOAK_BOOTSTRAP_APP_PASSWORD:-}"
BOOTSTRAP_EMAIL="${KEYCLOAK_BOOTSTRAP_APP_EMAIL:-${BOOTSTRAP_USERNAME}@local.invalid}"
BOOTSTRAP_FIRST_NAME="${KEYCLOAK_BOOTSTRAP_APP_FIRST_NAME:-Bootstrap}"
BOOTSTRAP_LAST_NAME="${KEYCLOAK_BOOTSTRAP_APP_LAST_NAME:-Superadmin}"
SMTP_HOST="${KEYCLOAK_SMTP_HOST:-${SMTP_HOST:-}}"
SMTP_PORT="${KEYCLOAK_SMTP_PORT:-${SMTP_PORT:-}}"
SMTP_USERNAME="${KEYCLOAK_SMTP_USERNAME:-${EMAIL_ADDRESS:-}}"
SMTP_PASSWORD="${KEYCLOAK_SMTP_PASSWORD:-${EMAIL_APP_PASSWORD:-}}"
SMTP_FROM="${KEYCLOAK_SMTP_FROM:-${EMAIL_ADDRESS:-}}"
SMTP_REPLY_TO="${KEYCLOAK_SMTP_REPLY_TO:-${EMAIL_ADDRESS:-}}"
SMTP_FROM_DISPLAY_NAME="${KEYCLOAK_SMTP_FROM_DISPLAY_NAME:-${EMAIL_FROM_NAME:-AcomOfferDesk}}"
SMTP_AUTH="${KEYCLOAK_SMTP_AUTH:-true}"
SMTP_SSL="${KEYCLOAK_SMTP_SSL:-}"
SMTP_STARTTLS="${KEYCLOAK_SMTP_STARTTLS:-}"
KEYCLOAK_VERIFY_EMAIL="${KEYCLOAK_VERIFY_EMAIL:-}"
KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS="${KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS:-1800}"
KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS="${KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS:-86400}"
KEYCLOAK_ACCESS_CODE_LIFESPAN_SECONDS="${KEYCLOAK_ACCESS_CODE_LIFESPAN_SECONDS:-300}"
KEYCLOAK_ACCESS_CODE_USER_ACTION_LIFESPAN_SECONDS="${KEYCLOAK_ACCESS_CODE_USER_ACTION_LIFESPAN_SECONDS:-1800}"
KEYCLOAK_ACCESS_CODE_LOGIN_LIFESPAN_SECONDS="${KEYCLOAK_ACCESS_CODE_LOGIN_LIFESPAN_SECONDS:-1800}"
KEYCLOAK_ACTION_TOKEN_USER_LIFESPAN_SECONDS="${KEYCLOAK_ACTION_TOKEN_USER_LIFESPAN_SECONDS:-1800}"

BACKEND_BASE_URL="${BACKEND_BASE_URL%/}"
WEB_BASE_URL="${WEB_BASE_URL%/}"

APP_ENV_NORMALIZED="$(printf '%s' "${APP_ENV:-development}" | tr '[:upper:]' '[:lower:]')"

is_true() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    true|1|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

is_weak_secret() {
  normalized="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  [ -z "$normalized" ] && return 0
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

refresh_kcadm_credentials() {
  until /opt/keycloak/bin/kcadm.sh config credentials \
    --server "$SERVER_URL" \
    --realm "$MASTER_REALM" \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" >/dev/null 2>&1
  do
    sleep 3
  done
}

apply_realm_mail_and_session_settings() {
  REALM_UPDATE_FILE="$(mktemp)"

  if [ -n "$SMTP_HOST" ] && [ -n "$SMTP_PORT" ] && [ -n "$SMTP_USERNAME" ] && [ -n "$SMTP_PASSWORD" ] && [ -n "$SMTP_FROM" ]; then
    if [ -z "$SMTP_SSL" ] && [ -z "$SMTP_STARTTLS" ]; then
      if [ "$SMTP_PORT" = "465" ]; then
        SMTP_SSL="true"
        SMTP_STARTTLS="false"
      else
        SMTP_SSL="false"
        SMTP_STARTTLS="true"
      fi
    fi

    cat >"$REALM_UPDATE_FILE" <<EOF
{
  "verifyEmail": $KEYCLOAK_VERIFY_EMAIL,
  "ssoSessionIdleTimeout": $KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS,
  "ssoSessionIdleTimeoutRememberMe": $KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS,
  "ssoSessionMaxLifespan": $KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS,
  "ssoSessionMaxLifespanRememberMe": $KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS,
  "clientSessionIdleTimeout": $KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS,
  "clientSessionMaxLifespan": $KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS,
  "accessCodeLifespan": $KEYCLOAK_ACCESS_CODE_LIFESPAN_SECONDS,
  "accessCodeLifespanUserAction": $KEYCLOAK_ACCESS_CODE_USER_ACTION_LIFESPAN_SECONDS,
  "accessCodeLifespanLogin": $KEYCLOAK_ACCESS_CODE_LOGIN_LIFESPAN_SECONDS,
  "actionTokenGeneratedByUserLifespan": $KEYCLOAK_ACTION_TOKEN_USER_LIFESPAN_SECONDS,
  "revokeRefreshToken": true,
  "loginTheme": "acom-offerdesk",
  "internationalizationEnabled": true,
  "defaultLocale": "ru",
  "supportedLocales": ["ru"],
  "smtpServer": {
    "auth": "$SMTP_AUTH",
    "host": "$SMTP_HOST",
    "port": "$SMTP_PORT",
    "user": "$SMTP_USERNAME",
    "password": "$SMTP_PASSWORD",
    "from": "$SMTP_FROM",
    "replyTo": "$SMTP_REPLY_TO",
    "fromDisplayName": "$SMTP_FROM_DISPLAY_NAME",
    "ssl": "$SMTP_SSL",
    "starttls": "$SMTP_STARTTLS"
  }
}
EOF
  else
    cat >"$REALM_UPDATE_FILE" <<EOF
{
  "verifyEmail": $KEYCLOAK_VERIFY_EMAIL,
  "ssoSessionIdleTimeout": $KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS,
  "ssoSessionIdleTimeoutRememberMe": $KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS,
  "ssoSessionMaxLifespan": $KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS,
  "ssoSessionMaxLifespanRememberMe": $KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS,
  "clientSessionIdleTimeout": $KEYCLOAK_SSO_IDLE_TIMEOUT_SECONDS,
  "clientSessionMaxLifespan": $KEYCLOAK_SSO_MAX_LIFESPAN_SECONDS,
  "accessCodeLifespan": $KEYCLOAK_ACCESS_CODE_LIFESPAN_SECONDS,
  "accessCodeLifespanUserAction": $KEYCLOAK_ACCESS_CODE_USER_ACTION_LIFESPAN_SECONDS,
  "accessCodeLifespanLogin": $KEYCLOAK_ACCESS_CODE_LOGIN_LIFESPAN_SECONDS,
  "actionTokenGeneratedByUserLifespan": $KEYCLOAK_ACTION_TOKEN_USER_LIFESPAN_SECONDS,
  "revokeRefreshToken": true,
  "loginTheme": "acom-offerdesk",
  "internationalizationEnabled": true,
  "defaultLocale": "ru",
  "supportedLocales": ["ru"]
}
EOF
    echo "Keycloak SMTP configuration is incomplete; updating only realm verifyEmail=$KEYCLOAK_VERIFY_EMAIL"
  fi

  /opt/keycloak/bin/kcadm.sh update "realms/$APP_REALM" -f "$REALM_UPDATE_FILE"
  rm -f "$REALM_UPDATE_FILE"
  echo "[realm] Applied mail/session settings (smtp host=${SMTP_HOST:-<none>} port=${SMTP_PORT:-<none>})"
}

apply_user_profile_configuration() {
  USER_PROFILE_FILE="$(mktemp)"
  cat >"$USER_PROFILE_FILE" <<'EOF'
{
  "attributes": [
    {
      "name": "username",
      "displayName": "${username}",
      "validations": {
        "length": {
          "min": 3,
          "max": 255
        },
        "username-prohibited-characters": {},
        "up-username-not-idn-homograph": {}
      },
      "permissions": {
        "view": ["admin", "user"],
        "edit": ["admin", "user"]
      },
      "multivalued": false
    },
    {
      "name": "email",
      "displayName": "${email}",
      "validations": {
        "email": {},
        "length": {
          "max": 255
        }
      },
      "required": {
        "roles": ["user"]
      },
      "permissions": {
        "view": ["admin", "user"],
        "edit": ["admin", "user"]
      },
      "multivalued": false
    },
    {
      "name": "lastName",
      "displayName": "${lastName}",
      "validations": {
        "length": {
          "max": 255
        },
        "person-name-prohibited-characters": {}
      },
      "required": {
        "roles": ["user"]
      },
      "permissions": {
        "view": ["admin", "user"],
        "edit": ["admin", "user"]
      },
      "multivalued": false
    },
    {
      "name": "firstName",
      "displayName": "${firstName}",
      "validations": {
        "length": {
          "max": 255
        },
        "person-name-prohibited-characters": {}
      },
      "required": {
        "roles": ["user"]
      },
      "permissions": {
        "view": ["admin", "user"],
        "edit": ["admin", "user"]
      },
      "multivalued": false
    },
    {
      "name": "middleName",
      "displayName": "Отчество",
      "validations": {
        "length": {
          "max": 255
        },
        "person-name-prohibited-characters": {}
      },
      "required": {
        "roles": ["user"]
      },
      "permissions": {
        "view": ["admin", "user"],
        "edit": ["admin", "user"]
      },
      "multivalued": false
    }
  ],
  "groups": [
    {
      "name": "user-metadata",
      "displayHeader": "User metadata",
      "displayDescription": "Attributes, which refer to user metadata"
    }
  ]
}
EOF

  /opt/keycloak/bin/kcadm.sh update users/profile -r "$APP_REALM" -f "$USER_PROFILE_FILE"
  rm -f "$USER_PROFILE_FILE"
  echo "[realm] Applied user profile schema with middleName"
}

if [ -z "$ADMIN_SERVICE_CLIENT_SECRET" ] || is_weak_secret "$ADMIN_SERVICE_CLIENT_SECRET"; then
  if [ "$APP_ENV_NORMALIZED" = "production" ]; then
    echo "KEYCLOAK_ADMIN_CLIENT_SECRET must be set to a strong non-placeholder value"
    exit 1
  fi
  echo "WARN: KEYCLOAK_ADMIN_CLIENT_SECRET uses a weak placeholder outside production"
fi

if [ "$APP_ENV_NORMALIZED" = "production" ]; then
  if [ "${BACKEND_BASE_URL#https://}" = "$BACKEND_BASE_URL" ] || [ "${WEB_BASE_URL#https://}" = "$WEB_BASE_URL" ]; then
    echo "PUBLIC_BACKEND_BASE_URL and WEB_BASE_URL must use https in production"
    exit 1
  fi
fi

PERMISSION_ROLE_NAMES=$(cat <<'EOF'
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
normative_files.status.update
files.download
unavailability.manage_all
unavailability.manage_own
unavailability.manage_subordinate
contractors.read
contractors.profile.read
contractors.profile.status.update
contractors.manual.create
contractors.manual.manage
department.requests.read
department.requests.update
department.requests.status_update
department.requests.assign
department.offers.update
department.offers.accept
department.offers.reject
department.chats.read
department.files.read
department.files.upload
department.files.delete
department.dashboard.read
department.plans.read
department.plans.manage
EOF
)

APP_ROLE_NAMES=$(cat <<'EOF'
app.superadmin
app.admin
app.project_manager
app.lead_economist
app.economist
app.operator
app.contractor
EOF
)

CONTRACTOR_DELEGATION_ROLE_NAMES=$(cat <<'EOF'
delegation.contractors.profile.status.update
EOF
)

DEPARTMENT_DELEGATION_ROLE_NAMES=$(cat <<'EOF'
delegation.department.requests.read
delegation.department.requests.update
delegation.department.requests.status_update
delegation.department.requests.assign
delegation.department.offers.update
delegation.department.offers.accept
delegation.department.offers.reject
delegation.department.chats.read
delegation.department.files.read
delegation.department.files.upload
delegation.department.files.delete
delegation.department.dashboard.read
delegation.department.plans.read
delegation.department.plans.manage
EOF
)

ALL_ROLE_NAMES=$(cat <<EOF
$PERMISSION_ROLE_NAMES
$APP_ROLE_NAMES
$CONTRACTOR_DELEGATION_ROLE_NAMES
$DEPARTMENT_DELEGATION_ROLE_NAMES
EOF
)

ROLE_APP_SUPERADMIN=$(cat <<EOF
$PERMISSION_ROLE_NAMES
app.admin
app.project_manager
app.lead_economist
app.economist
app.operator
app.contractor
EOF
)
ROLE_APP_ADMIN=$(cat <<'EOF'
profile.manage_own
feedback.create
users.read
users.create
users.status.update
users.role.update_any
users.login.update
users.password.update
profile.manage_any
company_contacts.manage_any
contractors.manual.create
contractors.manual.manage
EOF
)
ROLE_APP_CONTRACTOR=$(cat <<'EOF'
profile.manage_own
feedback.create
company_contacts.manage_own
requests.open.read
requests.offered.read
requests.contractor_view.read
offers.create
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
files.download
EOF
)
ROLE_APP_PROJECT_MANAGER=$(cat <<'EOF'
profile.manage_own
feedback.create
requests.read
offers.workspace.read
offers.contractor_info.read
chat.read
files.download
users.read
contractors.read
contractors.profile.read
users.status.update
users.role.update_economy
users.manager.update
requests.owner.change
requests.amounts.read
normative_files.read
dashboard.process.read
dashboard.savings.read
dashboard.plans.read
contractors.manual.create
contractors.manual.manage
unavailability.manage_subordinate
unavailability.manage_own
EOF
)
ROLE_APP_LEAD_ECONOMIST=$(cat <<'EOF'
profile.manage_own
feedback.create
requests.read
offers.workspace.read
offers.contractor_info.read
chat.read
files.download
requests.create
requests.update
requests.pricing.update
requests.deadline.update
requests.status.update
requests.amounts.read
requests.files.upload
requests.files.delete
requests.email_notifications.send
requests.deleted_alerts.mark_viewed
offers.update
offers.amount.update
offers.details.update
offers.status.update
chat.message.send
chat.message.attach
chat.receipts.mark_received
chat.receipts.mark_read
users.read
contractors.read
contractors.profile.read
users.create
users.status.update
users.role.update_economy
users.manager.update
requests.owner.change
normative_files.read
dashboard.process.read
dashboard.savings.read
dashboard.plans.read
unavailability.manage_subordinate
normative_files.manage
normative_files.create
normative_files.status.update
profile.manage_any
company_contacts.manage_any
unavailability.manage_own
offers.manual.create
contractors.manual.create
contractors.manual.manage
EOF
)
ROLE_APP_ECONOMIST=$(cat <<'EOF'
profile.manage_own
feedback.create
requests.read
offers.workspace.read
offers.contractor_info.read
chat.read
files.download
requests.create
requests.update
requests.pricing.update
requests.deadline.update
requests.status.update
requests.amounts.read
requests.files.upload
requests.files.delete
requests.email_notifications.send
requests.deleted_alerts.mark_viewed
offers.update
offers.amount.update
offers.details.update
offers.status.update
chat.message.send
chat.message.attach
chat.receipts.mark_received
chat.receipts.mark_read
users.read
contractors.read
contractors.profile.read
users.status.update
users.manager.update
normative_files.read
dashboard.process.read
dashboard.savings.read
dashboard.plans.read
unavailability.manage_own
unavailability.manage_subordinate
offers.manual.create
contractors.manual.create
contractors.manual.manage
EOF
)
ROLE_APP_OPERATOR=$(cat <<'EOF'
profile.manage_own
feedback.create
requests.read
requests.create
requests.update
requests.pricing.update
requests.deadline.update
requests.status.update
requests.amounts.read
offers.contractor_info.read
normative_files.read
EOF
)
ROLE_DELEGATION_CONTRACTORS_PROFILE_STATUS_UPDATE=$(cat <<'EOF'
contractors.read
contractors.profile.read
contractors.profile.status.update
EOF
)
ROLE_DELEGATION_DEPARTMENT_REQUESTS_READ=$(cat <<'EOF'
department.requests.read
EOF
)
ROLE_DELEGATION_DEPARTMENT_REQUESTS_UPDATE=$(cat <<'EOF'
department.requests.update
EOF
)
ROLE_DELEGATION_DEPARTMENT_REQUESTS_STATUS_UPDATE=$(cat <<'EOF'
department.requests.status_update
EOF
)
ROLE_DELEGATION_DEPARTMENT_REQUESTS_ASSIGN=$(cat <<'EOF'
department.requests.assign
EOF
)
ROLE_DELEGATION_DEPARTMENT_OFFERS_UPDATE=$(cat <<'EOF'
department.offers.update
EOF
)
ROLE_DELEGATION_DEPARTMENT_OFFERS_ACCEPT=$(cat <<'EOF'
department.offers.accept
EOF
)
ROLE_DELEGATION_DEPARTMENT_OFFERS_REJECT=$(cat <<'EOF'
department.offers.reject
EOF
)
ROLE_DELEGATION_DEPARTMENT_CHATS_READ=$(cat <<'EOF'
department.chats.read
EOF
)
ROLE_DELEGATION_DEPARTMENT_FILES_READ=$(cat <<'EOF'
department.files.read
EOF
)
ROLE_DELEGATION_DEPARTMENT_FILES_UPLOAD=$(cat <<'EOF'
department.files.upload
EOF
)
ROLE_DELEGATION_DEPARTMENT_FILES_DELETE=$(cat <<'EOF'
department.files.delete
EOF
)
ROLE_DELEGATION_DEPARTMENT_DASHBOARD_READ=$(cat <<'EOF'
department.dashboard.read
EOF
)
ROLE_DELEGATION_DEPARTMENT_PLANS_READ=$(cat <<'EOF'
department.plans.read
EOF
)
ROLE_DELEGATION_DEPARTMENT_PLANS_MANAGE=$(cat <<'EOF'
department.plans.manage
EOF
)
if [ -z "$KEYCLOAK_VERIFY_EMAIL" ]; then
  if [ "$APP_ENV_NORMALIZED" = "production" ]; then
    KEYCLOAK_VERIFY_EMAIL="true"
  else
    KEYCLOAK_VERIFY_EMAIL="false"
  fi
fi

if [ "$APP_ENV_NORMALIZED" = "production" ] && ! is_true "$KEYCLOAK_VERIFY_EMAIL"; then
  echo "KEYCLOAK_VERIFY_EMAIL must be true in production"
  exit 1
fi

if [ "$APP_ENV_NORMALIZED" = "production" ]; then
  if [ -z "$SMTP_HOST" ] || [ -z "$SMTP_PORT" ] || [ -z "$SMTP_USERNAME" ] || [ -z "$SMTP_PASSWORD" ] || [ -z "$SMTP_FROM" ]; then
    echo "SMTP config is required in production when Keycloak email flows are enabled"
    exit 1
  fi
fi

if [ -z "${KC_BOOTSTRAP_ADMIN_USERNAME:-}" ] || [ -z "${KC_BOOTSTRAP_ADMIN_PASSWORD:-}" ]; then
  echo "Keycloak bootstrap admin credentials are required"
  exit 1
fi

refresh_kcadm_credentials

if ! /opt/keycloak/bin/kcadm.sh get "realms/$APP_REALM" >/dev/null 2>&1; then
  echo "Realm $APP_REALM is not available"
  exit 1
fi

apply_realm_mail_and_session_settings
apply_user_profile_configuration

_CACHED_API_CLIENT_UUID=""

get_client_uuid() {
  client_id="$1"
  client_search=$(/opt/keycloak/bin/kcadm.sh get "clients?clientId=$client_id" -r "$APP_REALM")
  printf '%s' "$client_search" | tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1
}

resolve_api_client_uuid() {
  if [ -n "$_CACHED_API_CLIENT_UUID" ]; then
    printf '%s' "$_CACHED_API_CLIENT_UUID"
    return 0
  fi
  _CACHED_API_CLIENT_UUID="$(get_client_uuid "$API_CLIENT_ID")"
  printf '%s' "$_CACHED_API_CLIENT_UUID"
}

get_client_role_id() {
  client_uuid="$1"
  role_name="$2"
  role_payload=$(/opt/keycloak/bin/kcadm.sh get "clients/$client_uuid/roles/$role_name" -r "$APP_REALM")
  printf '%s' "$role_payload" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1
}

get_user_uuid() {
  username="$1"
  user_search=$(/opt/keycloak/bin/kcadm.sh get "users?username=$username&exact=true" -r "$APP_REALM")
  printf '%s' "$user_search" | tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1
}

payload_has_role_name() {
  payload="$1"
  role_name="$2"
  printf '%s' "$payload" | grep -Eq "\"name\"[[:space:]]*:[[:space:]]*\"$role_name\""
}

create_single_role_payload_file() {
  client_uuid="$1"
  role_name="$2"
  role_payload=$(/opt/keycloak/bin/kcadm.sh get "clients/$client_uuid/roles/$role_name" -r "$APP_REALM")
  payload_file="$(mktemp)"
  printf '[%s]\n' "$role_payload" >"$payload_file"
  printf '%s\n' "$payload_file"
}

ensure_user_has_client_role() {
  user_uuid="$1"
  client_uuid="$2"
  role_name="$3"

  current_mappings=$(/opt/keycloak/bin/kcadm.sh get "users/$user_uuid/role-mappings/clients/$client_uuid" -r "$APP_REALM")
  if payload_has_role_name "$current_mappings" "$role_name"; then
    return 0
  fi

  payload_file="$(create_single_role_payload_file "$client_uuid" "$role_name")"
  /opt/keycloak/bin/kcadm.sh create "users/$user_uuid/role-mappings/clients/$client_uuid" -r "$APP_REALM" -f "$payload_file" >/dev/null
  rm -f "$payload_file"
}

list_role_names_from_payload() {
  payload="$1"
  printf '%s' "$payload" | tr '{' '\n' | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

role_name_in_list() {
  needle="$1"
  haystack="$2"
  printf '%s\n' "$haystack" | grep -Fxq "$needle"
}

clear_role_composites() {
  client_uuid="$1"
  role_name="$2"

  current_composites=$(/opt/keycloak/bin/kcadm.sh get "clients/$client_uuid/roles/$role_name/composites" -r "$APP_REALM" 2>/dev/null || printf '[]')
  if ! printf '%s' "$current_composites" | grep -Eq '"name"[[:space:]]*:[[:space:]]*"'; then
    return 0
  fi

  payload_file="$(mktemp)"
  printf '%s' "$current_composites" >"$payload_file"
  if /opt/keycloak/bin/kcadm.sh delete "clients/$client_uuid/roles/$role_name/composites" -r "$APP_REALM" -f "$payload_file" >/dev/null 2>&1; then
    rm -f "$payload_file"
    return 0
  fi
  rm -f "$payload_file"

  # Fallback: member-by-member delete when bulk payload is rejected.
  list_role_names_from_payload "$current_composites" | while IFS= read -r member_role; do
    if [ -z "$member_role" ]; then
      continue
    fi
    remove_composite_role_member "$client_uuid" "$role_name" "$member_role"
  done
}

enforce_atomic_permission_roles() {
  api_client_uuid="$(resolve_api_client_uuid)"
  if [ -z "$api_client_uuid" ]; then
    echo "Unable to resolve API client UUID for $API_CLIENT_ID"
    exit 1
  fi

  while IFS= read -r role_name; do
    if [ -z "$role_name" ]; then
      continue
    fi
    clear_role_composites "$api_client_uuid" "$role_name"
    /opt/keycloak/bin/kcadm.sh update "clients/$api_client_uuid/roles/$role_name" -r "$APP_REALM" \
      -s "name=$role_name" \
      -s composite=false \
      -s clientRole=true >/dev/null
  done <<EOF
$PERMISSION_ROLE_NAMES
EOF
}

ensure_composite_role_has_member() {
  client_uuid="$1"
  composite_role_name="$2"
  member_role_name="$3"

  current_composites=$(/opt/keycloak/bin/kcadm.sh get "clients/$client_uuid/roles/$composite_role_name/composites" -r "$APP_REALM")
  if payload_has_role_name "$current_composites" "$member_role_name"; then
    return 0
  fi

  payload_file="$(create_single_role_payload_file "$client_uuid" "$member_role_name")"
  /opt/keycloak/bin/kcadm.sh create "clients/$client_uuid/roles/$composite_role_name/composites" -r "$APP_REALM" -f "$payload_file" >/dev/null
  rm -f "$payload_file"
}

ensure_composite_role_has_member_force() {
  client_uuid="$1"
  composite_role_name="$2"
  member_role_name="$3"

  payload_file="$(create_single_role_payload_file "$client_uuid" "$member_role_name")"
  # Force-add: ignore possible duplicates / already-present errors.
  /opt/keycloak/bin/kcadm.sh create "clients/$client_uuid/roles/$composite_role_name/composites" -r "$APP_REALM" -f "$payload_file" >/dev/null 2>&1 || true
  rm -f "$payload_file"
}

remove_composite_role_member() {
  client_uuid="$1"
  composite_role_name="$2"
  member_role_name="$3"

  payload_file="$(create_single_role_payload_file "$client_uuid" "$member_role_name")"
  /opt/keycloak/bin/kcadm.sh delete "clients/$client_uuid/roles/$composite_role_name/composites" -r "$APP_REALM" -f "$payload_file" >/dev/null 2>&1 || true
  rm -f "$payload_file"
}

ensure_web_client() {
  client_uuid="$(get_client_uuid "$WEB_CLIENT_ID")"
  if [ -z "$client_uuid" ]; then
    /opt/keycloak/bin/kcadm.sh create clients -r "$APP_REALM" \
      -s "clientId=$WEB_CLIENT_ID" \
      -s "name=AcomOfferDesk Web" \
      -s enabled=true \
      -s publicClient=true \
      -s standardFlowEnabled=true \
      -s directAccessGrantsEnabled=false \
      -s implicitFlowEnabled=false \
      -s serviceAccountsEnabled=false \
      -s fullScopeAllowed=true \
      -s "rootUrl=$WEB_BASE_URL" \
      -s "baseUrl=$WEB_BASE_URL" \
      -s 'webOrigins=["'"$WEB_BASE_URL"'"]' \
      -s 'redirectUris=["'"$BACKEND_BASE_URL"'/api/v1/auth/callback"]'
    client_uuid="$(get_client_uuid "$WEB_CLIENT_ID")"
  else
    /opt/keycloak/bin/kcadm.sh update "clients/$client_uuid" -r "$APP_REALM" \
      -s enabled=true \
      -s publicClient=true \
      -s standardFlowEnabled=true \
      -s directAccessGrantsEnabled=false \
      -s implicitFlowEnabled=false \
      -s serviceAccountsEnabled=false \
      -s fullScopeAllowed=true \
      -s "rootUrl=$WEB_BASE_URL" \
      -s "baseUrl=$WEB_BASE_URL" \
      -s 'webOrigins=["'"$WEB_BASE_URL"'"]' \
      -s 'redirectUris=["'"$BACKEND_BASE_URL"'/api/v1/auth/callback"]'
  fi
}

ensure_api_client() {
  client_uuid="$(get_client_uuid "$API_CLIENT_ID")"
  if [ -z "$client_uuid" ]; then
    /opt/keycloak/bin/kcadm.sh create clients -r "$APP_REALM" \
      -s "clientId=$API_CLIENT_ID" \
      -s "name=AcomOfferDesk API Roles" \
      -s enabled=true \
      -s publicClient=false \
      -s clientAuthenticatorType=client-secret \
      -s standardFlowEnabled=false \
      -s directAccessGrantsEnabled=false \
      -s implicitFlowEnabled=false \
      -s serviceAccountsEnabled=false \
      -s fullScopeAllowed=true
    client_uuid="$(get_client_uuid "$API_CLIENT_ID")"
  else
    /opt/keycloak/bin/kcadm.sh update "clients/$client_uuid" -r "$APP_REALM" \
      -s enabled=true \
      -s publicClient=false \
      -s clientAuthenticatorType=client-secret \
      -s standardFlowEnabled=false \
      -s directAccessGrantsEnabled=false \
      -s implicitFlowEnabled=false \
      -s serviceAccountsEnabled=false \
      -s fullScopeAllowed=true
  fi
}

ensure_admin_service_client() {
  client_uuid="$(get_client_uuid "$ADMIN_SERVICE_CLIENT_ID")"
  if [ -z "$client_uuid" ]; then
    /opt/keycloak/bin/kcadm.sh create clients -r "$APP_REALM" \
      -s "clientId=$ADMIN_SERVICE_CLIENT_ID" \
      -s "name=AcomOfferDesk Admin Service" \
      -s enabled=true \
      -s publicClient=false \
      -s clientAuthenticatorType=client-secret \
      -s "secret=$ADMIN_SERVICE_CLIENT_SECRET" \
      -s standardFlowEnabled=false \
      -s directAccessGrantsEnabled=false \
      -s implicitFlowEnabled=false \
      -s serviceAccountsEnabled=true \
      -s fullScopeAllowed=false
    client_uuid="$(get_client_uuid "$ADMIN_SERVICE_CLIENT_ID")"
  else
    /opt/keycloak/bin/kcadm.sh update "clients/$client_uuid" -r "$APP_REALM" \
      -s enabled=true \
      -s publicClient=false \
      -s clientAuthenticatorType=client-secret \
      -s "secret=$ADMIN_SERVICE_CLIENT_SECRET" \
      -s standardFlowEnabled=false \
      -s directAccessGrantsEnabled=false \
      -s implicitFlowEnabled=false \
      -s serviceAccountsEnabled=true \
      -s fullScopeAllowed=false
  fi
}

ensure_client_role() {
  client_uuid="$1"
  role_name="$2"
  composite_flag="$3"

  if /opt/keycloak/bin/kcadm.sh get "clients/$client_uuid/roles/$role_name" -r "$APP_REALM" >/dev/null 2>&1; then
    # Role exists. Final role shape is enforced later by:
    # - enforce_atomic_permission_roles (atomic permissions),
    # - sync_composite_role (app.* and delegation.department.*).
    return 0
  else
    /opt/keycloak/bin/kcadm.sh create "clients/$client_uuid/roles" -r "$APP_REALM" \
      -s "name=$role_name" \
      -s "composite=$composite_flag" \
      -s clientRole=true >/dev/null
  fi
}

sync_composite_role() {
  role_name="$1"
  desired_members="$2"
  api_client_uuid="$(resolve_api_client_uuid)"

  if [ -z "$api_client_uuid" ]; then
    echo "Unable to resolve API client UUID for $API_CLIENT_ID"
    exit 1
  fi

  /opt/keycloak/bin/kcadm.sh update "clients/$api_client_uuid/roles/$role_name" -r "$APP_REALM" \
    -s "name=$role_name" \
    -s composite=true \
    -s clientRole=true >/dev/null

  current_composites=$(/opt/keycloak/bin/kcadm.sh get "clients/$api_client_uuid/roles/$role_name/composites" -r "$APP_REALM" 2>/dev/null || printf '[]')
  current_member_names="$(list_role_names_from_payload "$current_composites")"

  desired_members_file="$(mktemp)"
  printf '%s\n' "$desired_members" >"$desired_members_file"
  while IFS= read -r member_role; do
    if [ -n "$member_role" ] && [ "$member_role" != "$role_name" ] && ! role_name_in_list "$member_role" "$current_member_names"; then
      ensure_composite_role_has_member "$api_client_uuid" "$role_name" "$member_role"
    fi
  done <"$desired_members_file"

  current_composites=$(/opt/keycloak/bin/kcadm.sh get "clients/$api_client_uuid/roles/$role_name/composites" -r "$APP_REALM" 2>/dev/null || printf '[]')
  for member_role in $(list_role_names_from_payload "$current_composites"); do
    if [ -z "$member_role" ] || [ "$member_role" = "$role_name" ]; then
      continue
    fi
    if ! role_name_in_list "$member_role" "$desired_members"; then
      remove_composite_role_member "$api_client_uuid" "$role_name" "$member_role"
    fi
  done

  rm -f "$desired_members_file"
}

_verify_atomic_permission_roles() {
  api_client_uuid="$1"
  verify_failed=0

  while IFS= read -r role_name; do
    if [ -z "$role_name" ]; then
      continue
    fi
    role_payload=$(/opt/keycloak/bin/kcadm.sh get "clients/$api_client_uuid/roles/$role_name" -r "$APP_REALM" 2>/dev/null || printf '{}')
    if printf '%s' "$role_payload" | grep -Eq '"composite"[[:space:]]*:[[:space:]]*true'; then
      echo "VERIFY_FAIL: permission role '$role_name' must be composite=false"
      verify_failed=1
    fi
    composites=$(/opt/keycloak/bin/kcadm.sh get "clients/$api_client_uuid/roles/$role_name/composites" -r "$APP_REALM" 2>/dev/null || printf '[]')
    if printf '%s' "$composites" | grep -Eq '"name"[[:space:]]*:[[:space:]]*"'; then
      echo "VERIFY_FAIL: permission role '$role_name' must not have composite members"
      verify_failed=1
    fi
  done <<EOF
$PERMISSION_ROLE_NAMES
EOF

  return "$verify_failed"
}

verify_keycloak_permission_model_silent() {
  api_client_uuid="$(resolve_api_client_uuid)"
  if [ -z "$api_client_uuid" ]; then
    return 1
  fi
  _verify_atomic_permission_roles "$api_client_uuid"
}

verify_keycloak_permission_model() {
  api_client_uuid="$(resolve_api_client_uuid)"
  if [ -z "$api_client_uuid" ]; then
    echo "VERIFY_FAIL: unable to resolve API client UUID for $API_CLIENT_ID"
    exit 1
  fi

  if ! _verify_atomic_permission_roles "$api_client_uuid"; then
    exit 1
  fi

  echo "VERIFY_OK: atomic permission roles have no nested composites"
}

ensure_api_roles_model() {
  api_client_uuid="$(resolve_api_client_uuid)"
  if [ -z "$api_client_uuid" ]; then
    echo "Unable to resolve API client UUID for $API_CLIENT_ID"
    exit 1
  fi

  echo "[1/6] Ensuring atomic permission roles exist in $API_CLIENT_ID"
  printf '%s\n' "$PERMISSION_ROLE_NAMES" | while IFS= read -r role_name; do
    if [ -n "$role_name" ]; then
      ensure_client_role "$api_client_uuid" "$role_name" "false"
    fi
  done

  echo "[2/6] Ensuring app.* composite roles exist"
  printf '%s\n' "$APP_ROLE_NAMES" | while IFS= read -r role_name; do
    if [ -n "$role_name" ]; then
      ensure_client_role "$api_client_uuid" "$role_name" "true"
    fi
  done

  echo "[3/7] Ensuring delegation.contractors.* composite roles exist"
  printf '%s\n' "$CONTRACTOR_DELEGATION_ROLE_NAMES" | while IFS= read -r role_name; do
    if [ -n "$role_name" ]; then
      ensure_client_role "$api_client_uuid" "$role_name" "true"
    fi
  done

  echo "[4/7] Ensuring delegation.department.* composite roles exist"
  printf '%s\n' "$DEPARTMENT_DELEGATION_ROLE_NAMES" | while IFS= read -r role_name; do
    if [ -n "$role_name" ]; then
      ensure_client_role "$api_client_uuid" "$role_name" "true"
    fi
  done

  echo "[5/7] Enforcing atomic permission roles (no nested composites)"
  enforce_atomic_permission_roles

  echo "[6/7] Syncing composite membership for app.* and delegation.*"
  refresh_kcadm_credentials
  sync_composite_role "app.superadmin" "$ROLE_APP_SUPERADMIN"
  sync_composite_role "app.admin" "$ROLE_APP_ADMIN"
  sync_composite_role "app.contractor" "$ROLE_APP_CONTRACTOR"
  sync_composite_role "app.project_manager" "$ROLE_APP_PROJECT_MANAGER"
  sync_composite_role "app.lead_economist" "$ROLE_APP_LEAD_ECONOMIST"
  sync_composite_role "app.economist" "$ROLE_APP_ECONOMIST"
  sync_composite_role "app.operator" "$ROLE_APP_OPERATOR"
  sync_composite_role "delegation.contractors.profile.status.update" "$ROLE_DELEGATION_CONTRACTORS_PROFILE_STATUS_UPDATE"
  sync_composite_role "delegation.department.requests.read" "$ROLE_DELEGATION_DEPARTMENT_REQUESTS_READ"
  sync_composite_role "delegation.department.requests.update" "$ROLE_DELEGATION_DEPARTMENT_REQUESTS_UPDATE"
  sync_composite_role "delegation.department.requests.status_update" "$ROLE_DELEGATION_DEPARTMENT_REQUESTS_STATUS_UPDATE"
  sync_composite_role "delegation.department.requests.assign" "$ROLE_DELEGATION_DEPARTMENT_REQUESTS_ASSIGN"
  sync_composite_role "delegation.department.offers.update" "$ROLE_DELEGATION_DEPARTMENT_OFFERS_UPDATE"
  sync_composite_role "delegation.department.offers.accept" "$ROLE_DELEGATION_DEPARTMENT_OFFERS_ACCEPT"
  sync_composite_role "delegation.department.offers.reject" "$ROLE_DELEGATION_DEPARTMENT_OFFERS_REJECT"
  sync_composite_role "delegation.department.chats.read" "$ROLE_DELEGATION_DEPARTMENT_CHATS_READ"
  sync_composite_role "delegation.department.files.read" "$ROLE_DELEGATION_DEPARTMENT_FILES_READ"
  sync_composite_role "delegation.department.files.upload" "$ROLE_DELEGATION_DEPARTMENT_FILES_UPLOAD"
  sync_composite_role "delegation.department.files.delete" "$ROLE_DELEGATION_DEPARTMENT_FILES_DELETE"
  sync_composite_role "delegation.department.dashboard.read" "$ROLE_DELEGATION_DEPARTMENT_DASHBOARD_READ"
  sync_composite_role "delegation.department.plans.read" "$ROLE_DELEGATION_DEPARTMENT_PLANS_READ"
  sync_composite_role "delegation.department.plans.manage" "$ROLE_DELEGATION_DEPARTMENT_PLANS_MANAGE"

  # Force ensure direct membership for newly introduced contractor profile status permissions.
  # Some environments may have pre-existing role composition artifacts; this makes the bootstrap idempotent.
  api_client_uuid="$(resolve_api_client_uuid)"
  ensure_composite_role_has_member_force "$api_client_uuid" "app.superadmin" "contractors.profile.read"
  ensure_composite_role_has_member_force "$api_client_uuid" "app.superadmin" "contractors.profile.status.update"
  ensure_composite_role_has_member_force "$api_client_uuid" "delegation.contractors.profile.status.update" "contractors.profile.read"
  ensure_composite_role_has_member_force "$api_client_uuid" "delegation.contractors.profile.status.update" "contractors.profile.status.update"

  # Always re-apply after composite sync:
  # this keeps department.* and all other atomic permission roles strictly leaf.
  echo "KEYCLOAK_BOOTSTRAP: re-applying enforce_atomic after composite sync"
  enforce_atomic_permission_roles

  echo "[7/7] Verifying final Keycloak permission model"
  verify_keycloak_permission_model
}

ensure_admin_service_role_bindings() {
  # Required for backend KeycloakAdminService operations:
  # lookup users, create/update users, reset passwords, terminate sessions.
  service_account_user_uuid="$(get_user_uuid "service-account-$ADMIN_SERVICE_CLIENT_ID")"
  realm_management_uuid="$(get_client_uuid "realm-management")"

  if [ -z "$service_account_user_uuid" ] || [ -z "$realm_management_uuid" ]; then
    echo "Unable to resolve service account or realm-management client for $ADMIN_SERVICE_CLIENT_ID"
    exit 1
  fi

  ensure_user_has_client_role "$service_account_user_uuid" "$realm_management_uuid" "query-users"
  ensure_user_has_client_role "$service_account_user_uuid" "$realm_management_uuid" "view-users"
  ensure_user_has_client_role "$service_account_user_uuid" "$realm_management_uuid" "manage-users"
  # Required for read-only permission-model checks (realm, clients, roles).
  ensure_user_has_client_role "$service_account_user_uuid" "$realm_management_uuid" "view-realm"
  ensure_user_has_client_role "$service_account_user_uuid" "$realm_management_uuid" "query-clients"
  ensure_user_has_client_role "$service_account_user_uuid" "$realm_management_uuid" "view-clients"
}

ensure_bootstrap_user() {
  USER_SEARCH=$(/opt/keycloak/bin/kcadm.sh get "users?username=$BOOTSTRAP_USERNAME&exact=true" -r "$APP_REALM")
  USER_UUID=$(printf '%s' "$USER_SEARCH" | tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

  if [ -z "$USER_UUID" ]; then
    /opt/keycloak/bin/kcadm.sh create users -r "$APP_REALM" \
      -s "username=$BOOTSTRAP_USERNAME" \
      -s enabled=true \
      -s emailVerified=true \
      -s "email=$BOOTSTRAP_EMAIL" \
      -s "firstName=$BOOTSTRAP_FIRST_NAME" \
      -s "lastName=$BOOTSTRAP_LAST_NAME"
    USER_SEARCH=$(/opt/keycloak/bin/kcadm.sh get "users?username=$BOOTSTRAP_USERNAME&exact=true" -r "$APP_REALM")
    USER_UUID=$(printf '%s' "$USER_SEARCH" | tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
  fi

  if [ -n "$USER_UUID" ]; then
    USER_UPDATE_FILE="$(mktemp)"
    cat >"$USER_UPDATE_FILE" <<EOF
{
  "enabled": true,
  "emailVerified": true,
  "email": "$BOOTSTRAP_EMAIL",
  "firstName": "$BOOTSTRAP_FIRST_NAME",
  "lastName": "$BOOTSTRAP_LAST_NAME",
  "requiredActions": ["UPDATE_PASSWORD"]
}
EOF
    /opt/keycloak/bin/kcadm.sh update "users/$USER_UUID" -r "$APP_REALM" -f "$USER_UPDATE_FILE"
    rm -f "$USER_UPDATE_FILE"

    if [ -n "$BOOTSTRAP_PASSWORD" ]; then
      /opt/keycloak/bin/kcadm.sh set-password -r "$APP_REALM" \
        --userid "$USER_UUID" \
        --new-password "$BOOTSTRAP_PASSWORD" \
        --temporary
    fi

    api_client_uuid="$(get_client_uuid "$API_CLIENT_ID")"
    if [ -z "$api_client_uuid" ]; then
      echo "Unable to resolve API client UUID for $API_CLIENT_ID"
      exit 1
    fi

    ensure_user_has_client_role "$USER_UUID" "$api_client_uuid" "app.superadmin"
  fi
}

refresh_kcadm_credentials
apply_realm_mail_and_session_settings

ensure_web_client
ensure_api_client
ensure_admin_service_client
ensure_api_roles_model
ensure_admin_service_role_bindings
ensure_bootstrap_user
