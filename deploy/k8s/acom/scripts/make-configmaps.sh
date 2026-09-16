#!/usr/bin/env bash
# Собирает ConfigMap flyway-sql из SQL-миграций, приехавших с текущим чекаутом.
# Источник: deploy/order_database/flyway/sql/V*.sql (тот же SHA, что и образы).
# Идемпотентно: dry-run=client + apply (паттерн apply-secrets.sh).
# Запускать ДО `kubectl apply -k`: Job flyway-migrate монтирует этот ConfigMap.
set -euo pipefail

NS="${NS:-acom}"
KUBECTL="${KUBECTL:-kubectl}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_DIR="${SQL_DIR:-${SCRIPT_DIR}/../../order_database/flyway/sql}"

if [ ! -d "${SQL_DIR}" ]; then
  echo "FAIL: нет каталога миграций ${SQL_DIR}" >&2
  exit 1
fi

set -- "${SQL_DIR}"/V*.sql
if [ ! -e "$1" ]; then
  echo "FAIL: нет V*.sql в ${SQL_DIR}" >&2
  exit 1
fi

echo "flyway-sql <- ${SQL_DIR}:"
ls -1 "${SQL_DIR}"/V*.sql

"${KUBECTL}" -n "${NS}" create configmap flyway-sql \
  --from-file="${SQL_DIR}" \
  --dry-run=client -o yaml | "${KUBECTL}" apply -f -

echo "MAKE_CONFIGMAPS_OK flyway-sql"
