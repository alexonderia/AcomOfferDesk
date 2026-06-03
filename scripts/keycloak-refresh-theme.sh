#!/usr/bin/env bash
# Re-copy login theme from themes-src into /opt/keycloak/themes (prepare-theme.sh).
# Needed after git pull: Keycloak entrypoint runs prepare-theme only on container start.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_ENV_FILE="${1:-backend/.env}"
export APP_RUNTIME_ENV_FILE="./$COMPOSE_ENV_FILE"

if [ "$(docker inspect -f '{{.State.Running}}' keycloak 2>/dev/null || echo false)" != "true" ]; then
  echo "KEYCLOAK_THEME: keycloak is not running — start infra first"
  exit 1
fi

echo "KEYCLOAK_THEME: running prepare-theme.sh in keycloak container"
docker compose --env-file "$COMPOSE_ENV_FILE" exec -T keycloak \
  sh /opt/keycloak/bootstrap/prepare-theme.sh

if docker exec keycloak grep -q '^middleName=Отчество$' \
  /opt/keycloak/themes/acom-offerdesk/login/messages/messages_ru.properties 2>/dev/null; then
  echo "KEYCLOAK_THEME: OK (middleName label present in active theme)"
else
  echo "KEYCLOAK_THEME: WARN — middleName=Отчество missing in container theme after refresh" >&2
  exit 1
fi
