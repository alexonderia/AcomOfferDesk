#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.prod-like.example}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml docker-compose.prod.yml}"

compose_args=()
for f in $COMPOSE_FILES; do
  compose_args+=(-f "$f")
done

tmp_cfg="$(mktemp)"
trap 'rm -f "$tmp_cfg"' EXIT

echo "Rendering compose config..."
docker compose --env-file "$ENV_FILE" "${compose_args[@]}" config > "$tmp_cfg"

fail=0
warn=0

for forbidden in "8000:" "5672:" "15672:" "9000:" "9001:" "5432:" "5050:"; do
  if rg -n "$forbidden" "$tmp_cfg" >/dev/null; then
    echo "FAIL: forbidden published host port found in rendered config: $forbidden"
    fail=1
  fi
done

if rg -n "start-dev" "$tmp_cfg" >/dev/null; then
  echo "WARN: start-dev detected in rendered config."
  warn=1
fi

for sample in ".env.prod-like.example" ".env.example" ".env.dev.example"; do
  if [[ -f "$sample" ]]; then
    if rg -n "guest:guest|RABBITMQ_DEFAULT_USER=guest|RABBITMQ_DEFAULT_PASS=guest|minioadmin|minioadmin/minioadmin|dev-secret|start-dev" "$sample" >/dev/null; then
      echo "WARN: insecure/dev defaults detected in $sample"
      warn=1
    fi
    if rg -n "^CHANGE_ME" "$sample" >/dev/null; then
      echo "WARN: CHANGE_ME placeholders exist in $sample (expected for example files, replace in real env files)."
      warn=1
    fi
  fi
done

if [[ $fail -eq 1 ]]; then
  echo "Perimeter check: FAILED"
  exit 1
fi

if [[ $warn -eq 1 ]]; then
  echo "Perimeter check: PASSED with warnings"
  exit 0
fi

echo "Perimeter check: PASSED"
