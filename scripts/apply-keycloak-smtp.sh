#!/usr/bin/env bash
# Re-apply realm SMTP settings from the selected env file to a running Keycloak container.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.prod-like}"
KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
APPLY_SCRIPT_HOST="${APPLY_SCRIPT_HOST:-$ROOT_DIR/infra/keycloak/apply-realm-smtp.sh}"
APPLY_SCRIPT_CONTAINER="${APPLY_SCRIPT_CONTAINER:-/opt/keycloak/bootstrap/apply-realm-smtp.sh}"

if command -v docker.exe >/dev/null 2>&1; then
  DOCKER_BIN="docker.exe"
elif command -v docker >/dev/null 2>&1; then
  DOCKER_BIN="docker"
else
  echo "FAIL: docker CLI is not available"
  exit 1
fi

DOCKER_ENV_FILE="$ENV_FILE"
DOCKER_APPLY_SCRIPT_HOST="$APPLY_SCRIPT_HOST"
if [[ "$DOCKER_BIN" == "docker.exe" ]] && command -v wslpath >/dev/null 2>&1; then
  DOCKER_ENV_FILE="$(wslpath -w "$ENV_FILE")"
  DOCKER_APPLY_SCRIPT_HOST="$(wslpath -w "$APPLY_SCRIPT_HOST")"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "FAIL: env file not found: $ENV_FILE"
  exit 1
fi

if [[ ! -f "$APPLY_SCRIPT_HOST" ]]; then
  echo "FAIL: apply script not found: $APPLY_SCRIPT_HOST"
  exit 1
fi

container_running="$("$DOCKER_BIN" inspect -f '{{.State.Running}}' "$KEYCLOAK_CONTAINER" 2>/dev/null | tr -d '\r' || true)"
if [[ "$container_running" != "true" ]]; then
  echo "FAIL: container '$KEYCLOAK_CONTAINER' is not running"
  exit 1
fi

"$DOCKER_BIN" cp "$DOCKER_APPLY_SCRIPT_HOST" "${KEYCLOAK_CONTAINER}:/tmp/apply-realm-smtp.sh"

"$DOCKER_BIN" exec --env-file "$DOCKER_ENV_FILE" \
  -e KEYCLOAK_APPLY_SMTP_SERVER_URL=http://127.0.0.1:8080/iam \
  "$KEYCLOAK_CONTAINER" \
  /bin/sh -lc "tr -d '\r' < /tmp/apply-realm-smtp.sh > /tmp/apply-realm-smtp-fixed.sh && /bin/sh /tmp/apply-realm-smtp-fixed.sh"
