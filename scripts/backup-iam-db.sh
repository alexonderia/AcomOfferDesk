#!/usr/bin/env bash
set -Eeuo pipefail

: "${PGHOST:?Set PGHOST for the IAM PostgreSQL server}"
: "${PGPORT:?Set PGPORT for the IAM PostgreSQL server}"
: "${PGDATABASE:?Set PGDATABASE to the IAM database name}"
: "${PGUSER:?Set PGUSER to the IAM database user}"

command -v pg_dump >/dev/null 2>&1 || {
  echo "pg_dump is required" >&2
  exit 127
}

backup_dir="${IAM_BACKUP_DIR:-./backups/iam}"
timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
backup_file="${backup_dir}/iam-${timestamp}.dump"

umask 077
mkdir -p "${backup_dir}"
pg_dump \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-acl \
  --file="${backup_file}"

printf '%s\n' "${backup_file}"
