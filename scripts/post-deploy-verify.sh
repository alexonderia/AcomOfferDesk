#!/usr/bin/env bash
# Post-deploy gate on VPS: infrastructure smoke + Keycloak permission model (read-only).
# Uses env from the running backend container (same secrets as production traffic).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-backend/.env}"
CONTAINER_ENV_PATH="/tmp/post-deploy-verify.env"
BASE_URL="${POST_DEPLOY_BASE_URL:-}"

if ! docker network inspect project_net >/dev/null 2>&1; then
  echo "POST_DEPLOY_VERIFY: Docker network project_net is missing" >&2
  exit 1
fi

if ! docker inspect --format '{{.State.Running}}' backend 2>/dev/null | grep -q true; then
  echo "POST_DEPLOY_VERIFY: backend container is not running" >&2
  exit 1
fi

echo "=== post-deploy: materialize env from running backend ==="
docker compose --env-file "$COMPOSE_ENV_FILE" exec -T backend python - <<'PY'
import os

path = "/tmp/post-deploy-verify.env"
skip_prefixes = ("_",)
skip_keys = {"PATH", "HOSTNAME", "HOME", "TERM", "SHLVL", "PWD", "PYTHONPATH"}

with open(path, "w", encoding="utf-8") as handle:
    for key, value in sorted(os.environ.items()):
        if key in skip_keys or key.startswith(skip_prefixes):
            continue
        if not key.isupper():
            continue
        safe = value.replace("\n", "\\n")
        handle.write(f"{key}={safe}\n")
PY

SMOKE_EXTRA=()
if [[ -n "$BASE_URL" ]]; then
  SMOKE_EXTRA+=(--base-url "$BASE_URL")
fi

# Shorter timeouts for deploy gate (avoid long hangs on optional deps).
SMOKE_ENV=(
  -e SMOKE_HTTP_TIMEOUT_SECONDS=8
  -e SMOKE_HTTP_RETRIES=1
)

run_in_backend() {
  local module="$1"
  shift
  docker compose --env-file "$COMPOSE_ENV_FILE" exec -T \
    "${SMOKE_ENV[@]}" \
    -e KEYCLOAK_INTERNAL_BASE_URL="${KEYCLOAK_INTERNAL_BASE_URL:-http://keycloak:8080/iam}" \
    -e PYTHONUNBUFFERED=1 \
    backend \
    python -m "$module" --env-file "$CONTAINER_ENV_PATH" "$@"
}

echo "=== post-deploy: infrastructure smoke (smoke_services) ==="
if ! run_in_backend app.scripts.smoke_services "${SMOKE_EXTRA[@]}"; then
  echo "POST_DEPLOY_VERIFY: smoke_services failed" >&2
  exit 1
fi

echo "=== post-deploy: Keycloak permission model (read-only) ==="
if ! run_in_backend app.scripts.check_keycloak_permission_model; then
  echo "POST_DEPLOY_VERIFY: check_keycloak_permission_model failed" >&2
  exit 1
fi

docker compose --env-file "$COMPOSE_ENV_FILE" exec -T backend rm -f "$CONTAINER_ENV_PATH" >/dev/null 2>&1 || true

echo "POST_DEPLOY_VERIFY: all checks passed"
