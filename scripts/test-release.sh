#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.dev}"
BASE_URL="${BASE_URL:-}"
INCLUDE_E2E="${INCLUDE_E2E:-false}"
STRICT_E2E="${STRICT_E2E:-false}"
PROVISION_E2E_USERS="${PROVISION_E2E_USERS:-true}"
KEEP_PROVISIONED_E2E_USERS="${KEEP_PROVISIONED_E2E_USERS:-false}"
REPAIR_KEYCLOAK="${REPAIR_KEYCLOAK:-true}"

echo "== [1/8] backend unit tests =="
"$ROOT_DIR/scripts/test-unit.sh"

echo "== [2/8] backend integration/API contract tests =="
"$ROOT_DIR/scripts/test-integration.sh"

echo "== [3/8] infrastructure smoke checks =="
if [[ -n "$BASE_URL" ]]; then
  BASE_URL="$BASE_URL" "$ROOT_DIR/scripts/smoke-infra.sh" "$ENV_FILE"
else
  "$ROOT_DIR/scripts/smoke-infra.sh" "$ENV_FILE"
fi

echo "== [4/8] keycloak permission model checks =="
if [[ "$REPAIR_KEYCLOAK" == "true" || "$REPAIR_KEYCLOAK" == "1" ]]; then
  KEYCLOAK_PERMISSION_REPAIR=1 "$ROOT_DIR/scripts/check-keycloak.sh" "$ENV_FILE"
else
  "$ROOT_DIR/scripts/check-keycloak.sh" "$ENV_FILE"
fi

echo "== [5/8] frontend lint =="
npm --prefix web run lint

echo "== [6/8] frontend unit/component tests =="
npm --prefix web run test:unit

echo "== [7/8] frontend typecheck/build =="
npm --prefix web run build

if [[ "$INCLUDE_E2E" == "true" || "$INCLUDE_E2E" == "1" ]]; then
  echo "== [8/8] e2e smoke =="
  e2e_env=(ENV_FILE="$ENV_FILE" BASE_URL="$BASE_URL")
  if [[ "$STRICT_E2E" == "true" || "$STRICT_E2E" == "1" ]]; then
    e2e_env+=(STRICT_CREDENTIALS=true)
  fi
  if [[ "$PROVISION_E2E_USERS" == "true" || "$PROVISION_E2E_USERS" == "1" ]]; then
    e2e_env+=(PROVISION_USERS=true)
  fi
  if [[ "$KEEP_PROVISIONED_E2E_USERS" == "true" || "$KEEP_PROVISIONED_E2E_USERS" == "1" ]]; then
    e2e_env+=(KEEP_PROVISIONED_USERS=true)
  fi
  env "${e2e_env[@]}" "$ROOT_DIR/scripts/e2e-smoke.sh"
else
  echo "== [8/8] e2e smoke skipped (set INCLUDE_E2E=true to enable) =="
fi

echo "Release checks completed"
