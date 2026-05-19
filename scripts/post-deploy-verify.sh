#!/usr/bin/env bash
# Post-deploy gate on VPS: infrastructure smoke + Keycloak permission model (read-only).
# Uses the running backend container (project_net) — avoids slow/unhealthy compose run sidecars.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-backend/.env}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-backend/.env}"
CONTAINER_ENV_PATH="/tmp/post-deploy-verify.env"
BASE_URL="${POST_DEPLOY_BASE_URL:-}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "POST_DEPLOY_VERIFY: env file not found: $ENV_FILE" >&2
  exit 1
fi

if ! docker network inspect project_net >/dev/null 2>&1; then
  echo "POST_DEPLOY_VERIFY: Docker network project_net is missing" >&2
  exit 1
fi

if ! docker inspect --format '{{.State.Running}}' backend 2>/dev/null | grep -q true; then
  echo "POST_DEPLOY_VERIFY: backend container is not running" >&2
  exit 1
fi

docker cp "$ROOT_DIR/$ENV_FILE" "backend:$CONTAINER_ENV_PATH" >/dev/null

SMOKE_EXTRA=()
if [[ -n "$BASE_URL" ]]; then
  SMOKE_EXTRA+=(--base-url "$BASE_URL")
fi

run_in_backend() {
  local module="$1"
  shift
  docker compose --env-file "$COMPOSE_ENV_FILE" exec -T \
    -e KEYCLOAK_INTERNAL_BASE_URL="${KEYCLOAK_INTERNAL_BASE_URL:-http://keycloak:8080/iam}" \
    backend \
    python -m "$module" --env-file "$CONTAINER_ENV_PATH" "$@"
}

echo "=== post-deploy: infrastructure smoke (smoke_services) ==="
run_in_backend app.scripts.smoke_services "${SMOKE_EXTRA[@]}"

echo "=== post-deploy: Keycloak permission model (read-only) ==="
run_in_backend app.scripts.check_keycloak_permission_model

docker exec backend rm -f "$CONTAINER_ENV_PATH" >/dev/null 2>&1 || true

echo "POST_DEPLOY_VERIFY: all checks passed"
