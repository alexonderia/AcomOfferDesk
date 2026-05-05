#!/usr/bin/env bash
# Развёртывание PostgreSQL из alexonderia/order_database на VPS (Docker Compose).
# Документация: docs/order-database-vps.md
# Flyway: https://github.com/alexonderia/order_database/blob/main/docs/flyway.md
#
# Приватный репозиторий order_database: нужен GITHUB_TOKEN или GH_TOKEN (classic PAT, scope repo).
# Запуск на сервере от root:
#   export GITHUB_TOKEN=ghp_...
#   bash scripts/install-order-database-vps.sh
# С машины разработчика:
#   TOKEN=$(gh auth token)
#   scp scripts/install-order-database-vps.sh root@VPS:/root/
#   ssh root@VPS "export GITHUB_TOKEN='$TOKEN'; bash /root/install-order-database-vps.sh | tee /tmp/install-order-db.log"
#
set -euo pipefail

ORDER_DB_DIR="${ORDER_DB_DIR:-/opt/order_database}"
APP_DIR="${APP_DIR:-/opt/acome-offer-desk}"
ORDER_DB_TARBALL_URL="${ORDER_DB_TARBALL_URL:-https://github.com/alexonderia/order_database/archive/refs/heads/main.tar.gz}"
ORDER_DB_API_TARBALL="${ORDER_DB_API_TARBALL:-https://api.github.com/repos/alexonderia/order_database/tarball/main}"
PG_HOST_PORT="${PG_HOST_PORT:-5432}"

log() { echo "[$(date -Iseconds)] $*"; }

fail() { echo "INSTALL_FAILED: $*" >&2; exit 1; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || fail "нет команды: $1"; }

need_cmd docker
need_cmd curl
need_cmd tar
need_cmd openssl

if ! docker compose version >/dev/null 2>&1; then
  fail "нужен Docker Compose v2 (docker compose)"
fi

docker network inspect project_net >/dev/null 2>&1 || fail "сеть project_net не найдена: docker network create project_net"

parent="$(dirname "$ORDER_DB_DIR")"
mkdir -p "$parent"
tmpdir="$(mktemp -d)"
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

GH_TOKEN_USE="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [[ -n "$GH_TOKEN_USE" ]]; then
  log "скачивание приватного order_database через GitHub API (tarball main)"
  curl -fsSL \
    -H "Authorization: Bearer ${GH_TOKEN_USE}" \
    -H "Accept: application/vnd.github+json" \
    -L \
    -o "$tmpdir/order_database.tar.gz" \
    "$ORDER_DB_API_TARBALL"
else
  log "скачивание публичного tar.gz (без токена)"
  curl -fsSL "$ORDER_DB_TARBALL_URL" -o "$tmpdir/order_database.tar.gz" || {
    fail "нужен доступ к репо: задайте GITHUB_TOKEN или GH_TOKEN (classic PAT, scope repo), либо скопируйте каталог order_database вручную в $ORDER_DB_DIR"
  }
fi
rm -rf "$ORDER_DB_DIR"
tar -xzf "$tmpdir/order_database.tar.gz" -C "$tmpdir"
extracted="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | head -1)"
[[ -n "$extracted" ]] || fail "в архиве нет корневого каталога"
mv "$extracted" "$ORDER_DB_DIR"
if [[ -n "${GH_TOKEN_USE:-}" ]]; then
  log "источник: GitHub API tarball main -> $ORDER_DB_DIR"
else
  log "источник: $ORDER_DB_TARBALL_URL -> $ORDER_DB_DIR"
fi

POSTGRES_PASS="$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 28)"
SUPERADMIN_PASS="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 22)"

umask 077
printf '%s\n' "$POSTGRES_PASS" >/root/.acom_order_db_postgres_password
printf '%s\n' "$SUPERADMIN_PASS" >/root/.acom_order_db_superadmin_password
log "пароли записаны в /root/.acom_order_db_postgres_password и /root/.acom_order_db_superadmin_password"

cat >"$ORDER_DB_DIR/.env" <<EOF
POSTGRES_DB=order_database
POSTGRES_USER=order_admin
POSTGRES_PASSWORD=${POSTGRES_PASS}
PG_PORT=${PG_HOST_PORT}
PGADMIN_DEFAULT_EMAIL=admin@local.invalid
PGADMIN_DEFAULT_PASSWORD=unused
PGADMIN_PORT=5050
SUPERADMIN_PASSWORD=${SUPERADMIN_PASS}
EOF

cd "$ORDER_DB_DIR"

log "остановка старого стека и тома (init только на пустом data)"
docker compose down -v 2>/dev/null || true
docker rm -f order-database-postgres order-database-flyway order-database-pgadmin 2>/dev/null || true
docker volume rm -f order_database_pg_data 2>/dev/null || true

log "docker compose build postgres"
docker compose build postgres

log "docker compose up -d postgres"
docker compose up -d postgres

log "ожидание healthy postgres..."
for i in $(seq 1 120); do
  if docker compose ps postgres 2>/dev/null | grep -q healthy; then
    log "postgres healthy"
    break
  fi
  if [[ "$i" -eq 120 ]]; then
    docker compose logs postgres --tail 100
    fail "таймаут ожидания healthy"
  fi
  sleep 2
done

log "flyway validate + migrate"
docker compose --profile tools run --rm flyway validate
docker compose --profile tools run --rm flyway migrate

log "проверки SQL"
docker compose exec -T postgres psql -U order_admin -d order_database -v ON_ERROR_STOP=1 -c "SELECT count(*) AS roles_count FROM roles;"
docker compose exec -T postgres psql -U order_admin -d order_database -v ON_ERROR_STOP=1 -c "SELECT id, role FROM roles ORDER BY id;"
docker compose exec -T postgres psql -U order_admin -d order_database -v ON_ERROR_STOP=1 -c "SELECT id, id_role, status FROM users WHERE id = 'superadmin';"
docker compose exec -T postgres psql -U order_admin -d order_database -v ON_ERROR_STOP=1 -c "SELECT COUNT(*) AS flyway_rows FROM flyway_schema_history;"

if [[ -d "$APP_DIR" && -f "$APP_DIR/backend/.env" ]]; then
  log "обновление DATABASE_URL в $APP_DIR/backend/.env -> order-database-postgres:5432"
  if grep -q '^DATABASE_URL=' "$APP_DIR/backend/.env"; then
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://order_admin:${POSTGRES_PASS}@order-database-postgres:5432/order_database|" "$APP_DIR/backend/.env"
  else
    echo "DATABASE_URL=postgresql+asyncpg://order_admin:${POSTGRES_PASS}@order-database-postgres:5432/order_database" >>"$APP_DIR/backend/.env"
  fi
  log "пересоздание backend и notifications_worker"
  (cd "$APP_DIR" && docker compose up -d --force-recreate backend notifications_worker)
  log "пересоздание gateway — иначе nginx может держать старый IP backend → 502 на API"
  (cd "$APP_DIR" && docker compose up -d --force-recreate --no-deps gateway)
else
  log "нет $APP_DIR/backend/.env — пропуск привязки приложения"
fi

log "INSTALL_SUCCESS"
