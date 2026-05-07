#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${BASE_URL:-}" ]]; then
  export E2E_BASE_URL="$BASE_URL"
fi

ENV_FILE="${ENV_FILE:-.env.dev}"
PROVISION_USERS="${PROVISION_USERS:-false}"
KEEP_PROVISIONED_USERS="${KEEP_PROVISIONED_USERS:-false}"
PROVISION_STATE_FILE=""
export PYTHONPATH="$ROOT_DIR/backend"

if [[ "${STRICT_CREDENTIALS:-false}" == "true" || "${STRICT_CREDENTIALS:-0}" == "1" ]]; then
  export E2E_STRICT_CREDENTIALS=true
fi

cleanup_provisioned_users() {
  if [[ -n "$PROVISION_STATE_FILE" && "$KEEP_PROVISIONED_USERS" != "true" && "$KEEP_PROVISIONED_USERS" != "1" ]]; then
    python -m app.scripts.e2e_provision_users cleanup --env-file "$ENV_FILE" --state-file "$PROVISION_STATE_FILE"
  elif [[ -n "$PROVISION_STATE_FILE" ]]; then
    echo "Provisioned E2E users were kept. State file: $PROVISION_STATE_FILE"
  fi
}

if [[ "$PROVISION_USERS" == "true" || "$PROVISION_USERS" == "1" ]]; then
  provision_json="$(python -m app.scripts.e2e_provision_users provision --env-file "$ENV_FILE" --state-dir ".tmp/e2e")"
  PROVISION_STATE_FILE="$(printf '%s' "$provision_json" | python -c 'import json,sys; print(json.load(sys.stdin)["state_file"])')"
  export E2E_SUPERADMIN_USERNAME="$(printf '%s' "$provision_json" | python -c 'import json,sys; data=json.load(sys.stdin); print(next(u["username"] for u in data["users"] if u["prefix"]=="E2E_SUPERADMIN"))')"
  export E2E_SUPERADMIN_PASSWORD="$(printf '%s' "$provision_json" | python -c 'import json,sys; data=json.load(sys.stdin); print(next(u["password"] for u in data["users"] if u["prefix"]=="E2E_SUPERADMIN"))')"
  export E2E_ECONOMIST_USERNAME="$(printf '%s' "$provision_json" | python -c 'import json,sys; data=json.load(sys.stdin); print(next(u["username"] for u in data["users"] if u["prefix"]=="E2E_ECONOMIST"))')"
  export E2E_ECONOMIST_PASSWORD="$(printf '%s' "$provision_json" | python -c 'import json,sys; data=json.load(sys.stdin); print(next(u["password"] for u in data["users"] if u["prefix"]=="E2E_ECONOMIST"))')"
  export E2E_CONTRACTOR_USERNAME="$(printf '%s' "$provision_json" | python -c 'import json,sys; data=json.load(sys.stdin); print(next(u["username"] for u in data["users"] if u["prefix"]=="E2E_CONTRACTOR"))')"
  export E2E_CONTRACTOR_PASSWORD="$(printf '%s' "$provision_json" | python -c 'import json,sys; data=json.load(sys.stdin); print(next(u["password"] for u in data["users"] if u["prefix"]=="E2E_CONTRACTOR"))')"
  export E2E_STRICT_CREDENTIALS=true
  trap cleanup_provisioned_users EXIT
fi

CMD=(npm --prefix web exec -- playwright test --config web/playwright.config.ts --grep @smoke)
if [[ "${HEADED:-false}" == "true" || "${HEADED:-0}" == "1" ]]; then
  CMD+=(--headed)
fi

"${CMD[@]}"
