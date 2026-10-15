#!/usr/bin/env bash
# Pre-merge checks before promoting dev → test (deploy branch).
# Run from repo root on a dev checkout that is candidate for merging into test.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "PROMOTION_CHECK: FAIL: $*" >&2
  exit 1
}

ok() {
  echo "PROMOTION_CHECK: OK: $*"
}

if [ ! -f docker-compose.yml ]; then
  fail "docker-compose.yml not found (run from repository root)"
fi

PYTHON_CMD="python3"
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_CMD="$ROOT_DIR/.venv/bin/python"
fi

export PYTHONPATH="$ROOT_DIR/backend"
export APP_ENV="${APP_ENV:-development}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://test:test@localhost:5432/test_db}"
export JWT_SECRET="${JWT_SECRET:-ci-test-jwt-secret}"
export EMAIL_ADDRESS="${EMAIL_ADDRESS:-ci@example.com}"
export EMAIL_APP_PASSWORD="${EMAIL_APP_PASSWORD:-ci-email-app-password}"
export SMTP_HOST="${SMTP_HOST:-smtp.example.com}"
export EMAIL_VERIFICATION_SECRET="${EMAIL_VERIFICATION_SECRET:-ci-email-verification-secret}"
export S3_ENDPOINT="${S3_ENDPOINT:-localhost:9000}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-ci-access-key}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-ci-secret-key}"
export S3_BUCKET="${S3_BUCKET:-ci-bucket}"

"$PYTHON_CMD" -m pytest \
  backend/tests/unit/test_iam_authentication_unit.py \
  backend/tests/unit/test_iam_migration_unit.py -q
ok "IAM authentication and migration contract tests passed"

if command -v docker >/dev/null 2>&1; then
  ENV_TEMPLATE=".env.prod-like.example"
  if [ -f "$ENV_TEMPLATE" ]; then
    export APP_RUNTIME_ENV_FILE="./$ENV_TEMPLATE"
    export IAM_RUNTIME_ENV_FILE="./.env.iam.example"
    export IAM_MIGRATION_ENV_FILE="./.env.iam-db.example"
    if docker compose -f docker-compose.yml -f docker-compose.prod.yml config >/dev/null 2>&1; then
      ok "docker compose config (prod stack) renders"
    else
      fail "docker compose config failed for prod stack (see error above)"
    fi
  else
    echo "PROMOTION_CHECK: SKIP: $ENV_TEMPLATE not found"
  fi
else
  echo "PROMOTION_CHECK: SKIP: docker not available for compose config check"
fi

echo "PROMOTION_CHECK: all checks passed"
