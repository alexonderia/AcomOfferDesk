#!/usr/bin/env bash
# Keycloak init on VPS: skip long bootstrap when model is OK; repair on verify failure.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_ENV_FILE="${1:-backend/.env}"
export APP_RUNTIME_ENV_FILE="./$COMPOSE_ENV_FILE"
export COMPOSE_ENV_FILE

STATE_DIR="$ROOT_DIR/.deploy-state"
BOOTSTRAP_SCRIPT="$ROOT_DIR/infra/keycloak/bootstrap.sh"
BOOTSTRAP_SHA_FILE="$STATE_DIR/keycloak-bootstrap.sha256"
mkdir -p "$STATE_DIR"

run_compose_init() {
  local service="$1"
  local run_name="$2"
  if ! docker compose --env-file "$COMPOSE_ENV_FILE" -f docker-compose.init.yml run --rm --no-deps --name "$run_name" "$service"; then
    return 1
  fi
}

keycloak_model_ok() {
  "$ROOT_DIR/scripts/run-keycloak-check-backend.sh" --env-file "$COMPOSE_ENV_FILE"
}

current_bootstrap_sha() {
  sha256sum "$BOOTSTRAP_SCRIPT" | awk '{print $1}'
}

should_skip_bootstrap() {
  if [ "${KEYCLOAK_BOOTSTRAP_FORCE:-0}" = "1" ] || [ "${KEYCLOAK_BOOTSTRAP_FORCE:-}" = "true" ]; then
    echo "KEYCLOAK_BOOTSTRAP: force full run (KEYCLOAK_BOOTSTRAP_FORCE)"
    return 1
  fi

  local current_sha stored_sha
  current_sha="$(current_bootstrap_sha)"
  stored_sha=""
  if [ -f "$BOOTSTRAP_SHA_FILE" ]; then
    stored_sha="$(tr -d '[:space:]' <"$BOOTSTRAP_SHA_FILE")"
  fi

  if [ "$current_sha" != "$stored_sha" ]; then
    if [ -z "$stored_sha" ]; then
      echo "KEYCLOAK_BOOTSTRAP: no deploy state yet — checking if full bootstrap is needed..."
      if keycloak_model_ok; then
        printf '%s\n' "$current_sha" >"$BOOTSTRAP_SHA_FILE"
        echo "KEYCLOAK_BOOTSTRAP: skip full bootstrap (model already OK, recorded sha)"
        return 0
      fi
      echo "KEYCLOAK_BOOTSTRAP: model check failed — running full bootstrap"
      return 1
    fi
    echo "KEYCLOAK_BOOTSTRAP: bootstrap.sh changed (stored=$stored_sha current=$current_sha)"
    return 1
  fi

  echo "KEYCLOAK_BOOTSTRAP: checking permission model (read-only)..."
  if keycloak_model_ok; then
    echo "KEYCLOAK_BOOTSTRAP: skip full bootstrap (model OK, script unchanged)"
    return 0
  fi

  echo "KEYCLOAK_BOOTSTRAP: model check failed — running full bootstrap"
  return 1
}

docker rm -f keycloak_db_prepare keycloak_bootstrap keycloak_user_role_sync >/dev/null 2>&1 || true

if ! run_compose_init keycloak_db_prepare keycloak_db_prepare_run; then
  echo "=== keycloak_db_prepare failed ===" >&2
  exit 1
fi

if should_skip_bootstrap; then
  :
else
  if ! run_compose_init keycloak_bootstrap keycloak_bootstrap_run; then
    echo "=== keycloak_bootstrap failed ===" >&2
    docker compose --env-file "$COMPOSE_ENV_FILE" logs --tail=160 keycloak || true
    exit 1
  fi
  current_bootstrap_sha >"$BOOTSTRAP_SHA_FILE"
  echo "KEYCLOAK_BOOTSTRAP: recorded sha in $BOOTSTRAP_SHA_FILE"
fi

if ! run_compose_init keycloak_user_role_sync keycloak_user_role_sync_run; then
  echo "=== keycloak_user_role_sync failed ===" >&2
  docker compose --env-file "$COMPOSE_ENV_FILE" logs --tail=160 backend || true
  exit 1
fi

PUBLIC_BASE_URL="$(grep -E '^(WEB_BASE_URL|PUBLIC_BACKEND_BASE_URL)=' "$COMPOSE_ENV_FILE" | head -n 1 | cut -d= -f2- | tr -d '\r' | sed -e 's/^["'\'']//' -e 's/["'\'']$//')"
if [ -z "$PUBLIC_BASE_URL" ]; then
  PUBLIC_BASE_URL="http://127.0.0.1:8080"
fi

chmod +x "$ROOT_DIR/scripts/post-deploy-verify.sh" "$ROOT_DIR/scripts/run-keycloak-check-backend.sh"

if POST_DEPLOY_BASE_URL="$PUBLIC_BASE_URL" "$ROOT_DIR/scripts/post-deploy-verify.sh" "$COMPOSE_ENV_FILE"; then
  echo "KEYCLOAK_INIT_DEPLOY: post-deploy verify passed"
  exit 0
fi

echo "KEYCLOAK_INIT_DEPLOY: post-deploy failed — attempting Keycloak repair (Python Admin API)..." >&2
if KEYCLOAK_PERMISSION_REPAIR=1 "$ROOT_DIR/scripts/run-keycloak-check-backend.sh" --repair --env-file "$COMPOSE_ENV_FILE"; then
  if POST_DEPLOY_BASE_URL="$PUBLIC_BASE_URL" "$ROOT_DIR/scripts/post-deploy-verify.sh" "$COMPOSE_ENV_FILE"; then
    echo "KEYCLOAK_INIT_DEPLOY: post-deploy verify passed after repair"
    exit 0
  fi
fi

echo "KEYCLOAK_INIT_DEPLOY: post-deploy verify still failing" >&2
docker compose --env-file "$COMPOSE_ENV_FILE" ps -a || true
exit 1
