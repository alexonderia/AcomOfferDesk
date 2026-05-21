#!/usr/bin/env bash
# Local/dev: run on the host with a repo env file (e.g. .env.dev).
# VPS/prod (running backend container): do NOT docker exec with /app/backend/.env — that path
# is not in the image. Use ./scripts/run-keycloak-check-backend.sh or ./scripts/post-deploy-verify.sh
# from the host; they inject compose env and pass a temp snapshot to the checker.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-${ENV_FILE:-.env.dev}}"
STRICT_UNKNOWN_ATOMIC="${STRICT_UNKNOWN_ATOMIC:-false}"
KEYCLOAK_PERMISSION_REPAIR="${KEYCLOAK_PERMISSION_REPAIR:-false}"

export PYTHONPATH="$ROOT_DIR/backend"
PYTHON_CMD="python"
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_CMD="$ROOT_DIR/.venv/bin/python"
fi

CMD=("$PYTHON_CMD" -m app.scripts.check_keycloak_permission_model --env-file "$ENV_FILE")
if [[ "$STRICT_UNKNOWN_ATOMIC" == "true" || "$STRICT_UNKNOWN_ATOMIC" == "1" ]]; then
  CMD+=(--strict-unknown-atomic)
fi
if [[ "$KEYCLOAK_PERMISSION_REPAIR" == "true" || "$KEYCLOAK_PERMISSION_REPAIR" == "1" ]]; then
  CMD+=(--repair)
fi

"${CMD[@]}"
