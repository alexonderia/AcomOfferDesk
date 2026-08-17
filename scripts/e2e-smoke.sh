#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.dev}"
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
      if (name != key) { next }
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

CMD=(npm --prefix web exec -- playwright test --config web/playwright.config.ts --grep @smoke)
if [[ "${HEADED:-false}" == "true" || "${HEADED:-0}" == "1" ]]; then
  CMD+=(--headed)
fi

"${CMD[@]}"
