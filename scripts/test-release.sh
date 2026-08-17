#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.dev}"
BASE_URL="${BASE_URL:-}"
INCLUDE_E2E="${INCLUDE_E2E:-false}"
STRICT_E2E="${STRICT_E2E:-false}"
REPAIR_IAM_RBAC="${REPAIR_IAM_RBAC:-true}"

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

echo "== [4/8] IAM RBAC and account reconciliation checks =="
if [[ "$REPAIR_IAM_RBAC" == "true" || "$REPAIR_IAM_RBAC" == "1" ]]; then
  IAM_RBAC_REPAIR=1 bash "$ROOT_DIR/scripts/check-iam.sh" "$ENV_FILE"
else
  bash "$ROOT_DIR/scripts/check-iam.sh" "$ENV_FILE"
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
  env "${e2e_env[@]}" "$ROOT_DIR/scripts/e2e-smoke.sh"
else
  echo "== [8/8] e2e smoke skipped (set INCLUDE_E2E=true to enable) =="
fi

echo "Release checks completed"
