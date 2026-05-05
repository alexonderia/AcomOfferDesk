#!/bin/sh
set -e
set -u

SERVER_URL="${KEYCLOAK_INTERNAL_BASE_URL:-${KEYCLOAK_INTERNAL_URL:-http://keycloak:8080/iam}}"
MASTER_REALM="${KEYCLOAK_MASTER_REALM:-master}"
APP_REALM="${KEYCLOAK_REALM:-acom-offerdesk}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-acom-offerdesk-web}"
BACKEND_BASE_URL="${PUBLIC_BACKEND_BASE_URL:-http://localhost:8080}"
WEB_BASE_URL="${WEB_BASE_URL:-http://localhost:8080}"
BOOTSTRAP_USERNAME="${KEYCLOAK_BOOTSTRAP_APP_USERNAME:-superadmin}"
BOOTSTRAP_PASSWORD="${KEYCLOAK_BOOTSTRAP_APP_PASSWORD:-}"
BOOTSTRAP_EMAIL="${KEYCLOAK_BOOTSTRAP_APP_EMAIL:-${BOOTSTRAP_USERNAME}@local.invalid}"
BOOTSTRAP_FIRST_NAME="${KEYCLOAK_BOOTSTRAP_APP_FIRST_NAME:-Bootstrap}"
BOOTSTRAP_LAST_NAME="${KEYCLOAK_BOOTSTRAP_APP_LAST_NAME:-Superadmin}"
SMTP_HOST="${SMTP_HOST:-}"
SMTP_PORT="${SMTP_PORT:-}"
SMTP_USERNAME="${KEYCLOAK_SMTP_USERNAME:-${EMAIL_ADDRESS:-}}"
SMTP_PASSWORD="${KEYCLOAK_SMTP_PASSWORD:-${EMAIL_APP_PASSWORD:-}}"
SMTP_FROM="${KEYCLOAK_SMTP_FROM:-${EMAIL_ADDRESS:-}}"
SMTP_REPLY_TO="${KEYCLOAK_SMTP_REPLY_TO:-${EMAIL_ADDRESS:-}}"
SMTP_FROM_DISPLAY_NAME="${KEYCLOAK_SMTP_FROM_DISPLAY_NAME:-${EMAIL_FROM_NAME:-AcomOfferDesk}}"
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

if [ -z "$KEYCLOAK_VERIFY_EMAIL" ]; then
  if [ "${APP_ENV:-development}" = "production" ]; then
    KEYCLOAK_VERIFY_EMAIL="true"
  else
    KEYCLOAK_VERIFY_EMAIL="false"
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

if ! /opt/keycloak/bin/kcadm.sh get "realms/$APP_REALM" >/dev/null 2>&1; then
  echo "Realm $APP_REALM is not available"
  exit 1
fi

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
    "auth": "true",
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

CLIENT_SEARCH=$(/opt/keycloak/bin/kcadm.sh get "clients?clientId=$CLIENT_ID" -r "$APP_REALM")
CLIENT_UUID=$(printf '%s' "$CLIENT_SEARCH" | tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

if [ -z "$CLIENT_UUID" ]; then
  /opt/keycloak/bin/kcadm.sh create clients -r "$APP_REALM" \
    -s "clientId=$CLIENT_ID" \
    -s "name=AcomOfferDesk Web" \
    -s enabled=true \
    -s publicClient=true \
    -s standardFlowEnabled=true \
    -s directAccessGrantsEnabled=false \
    -s implicitFlowEnabled=false \
    -s "rootUrl=$WEB_BASE_URL" \
    -s "baseUrl=$WEB_BASE_URL" \
    -s 'webOrigins=["'"$WEB_BASE_URL"'"]' \
    -s 'redirectUris=["'"$BACKEND_BASE_URL"'/api/v1/auth/callback"]'
  CLIENT_SEARCH=$(/opt/keycloak/bin/kcadm.sh get "clients?clientId=$CLIENT_ID" -r "$APP_REALM")
  CLIENT_UUID=$(printf '%s' "$CLIENT_SEARCH" | tr '{' '\n' | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
else
  /opt/keycloak/bin/kcadm.sh update "clients/$CLIENT_UUID" -r "$APP_REALM" \
    -s "rootUrl=$WEB_BASE_URL" \
    -s "baseUrl=$WEB_BASE_URL" \
    -s 'webOrigins=["'"$WEB_BASE_URL"'"]' \
    -s 'redirectUris=["'"$BACKEND_BASE_URL"'/api/v1/auth/callback"]'
fi

if [ -n "$BOOTSTRAP_PASSWORD" ]; then
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
    /opt/keycloak/bin/kcadm.sh set-password -r "$APP_REALM" \
      --userid "$USER_UUID" \
      --new-password "$BOOTSTRAP_PASSWORD" \
      --temporary
  fi
fi

