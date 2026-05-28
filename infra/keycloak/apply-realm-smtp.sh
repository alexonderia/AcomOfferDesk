#!/bin/sh
# Apply realm smtpServer from env. Safe to re-run after SMTP env changes.
set -e
set -u

SERVER_URL="${KEYCLOAK_APPLY_SMTP_SERVER_URL:-${KEYCLOAK_INTERNAL_BASE_URL:-${KEYCLOAK_INTERNAL_URL:-http://127.0.0.1:8080/iam}}}"
MASTER_REALM="${KEYCLOAK_MASTER_REALM:-master}"
APP_REALM="${KEYCLOAK_REALM:-acom-offerdesk}"

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

if [ -z "$SMTP_HOST" ] || [ -z "$SMTP_PORT" ] || [ -z "$SMTP_USERNAME" ] || [ -z "$SMTP_PASSWORD" ] || [ -z "$SMTP_FROM" ]; then
  echo "Keycloak SMTP env is incomplete (need host/port/user/password/from)"
  exit 1
fi

if [ -z "$SMTP_SSL" ] && [ -z "$SMTP_STARTTLS" ]; then
  if [ "$SMTP_PORT" = "465" ]; then
    SMTP_SSL="true"
    SMTP_STARTTLS="false"
  else
    SMTP_SSL="false"
    SMTP_STARTTLS="true"
  fi
fi

if [ -z "${KC_BOOTSTRAP_ADMIN_USERNAME:-}" ] || [ -z "${KC_BOOTSTRAP_ADMIN_PASSWORD:-}" ]; then
  echo "Keycloak bootstrap admin credentials are required"
  exit 1
fi

until /opt/keycloak/bin/kcadm.sh config credentials \
  --server "$SERVER_URL" \
  --realm "$MASTER_REALM" \
  --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
  --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" >/dev/null 2>&1
do
  sleep 3
done

REALM_UPDATE_FILE="$(mktemp)"
cat >"$REALM_UPDATE_FILE" <<EOF
{
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

/opt/keycloak/bin/kcadm.sh update "realms/$APP_REALM" -f "$REALM_UPDATE_FILE"
rm -f "$REALM_UPDATE_FILE"

echo "Keycloak realm SMTP applied: host=$SMTP_HOST port=$SMTP_PORT ssl=$SMTP_SSL starttls=$SMTP_STARTTLS auth=$SMTP_AUTH"
