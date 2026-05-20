#!/usr/bin/env bash
# Repair Keycloak permission model (atomic roles + app.* composite prune) then verify.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-${ENV_FILE:-.env.dev}}"
export KEYCLOAK_PERMISSION_REPAIR=1
exec "$ROOT_DIR/scripts/check-keycloak.sh" "$ENV_FILE"
