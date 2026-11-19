#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.dev}"
BASE_URL="${BASE_URL:-}"
INCLUDE_E2E="${INCLUDE_E2E:-false}"
STRICT_E2E="${STRICT_E2E:-false}"
REPAIR_IAM_RBAC="${REPAIR_IAM_RBAC:-false}"

echo "== [1/10] backend unit tests =="
"$ROOT_DIR/scripts/test-unit.sh"

echo "== [2/10] backend integration/API contract tests =="
"$ROOT_DIR/scripts/test-integration.sh"

echo "== [3/10] IAM tests =="
bash "$ROOT_DIR/scripts/test-iam.sh"

echo "== [4/10] file guard tests =="
bash "$ROOT_DIR/scripts/test-file-guard.sh"

echo "== [5/10] infrastructure smoke checks =="
if [[ -n "$BASE_URL" ]]; then
  BASE_URL="$BASE_URL" "$ROOT_DIR/scripts/smoke-infra.sh" "$ENV_FILE"
else
  "$ROOT_DIR/scripts/smoke-infra.sh" "$ENV_FILE"
fi

echo "== [6/10] IAM RBAC and account reconciliation checks =="
if [[ "$REPAIR_IAM_RBAC" == "true" || "$REPAIR_IAM_RBAC" == "1" ]]; then
  IAM_RBAC_REPAIR=1 bash "$ROOT_DIR/scripts/check-iam.sh" "$ENV_FILE"
else
  IAM_RBAC_REPAIR=0 bash "$ROOT_DIR/scripts/check-iam.sh" "$ENV_FILE"
fi

echo "== [7/10] frontend lint =="
npm --prefix web run lint

echo "== [8/10] frontend unit/component tests =="
npm --prefix web run test:unit

echo "== [9/10] frontend typecheck/build =="
npm --prefix web run build

if [[ "$INCLUDE_E2E" == "true" || "$INCLUDE_E2E" == "1" ]]; then
  echo "== [10/10] e2e smoke =="
  e2e_env=(ENV_FILE="$ENV_FILE" BASE_URL="$BASE_URL")
  if [[ "$STRICT_E2E" == "true" || "$STRICT_E2E" == "1" ]]; then
    e2e_env+=(STRICT_CREDENTIALS=true)
  fi
  env "${e2e_env[@]}" "$ROOT_DIR/scripts/e2e-smoke.sh"
else
  echo "== [10/10] e2e smoke skipped (set INCLUDE_E2E=true to enable); deployment readiness requires stand verification =="
fi

echo "Release checks completed"
