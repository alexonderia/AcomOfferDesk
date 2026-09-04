#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-${ENV_FILE:-.env.dev}}"
if [[ "${IAM_RBAC_REPAIR:-false}" == "true" || "${IAM_RBAC_REPAIR:-false}" == "1" ]]; then
  docker compose --env-file "$ENV_FILE" exec -T backend \
    python -m app.scripts.seed_iam_rbac
fi
docker compose --env-file "$ENV_FILE" exec -T backend \
  python -m app.scripts.seed_iam_rbac --report
docker compose --env-file "$ENV_FILE" exec -T backend \
  python -m app.scripts.reconcile_iam_accounts
