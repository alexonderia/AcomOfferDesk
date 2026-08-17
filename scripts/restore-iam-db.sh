#!/usr/bin/env bash
set -Eeuo pipefail

: "${PGHOST:?Set PGHOST for the target IAM PostgreSQL server}"
: "${PGPORT:?Set PGPORT for the target IAM PostgreSQL server}"
: "${PGDATABASE:?Set PGDATABASE to the empty target IAM database name}"
: "${PGUSER:?Set PGUSER to the target IAM database user}"
: "${IAM_RESTORE_CONFIRM_DATABASE:?Set IAM_RESTORE_CONFIRM_DATABASE to exactly match PGDATABASE}"

if [[ "${IAM_RESTORE_CONFIRM_DATABASE}" != "${PGDATABASE}" ]]; then
  echo "Restore aborted: IAM_RESTORE_CONFIRM_DATABASE must exactly match PGDATABASE (${PGDATABASE})." >&2
  exit 2
fi

backup_file="${1:-${IAM_BACKUP_FILE:-}}"
if [[ -z "${backup_file}" || ! -r "${backup_file}" ]]; then
  echo "Usage: $0 <readable iam backup file>" >&2
  exit 2
fi

command -v psql >/dev/null 2>&1 || {
  echo "psql is required to verify that the target IAM database is empty" >&2
  exit 127
}

target_table_count="$(
  psql \
    --no-psqlrc \
    --quiet \
    --tuples-only \
    --no-align \
    --set=ON_ERROR_STOP=1 \
    --command="
      SELECT count(*)
      FROM pg_catalog.pg_class AS relation
      JOIN pg_catalog.pg_namespace AS namespace
        ON namespace.oid = relation.relnamespace
      WHERE namespace.nspname = 'public'
        AND relation.relkind IN ('r', 'p');
    "
)"

if [[ ! "${target_table_count}" =~ ^[0-9]+$ ]]; then
  echo "Restore aborted: could not verify the target database table count." >&2
  exit 1
fi
if (( target_table_count != 0 )); then
  echo "Restore aborted: target database ${PGDATABASE} contains ${target_table_count} table(s) in public schema." >&2
  echo "Create a new empty database and retry; this script never drops existing objects." >&2
  exit 2
fi

case "${backup_file}" in
  *.sql)
    psql \
      --no-psqlrc \
      --set=ON_ERROR_STOP=1 \
      --single-transaction \
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
      --single-transaction \
      --no-owner \
      --no-acl \
      "${backup_file}"
    ;;
esac
