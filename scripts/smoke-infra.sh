#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-${ENV_FILE:-.env.dev}}"
BASE_URL="${BASE_URL:-}"
SMOKE_DATABASE_URL="${SMOKE_DATABASE_URL:-}"
SMOKE_S3_ENDPOINT="${SMOKE_S3_ENDPOINT:-}"
SMOKE_RABBITMQ_URL="${SMOKE_RABBITMQ_URL:-}"

export PYTHONPATH="$ROOT_DIR/backend"
PYTHON_CMD="python"
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_CMD="$ROOT_DIR/.venv/bin/python"
fi

CMD=("$PYTHON_CMD" -m app.scripts.smoke_services --env-file "$ENV_FILE")
if [[ -n "$BASE_URL" ]]; then
  CMD+=(--base-url "$BASE_URL")
fi
if [[ -n "$SMOKE_DATABASE_URL" ]]; then
  CMD+=(--database-url "$SMOKE_DATABASE_URL")
fi
if [[ -n "$SMOKE_S3_ENDPOINT" ]]; then
  CMD+=(--s3-endpoint "$SMOKE_S3_ENDPOINT")
fi
if [[ -n "$SMOKE_RABBITMQ_URL" ]]; then
  CMD+=(--rabbitmq-url "$SMOKE_RABBITMQ_URL")
fi

"${CMD[@]}"
