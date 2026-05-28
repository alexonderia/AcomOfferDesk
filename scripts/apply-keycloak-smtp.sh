#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.prod-like}"
KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
APPLY_SCRIPT_HOST="${APPLY_SCRIPT_HOST:-$ROOT_DIR/infra/keycloak/apply-realm-smtp.sh}"
APPLY_SCRIPT_CONTAINER="${APPLY_SCRIPT_CONTAINER:-/opt/keycloak/bootstrap/apply-realm-smtp.sh}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "FAIL: env file not found: $ENV_FILE"
  exit 1
fi

if [[ ! -f "$APPLY_SCRIPT_HOST" ]]; then
  echo "FAIL: apply script not found: $APPLY_SCRIPT_HOST"
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -qx "$KEYCLOAK_CONTAINER"; then
  echo "FAIL: container '$KEYCLOAK_CONTAINER' is not running"
  exit 1
fi

docker cp "$APPLY_SCRIPT_HOST" "${KEYCLOAK_CONTAINER}:/tmp/apply-realm-smtp.sh"

docker exec --env-file "$ENV_FILE" \
  -e KEYCLOAK_APPLY_SMTP_SERVER_URL=http://127.0.0.1:8080/iam \
  "$KEYCLOAK_CONTAINER" \
  /bin/sh -lc "tr -d '\r' < /tmp/apply-realm-smtp.sh > /tmp/apply-realm-smtp-fixed.sh && /bin/sh /tmp/apply-realm-smtp-fixed.sh"
