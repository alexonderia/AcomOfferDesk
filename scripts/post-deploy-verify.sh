#!/usr/bin/env bash
# Post-deploy gate on VPS: infrastructure smoke + Keycloak permission model (read-only).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-backend/.env}"
BASE_URL="${POST_DEPLOY_BASE_URL:-}"

if ! docker network inspect project_net >/dev/null 2>&1; then
  echo "POST_DEPLOY_VERIFY: Docker network project_net is missing" >&2
  exit 1
fi

if ! docker inspect --format '{{.State.Running}}' backend 2>/dev/null | grep -q true; then
  echo "POST_DEPLOY_VERIFY: backend container is not running" >&2
  exit 1
fi

SMOKE_BASE_URL="${BASE_URL}"
if [[ -z "$SMOKE_BASE_URL" ]]; then
  SMOKE_BASE_URL="$(grep -E '^(WEB_BASE_URL|PUBLIC_BACKEND_BASE_URL)=' "$COMPOSE_ENV_FILE" | head -n 1 | cut -d= -f2- | tr -d '\r' | sed -e 's/^["'\'']//' -e 's/["'\'']$//')"
fi
if [[ -z "$SMOKE_BASE_URL" ]]; then
  SMOKE_BASE_URL="http://127.0.0.1:8080"
fi

echo "=== post-deploy: smoke + Keycloak checks (single backend exec) ==="

docker compose --env-file "$COMPOSE_ENV_FILE" exec -T \
  -e POST_DEPLOY_BASE_URL="$SMOKE_BASE_URL" \
  -e KEYCLOAK_INTERNAL_BASE_URL="${KEYCLOAK_INTERNAL_BASE_URL:-http://keycloak:8080/iam}" \
  -e SMOKE_HTTP_TIMEOUT_SECONDS=8 \
  -e SMOKE_HTTP_RETRIES=1 \
  -e SMOKE_SKIP_RABBITMQ=true \
  -e SMOKE_S3_ENDPOINT=minio:9000 \
  -e SMOKE_MINIO_TIMEOUT_SECONDS=8 \
  -e PYTHONUNBUFFERED=1 \
  backend \
  python - <<'PY'
import os
import subprocess
import sys

env_path = "/app/post-deploy-verify.env"
skip_keys = {"PATH", "HOSTNAME", "HOME", "TERM", "SHLVL", "PWD", "PYTHONPATH"}

with open(env_path, "w", encoding="utf-8") as handle:
    for key, value in sorted(os.environ.items()):
        if key in skip_keys or key.startswith("_"):
            continue
        if not key.isupper():
            continue
        handle.write(f"{key}={value.replace(chr(10), '')}\n")

base_url = os.environ.get("POST_DEPLOY_BASE_URL", "").strip()
smoke_cmd = [
    sys.executable,
    "-m",
    "app.scripts.smoke_services",
    "--env-file",
    env_path,
]
if base_url:
    smoke_cmd.extend(["--base-url", base_url])

print("=== smoke_services ===", flush=True)
result = subprocess.run(smoke_cmd, check=False)
if result.returncode != 0:
    raise SystemExit(result.returncode)

print("=== check_keycloak_permission_model ===", flush=True)
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "app.scripts.check_keycloak_permission_model",
        "--env-file",
        env_path,
    ],
    check=False,
)
try:
    os.remove(env_path)
except OSError:
    pass
raise SystemExit(result.returncode)
PY

echo "POST_DEPLOY_VERIFY: all checks passed"
