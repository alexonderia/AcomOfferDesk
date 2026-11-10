#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "$0")" && pwd)"
ORDER_DB_DIR="${ORDER_DB_DIR:-/opt/order_database}"
DATA_SQL="${DATA_SQL:-$BUNDLE_DIR/order_database_data.sql}"
FULL_DUMP="${FULL_DUMP:-$BUNDLE_DIR/order_database_full.dump}"
KEYCLOAK_USERS_JSON="${KEYCLOAK_USERS_JSON:-$BUNDLE_DIR/keycloak_users.json}"

usage() {
  cat <<'USAGE'
Usage:
  ./restore_migration_bundle.sh db-sql
  ./restore_migration_bundle.sh db-dump
  ./restore_migration_bundle.sh verify

Commands:
  db-sql   Restore order_database from order_database_data.sql (schema must already exist)
  db-dump  Restore full PostgreSQL dump (schema+data)
  verify   Print row counts and bundle checksums

Notes:
  - Run on VPS host with docker compose access to /opt/order_database.
  - keycloak_users.json is preserved for manual import/filtering stage.
USAGE
}

require_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Required file not found: $file" >&2
    exit 1
  fi
}

restore_db_sql() {
  require_file "$DATA_SQL"
  cd "$ORDER_DB_DIR"
  local tables
  tables=$(docker compose exec -T postgres psql -U order_admin -d order_database -At -c "SELECT string_agg(format('%I', tablename), ',') FROM pg_tables WHERE schemaname='public' AND tablename NOT IN ('roles','flyway_schema_history');")
  if [[ -n "$tables" ]]; then
    docker compose exec -T postgres psql -U order_admin -d order_database -c "TRUNCATE TABLE $tables RESTART IDENTITY CASCADE;"
  fi

  {
    echo "SET session_replication_role = replica;"
    cat "$DATA_SQL"
    echo "SET session_replication_role = origin;"
  } | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U order_admin -d order_database

  echo "DB restore from data SQL completed."
}

restore_db_dump() {
  require_file "$FULL_DUMP"
  cd "$ORDER_DB_DIR"
  docker compose exec -T postgres dropdb -U order_admin --if-exists order_database
  docker compose exec -T postgres createdb -U order_admin order_database
  docker compose exec -T postgres pg_restore -U order_admin -d order_database --no-owner --no-privileges < "$FULL_DUMP"
  echo "DB restore from full dump completed."
}

verify_bundle() {
  cd "$BUNDLE_DIR"
  if [[ -f "$BUNDLE_DIR/SHA256SUMS.txt" ]]; then
    sha256sum -c "$BUNDLE_DIR/SHA256SUMS.txt" || true
  fi
  cd "$ORDER_DB_DIR"
  docker compose exec -T postgres psql -U order_admin -d order_database -At -c "SELECT 'users',count(*) FROM users UNION ALL SELECT 'requests',count(*) FROM requests UNION ALL SELECT 'offers',count(*) FROM offers UNION ALL SELECT 'economy_plans',count(*) FROM economy_plans UNION ALL SELECT 'user_auth_accounts',count(*) FROM user_auth_accounts UNION ALL SELECT 'roles',count(*) FROM roles;"
  echo "Keycloak snapshot file: $KEYCLOAK_USERS_JSON"
}

cmd="${1:-}"
case "$cmd" in
  db-sql)
    restore_db_sql
    ;;
  db-dump)
    restore_db_dump
    ;;
  verify)
    verify_bundle
    ;;
  *)
    usage
    exit 1
    ;;
esac
