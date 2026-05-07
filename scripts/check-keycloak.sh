#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-${ENV_FILE:-.env.dev}}"
STRICT_UNKNOWN_ATOMIC="${STRICT_UNKNOWN_ATOMIC:-false}"

export PYTHONPATH="$ROOT_DIR/backend"

CMD=(python -m app.scripts.check_keycloak_permission_model --env-file "$ENV_FILE")
if [[ "$STRICT_UNKNOWN_ATOMIC" == "true" || "$STRICT_UNKNOWN_ATOMIC" == "1" ]]; then
  CMD+=(--strict-unknown-atomic)
fi

"${CMD[@]}"