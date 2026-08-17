#!/usr/bin/env bash
set -Eeuo pipefail

: "${PGHOST:?Set PGHOST for the target IAM PostgreSQL server}"
: "${PGPORT:?Set PGPORT for the target IAM PostgreSQL server}"
: "${PGDATABASE:?Set PGDATABASE to the empty target IAM database name}"
: "${PGUSER:?Set PGUSER to the target IAM database user}"

backup_file="${1:-${IAM_BACKUP_FILE:-}}"
if [[ -z "${backup_file}" || ! -r "${backup_file}" ]]; then
  echo "Usage: $0 <readable iam backup file>" >&2
  exit 2
fi

case "${backup_file}" in
  *.sql)
    command -v psql >/dev/null 2>&1 || {
      echo "psql is required for plain SQL backups" >&2
      exit 127
    }
    psql \
      --no-psqlrc \
      --set=ON_ERROR_STOP=1 \
      --file="${backup_file}"
    ;;
  *)
    command -v pg_restore >/dev/null 2>&1 || {
      echo "pg_restore is required" >&2
      exit 127
    }
    pg_restore \
      --dbname="${PGDATABASE}" \
      --exit-on-error \
      --no-owner \
      --no-acl \
      "${backup_file}"
    ;;
esac
