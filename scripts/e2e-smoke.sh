#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.dev}"
PROVISION_USERS="${PROVISION_USERS:-false}"
KEEP_PROVISIONED_USERS="${KEEP_PROVISIONED_USERS:-false}"
PROVISION_STATE_FILE=""
export PYTHONPATH="$ROOT_DIR/backend"
PYTHON_CMD="python"
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_CMD="$ROOT_DIR/.venv/bin/python"
fi

if [[ "$ENV_FILE" = /* ]]; then
  ENV_FILE_PATH="$ENV_FILE"
else
  ENV_FILE_PATH="$ROOT_DIR/$ENV_FILE"
fi

if [[ ! -f "$ENV_FILE_PATH" ]]; then
  echo "Env file not found: $ENV_FILE_PATH" >&2
  exit 1
fi

get_env_value() {
  local key="$1"
  awk -F= -v key="$key" '
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    {
      name=$1
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", name)
      if (name != key) {
        next
      }
      value = substr($0, index($0, "=") + 1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      if ((value ~ /^".*"$/) || (value ~ /^'\''.*'\''$/)) {
        value = substr(value, 2, length(value) - 2)
      }
      print value
      exit
    }
  ' "$ENV_FILE_PATH"
}

normalize_async_database_url() {
  local url="$1"
  if [[ "$url" == postgresql://* ]]; then
    printf 'postgresql+asyncpg://%s\n' "${url#postgresql://}"
    return
  fi
  printf '%s\n' "$url"
}

if [[ -n "${BASE_URL:-}" ]]; then
  export E2E_BASE_URL="$BASE_URL"
elif [[ -z "${E2E_BASE_URL:-}" ]]; then
  derived_base_url="$(get_env_value "WEB_BASE_URL")"
  if [[ -z "$derived_base_url" ]]; then
    derived_base_url="$(get_env_value "PUBLIC_BACKEND_BASE_URL")"
  fi
  if [[ -n "$derived_base_url" ]]; then
    export E2E_BASE_URL="$derived_base_url"
    echo "Using E2E_BASE_URL=$derived_base_url from $ENV_FILE"
  fi
fi

if [[ "${STRICT_CREDENTIALS:-false}" == "true" || "${STRICT_CREDENTIALS:-0}" == "1" ]]; then
  export E2E_STRICT_CREDENTIALS=true
fi

cleanup_provisioned_users() {
  if [[ -n "$PROVISION_STATE_FILE" && "$KEEP_PROVISIONED_USERS" != "true" && "$KEEP_PROVISIONED_USERS" != "1" ]]; then
    "$PYTHON_CMD" -m app.scripts.e2e_provision_users cleanup --env-file "$ENV_FILE" --state-file "$PROVISION_STATE_FILE"
  elif [[ -n "$PROVISION_STATE_FILE" ]]; then
    echo "Provisioned E2E users were kept. State file: $PROVISION_STATE_FILE"
  fi
}

if [[ "$PROVISION_USERS" == "true" || "$PROVISION_USERS" == "1" ]]; then
  export KEYCLOAK_HTTP_TIMEOUT_SECONDS=30

  internal_base="$(get_env_value "KEYCLOAK_INTERNAL_BASE_URL")"
  public_base="$(get_env_value "KEYCLOAK_PUBLIC_BASE_URL")"
  realm="$(get_env_value "KEYCLOAK_REALM")"
  realm="${realm:-acom-offerdesk}"

  if [[ -n "$public_base" && "$internal_base" =~ ://keycloak(:[0-9]+)?/ ]]; then
    local_keycloak_base="http://127.0.0.1:8080/iam"
    if curl -fsS --max-time 5 "${local_keycloak_base}/realms/${realm}" >/dev/null 2>&1; then
      export KEYCLOAK_INTERNAL_BASE_URL="$local_keycloak_base"
      echo "Using local KEYCLOAK_INTERNAL_BASE_URL=$local_keycloak_base for provisioning"
    else
      export KEYCLOAK_INTERNAL_BASE_URL="$public_base"
      echo "Using host-accessible KEYCLOAK_INTERNAL_BASE_URL=$public_base for provisioning"
    fi
  fi

  database_override="$(get_env_value "SMOKE_DATABASE_URL")"
  if [[ -z "$database_override" ]]; then
    database_override="$(get_env_value "DATABASE_URL")"
    database_override="${database_override/@order-database-postgres:/@127.0.0.1:}"
  fi
  if [[ -n "$database_override" ]]; then
    export DATABASE_URL="$(normalize_async_database_url "$database_override")"
    echo "Using host-accessible DATABASE_URL for provisioning"
  fi

  provision_json="$("$PYTHON_CMD" -m app.scripts.e2e_provision_users provision --env-file "$ENV_FILE" --state-dir ".tmp/e2e")"
  PROVISION_STATE_FILE="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; print(json.load(sys.stdin)["state_file"])')"
  export E2E_SUPERADMIN_USERNAME="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; data=json.load(sys.stdin); print(next(u["username"] for u in data["users"] if u["prefix"]=="E2E_SUPERADMIN"))')"
  export E2E_SUPERADMIN_PASSWORD="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; data=json.load(sys.stdin); print(next(u["password"] for u in data["users"] if u["prefix"]=="E2E_SUPERADMIN"))')"
  export E2E_ECONOMIST_USERNAME="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; data=json.load(sys.stdin); print(next(u["username"] for u in data["users"] if u["prefix"]=="E2E_ECONOMIST"))')"
  export E2E_ECONOMIST_PASSWORD="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; data=json.load(sys.stdin); print(next(u["password"] for u in data["users"] if u["prefix"]=="E2E_ECONOMIST"))')"
  export E2E_CONTRACTOR_USERNAME="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; data=json.load(sys.stdin); print(next(u["username"] for u in data["users"] if u["prefix"]=="E2E_CONTRACTOR"))')"
  export E2E_CONTRACTOR_PASSWORD="$(printf '%s' "$provision_json" | "$PYTHON_CMD" -c 'import json,sys; data=json.load(sys.stdin); print(next(u["password"] for u in data["users"] if u["prefix"]=="E2E_CONTRACTOR"))')"
  export E2E_STRICT_CREDENTIALS=true
  trap cleanup_provisioned_users EXIT
fi

CMD=(npm --prefix web exec -- playwright test --config web/playwright.config.ts --grep @smoke)
if [[ "${HEADED:-false}" == "true" || "${HEADED:-0}" == "1" ]]; then
  CMD+=(--headed)
fi

"${CMD[@]}"
