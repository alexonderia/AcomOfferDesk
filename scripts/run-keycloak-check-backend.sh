#!/usr/bin/env bash
# Run check_keycloak_permission_model inside the running backend container (VPS/deploy).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-backend/.env}"
REPAIR="${KEYCLOAK_PERMISSION_REPAIR:-false}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repair)
      REPAIR=true
      shift
      ;;
    --env-file)
      COMPOSE_ENV_FILE="${2:?}"
      shift 2
      ;;
    *)
      COMPOSE_ENV_FILE="$1"
      shift
      ;;
  esac
done

if ! docker inspect --format '{{.State.Running}}' backend 2>/dev/null | grep -q true; then
  echo "KEYCLOAK_CHECK: backend container is not running" >&2
  exit 1
fi

REPAIR_FLAG=""
if [ "$REPAIR" = "true" ] || [ "$REPAIR" = "1" ]; then
  REPAIR_FLAG="--repair"
fi

docker compose --env-file "$COMPOSE_ENV_FILE" exec -T \
  -e KEYCLOAK_INTERNAL_BASE_URL="${KEYCLOAK_INTERNAL_BASE_URL:-http://keycloak:8080/iam}" \
  -e PYTHONUNBUFFERED=1 \
  backend \
  python - <<PY
import os
import subprocess
import sys

env_path = "/app/keycloak-check.env"
skip_keys = {"PATH", "HOSTNAME", "HOME", "TERM", "SHLVL", "PWD", "PYTHONPATH"}

with open(env_path, "w", encoding="utf-8") as handle:
    for key, value in sorted(os.environ.items()):
        if key in skip_keys or key.startswith("_"):
            continue
        if not key.isupper():
            continue
        handle.write(f"{key}={value.replace(chr(10), '')}\n")

cmd = [
    sys.executable,
    "-m",
    "app.scripts.check_keycloak_permission_model",
    "--env-file",
    env_path,
]
repair = "${REPAIR_FLAG}"
if repair:
    cmd.append(repair)

result = subprocess.run(cmd, check=False)
try:
    os.remove(env_path)
except OSError:
    pass
raise SystemExit(result.returncode)
PY
