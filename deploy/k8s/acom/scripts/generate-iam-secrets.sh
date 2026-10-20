#!/usr/bin/env bash
# Генерация IAM-секретов для k8s-контура AcomOfferDesk.
#
# Что делает:
#   * создаёт пару RSA-ключей для подписи IAM-токенов;
#   * генерирует три независимых случайных секрета (>= 32 символов);
#   * собирает IAM_DATABASE_URL для отдельной БД acom_iam;
#   * пишет файлы в каталог 0700, сами файлы 0600;
#   * по флагу --apply создаёт/обновляет Secret acom-iam-secrets.
#
# Значения НЕ печатаются. Приватный ключ получает только сервис iam.
#
# Пример:
#   bash deploy/k8s/acom/scripts/generate-iam-secrets.sh \
#     --db-env deploy/k8s/acom/.secrets/acom-db.env \
#     --out-dir deploy/k8s/acom/.secrets
#
# Требования: openssl, python3; для --apply — kubectl с доступом к namespace acom.
set -euo pipefail
umask 077

usage() {
  cat <<'EOF'
Usage: generate-iam-secrets.sh --db-env FILE [options]

  --db-env FILE     env-файл с POSTGRES_USER и POSTGRES_PASSWORD (обязательно)
  --out-dir DIR     каталог для результатов (default: deploy/k8s/acom/.secrets)
  --db-name NAME    имя БД IAM (default: acom_iam)
  --db-host HOST    хост Postgres (default: postgres.acom.svc.cluster.local)
  --db-port PORT    порт Postgres (default: 5432)
  --apply           создать/обновить Secret acom-iam-secrets через kubectl
  --force           перезаписать существующие файлы
  -h, --help        эта справка

Файлы на выходе:
  acom-iam.env      секреты сервиса iam (включая приватный ключ)
  acom-app-iam.env  публичная часть для acom-app-secrets
  acom-iam-db.env   параметры Flyway для БД acom_iam

Значения не печатаются и не коммитятся.
EOF
}

OUT_DIR="deploy/k8s/acom/.secrets"
DB_ENV=""
DB_NAME="acom_iam"
DB_HOST="postgres.acom.svc.cluster.local"
DB_PORT="5432"
APPLY=0
FORCE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --db-env) DB_ENV="${2:-}"; shift 2 ;;
    --out-dir) OUT_DIR="${2:-}"; shift 2 ;;
    --db-name) DB_NAME="${2:-}"; shift 2 ;;
    --db-host) DB_HOST="${2:-}"; shift 2 ;;
    --db-port) DB_PORT="${2:-}"; shift 2 ;;
    --apply) APPLY=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "UNKNOWN_ARG $1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v openssl >/dev/null 2>&1 || { echo "MISSING openssl" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "MISSING python3" >&2; exit 2; }

if [ -z "$DB_ENV" ]; then
  echo "MISSING --db-env FILE (нужен POSTGRES_USER/POSTGRES_PASSWORD)" >&2
  exit 2
fi
if [ ! -r "$DB_ENV" ]; then
  echo "DB_ENV_NOT_READABLE $DB_ENV" >&2
  exit 2
fi

DB_USER=$(grep -E '^POSTGRES_USER=' "$DB_ENV" | tail -1 | cut -d= -f2- || true)
DB_PASS=$(grep -E '^POSTGRES_PASSWORD=' "$DB_ENV" | tail -1 | cut -d= -f2- || true)
if [ -z "$DB_USER" ]; then echo "MISSING_KEY POSTGRES_USER in $DB_ENV" >&2; exit 3; fi
if [ -z "$DB_PASS" ]; then echo "MISSING_KEY POSTGRES_PASSWORD in $DB_ENV" >&2; exit 3; fi

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

IAM_ENV="$OUT_DIR/acom-iam.env"
APP_IAM_ENV="$OUT_DIR/acom-app-iam.env"
IAM_DB_ENV="$OUT_DIR/acom-iam-db.env"

for f in "$IAM_ENV" "$APP_IAM_ENV" "$IAM_DB_ENV"; do
  if [ -e "$f" ] && [ "$FORCE" -ne 1 ]; then
    echo "REFUSE_OVERWRITE $f (use --force)" >&2
    exit 3
  fi
done

TMP=$(mktemp -d)
chmod 700 "$TMP"
trap 'rm -rf "$TMP"' EXIT

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
  -out "$TMP/private.pem" >/dev/null 2>&1
openssl pkey -in "$TMP/private.pem" -pubout \
  -out "$TMP/public.pem" >/dev/null 2>&1

openssl pkey -in "$TMP/private.pem" -noout >/dev/null 2>&1 || {
  echo "RSA_PRIVATE_INVALID" >&2; exit 4;
}
openssl pkey -pubin -in "$TMP/public.pem" -noout >/dev/null 2>&1 || {
  echo "RSA_PUBLIC_INVALID" >&2; exit 4;
}

escape_pem() {
  python3 - "$1" <<'PY'
import sys
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = fh.read().strip()
print(data.replace("\n", "\\n"))
PY
}
PRIVATE_ESC=$(escape_pem "$TMP/private.pem")
PUBLIC_ESC=$(escape_pem "$TMP/public.pem")

gen_token() {
  openssl rand -base64 48 | tr -d '\n'
}
INTERNAL_TOKEN=$(gen_token)
AUTH_REQUEST_SECRET=$(gen_token)
TOKEN_HASH_SECRET=$(gen_token)

for value in "$INTERNAL_TOKEN" "$AUTH_REQUEST_SECRET" "$TOKEN_HASH_SECRET"; do
  if [ "${#value}" -lt 32 ]; then
    echo "TOKEN_TOO_SHORT" >&2
    exit 4
  fi
done

ENC_USER=$(DB_USER="$DB_USER" python3 -c 'import os,urllib.parse; print(urllib.parse.quote(os.environ["DB_USER"], safe=""))')
ENC_PASS=$(DB_PASS="$DB_PASS" python3 -c 'import os,urllib.parse; print(urllib.parse.quote(os.environ["DB_PASS"], safe=""))')
# SQLAlchemy asyncpg передаёт query-параметры как kwargs в asyncpg.connect;
# sslmode/sslrootcert он не принимает. ssl=require шифрует соединение.
# Проверку CA делает post-deploy-verify через libpq (sslmode=verify-full).
DB_URL="postgresql+asyncpg://${ENC_USER}:${ENC_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}?ssl=require"
JDBC_URL="jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=verify-full&sslrootcert=/etc/ssl/postgres/ca.crt"

{
  printf 'IAM_DATABASE_URL=%s\n' "$DB_URL"
  printf 'IAM_INTERNAL_SERVICE_TOKEN=%s\n' "$INTERNAL_TOKEN"
  printf 'IAM_AUTH_REQUEST_SECRET=%s\n' "$AUTH_REQUEST_SECRET"
  printf 'IAM_TOKEN_HASH_SECRET=%s\n' "$TOKEN_HASH_SECRET"
  printf 'IAM_SIGNING_PRIVATE_KEY=%s\n' "$PRIVATE_ESC"
  printf 'IAM_SIGNING_PUBLIC_KEY=%s\n' "$PUBLIC_ESC"
  printf 'IAM_SIGNING_KID=iam-signing-1\n'
  printf 'IAM_SIGNING_VERIFICATION_KEYS={}\n'
} > "$IAM_ENV"
chmod 600 "$IAM_ENV"

{
  printf 'IAM_INTERNAL_SERVICE_TOKEN=%s\n' "$INTERNAL_TOKEN"
  printf 'IAM_SIGNING_PUBLIC_KEY=%s\n' "$PUBLIC_ESC"
  printf 'IAM_SIGNING_KID=iam-signing-1\n'
  printf 'IAM_SIGNING_VERIFICATION_KEYS={}\n'
} > "$APP_IAM_ENV"
chmod 600 "$APP_IAM_ENV"

{
  printf 'FLYWAY_URL=%s\n' "$JDBC_URL"
  printf 'FLYWAY_USER=%s\n' "$DB_USER"
  printf 'FLYWAY_PASSWORD=%s\n' "$DB_PASS"
  printf 'FLYWAY_CONNECT_RETRIES=30\n'
} > "$IAM_DB_ENV"
chmod 600 "$IAM_DB_ENV"

echo "IAM_SECRETS_OK"
echo "FILE $IAM_ENV keys=IAM_DATABASE_URL IAM_INTERNAL_SERVICE_TOKEN IAM_AUTH_REQUEST_SECRET IAM_TOKEN_HASH_SECRET IAM_SIGNING_PRIVATE_KEY IAM_SIGNING_PUBLIC_KEY"
echo "FILE $APP_IAM_ENV keys=IAM_INTERNAL_SERVICE_TOKEN IAM_SIGNING_PUBLIC_KEY IAM_SIGNING_KID IAM_SIGNING_VERIFICATION_KEYS"
echo "FILE $IAM_DB_ENV keys=FLYWAY_URL FLYWAY_USER FLYWAY_PASSWORD"
echo "MERGE $APP_IAM_ENV into acom-app-secrets (apply-secrets.sh делает это автоматически)"

if [ "$APPLY" -eq 1 ]; then
  command -v kubectl >/dev/null 2>&1 || { echo "MISSING kubectl" >&2; exit 5; }
  NS="${NS:-acom}"
  kubectl -n "$NS" create secret generic acom-iam-secrets \
    --from-env-file="$IAM_ENV" \
    --dry-run=client -o yaml | kubectl apply -f - >/dev/null
  echo "SECRET_APPLIED $NS/acom-iam-secrets"
fi
