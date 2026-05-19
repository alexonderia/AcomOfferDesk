#!/usr/bin/env bash
# Post-deploy gate on VPS: infrastructure smoke + Keycloak permission model (read-only).
# Runs inside the backend image on project_net so Docker DNS names resolve.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-backend/.env}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-backend/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "POST_DEPLOY_VERIFY: env file not found: $ENV_FILE" >&2
  exit 1
fi

if ! docker network inspect project_net >/dev/null 2>&1; then
  echo "POST_DEPLOY_VERIFY: Docker network project_net is missing" >&2
  exit 1
fi

ENV_IN_CONTAINER="/tmp/post-deploy-verify.env"
BASE_URL="${POST_DEPLOY_BASE_URL:-}"
SMOKE_EXTRA=()
if [[ -n "$BASE_URL" ]]; then
  SMOKE_EXTRA+=(--base-url "$BASE_URL")
fi

run_backend_script() {
  local module="$1"
  shift
  docker compose --env-file "$COMPOSE_ENV_FILE" run --rm --no-deps \
    -v "$ROOT_DIR/$ENV_FILE:$ENV_IN_CONTAINER:ro" \
    -e KEYCLOAK_INTERNAL_BASE_URL="${KEYCLOAK_INTERNAL_BASE_URL:-http://keycloak:8080/iam}" \
    backend \
    python -m "$module" --env-file "$ENV_IN_CONTAINER" "$@"
}

echo "=== post-deploy: infrastructure smoke (smoke_services) ==="
run_backend_script app.scripts.smoke_services "${SMOKE_EXTRA[@]}"

echo "=== post-deploy: Keycloak permission model (read-only) ==="
run_backend_script app.scripts.check_keycloak_permission_model

echo "POST_DEPLOY_VERIFY: all checks passed"
