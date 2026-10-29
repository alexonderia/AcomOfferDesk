#!/usr/bin/env bash
# Секреты namespace acom из /opt/acome-offer-desk/.env (прод) с перепривязкой адресов.
# IAM-секреты берутся из отдельного файла: generate-iam-secrets.sh (значения не печатаются).
# ЗНАЧЕНИЯ НЕ ПЕЧАТАЮТСЯ. Временные файлы 0600, удаляются trap-ом.
set -euo pipefail
NS=${NS:-acom}
ENV=${ENV:-/opt/acome-offer-desk/.env}
IAM_ENV=${IAM_ENV:-/opt/acome-iam/acom-iam.env}
DIR=$(mktemp -d); chmod 700 "$DIR"
trap 'rm -rf "$DIR"' EXIT
if [ -z "${KUBECONFIG:-}" ] && [ -r /etc/rancher/k3s/k3s.yaml ]; then
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
fi

[ -r "$ENV" ] || { echo "ENV_NOT_READABLE $ENV" >&2; exit 2; }
[ -r "$IAM_ENV" ] || { echo "IAM_ENV_NOT_READABLE $IAM_ENV (создай generate-iam-secrets.sh)" >&2; exit 2; }
kubectl get namespace "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

# --- 1) acom-db-secret: POSTGRES_* + SUPERADMIN_PASSWORD
grep -E "^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|SUPERADMIN_PASSWORD)=" "$ENV" > "$DIR/db.env"
kubectl -n $NS create secret generic acom-db-secret --from-env-file="$DIR/db.env" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK acom-db-secret ($(wc -l < "$DIR/db.env") keys)"

# --- 1b) acom-minio-secret: root-учётка MinIO.
# В прод-.env отдельных MINIO_ROOT_* нет: MinIO и приложение используют одни
# и те же S3_ACCESS_KEY/S3_SECRET_KEY. Иначе приложение не прочитает объекты.
MUSER=$(grep -E '^S3_ACCESS_KEY=' "$ENV" | tail -1 | cut -d= -f2-)
MPASS=$(grep -E '^S3_SECRET_KEY=' "$ENV" | tail -1 | cut -d= -f2-)
if [ -z "$MUSER" ] || [ -z "$MPASS" ]; then
  echo "MISSING_KEY S3_ACCESS_KEY/S3_SECRET_KEY in $ENV" >&2
  exit 3
fi
printf 'MINIO_ROOT_USER=%s\nMINIO_ROOT_PASSWORD=%s\n' "$MUSER" "$MPASS" > "$DIR/minio.env"
kubectl -n $NS create secret generic acom-minio-secret --from-env-file="$DIR/minio.env" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK acom-minio-secret"

# --- 2) acom-app-secrets: фильтр ключей + перепривязка адресов
ALLOWED="APP_ENV AUTH_ENABLE_LEGACY_PASSWORD_LOGIN JWT_ALGORITHM JWT_EXP_MINUTES JWT_SECRET EMAIL_ADDRESS EMAIL_APP_PASSWORD EMAIL_FROM_NAME EMAIL_REPLY_SECRET EMAIL_REPLY_TTL_SECONDS EMAIL_VERIFICATION_SECRET EMAIL_VERIFICATION_TTL_SECONDS IMAP_HOST IMAP_MAILBOX IMAP_PORT SMTP_HOST SMTP_PORT DATABASE_URL RABBITMQ_URL S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET S3_ENDPOINT S3_PUBLIC_ENDPOINT S3_PRESIGNED_GET_TTL_SECONDS S3_SECURE ADMIN_ROLE_ID CONTRACTOR_ROLE_ID ECONOMIST_ROLE_ID LEAD_ECONOMIST_ROLE_ID SUPERADMIN_ROLE_ID ALLOWED_CREATION_ROLE_IDS SUPERADMIN_PASSWORD REGISTRATION_NOTIFY_ENABLED REGISTRATION_NOTIFY_SERVICE REGISTRATION_NOTIFY_TIMEOUT_SECONDS REGISTRATION_NOTIFY_URL TG_BOT_PUBLIC_URL TG_COOKIE_NAME TG_COOKIE_TTL_SECONDS TG_LINK_SECRET TG_REGISTER_TTL_SECONDS TG_REQUEST_TTL_SECONDS WEB_BASE_URL PUBLIC_BACKEND_BASE_URL REQUEST_UPLOAD_DIR"
# Эти ключи могут быть пустыми: приложение само подставляет None/дефолт.
OPTIONAL_EMPTY="S3_PUBLIC_ENDPOINT IMAP_HOST"
: > "$DIR/app.env"
for k in $ALLOWED; do
  v=$(grep -E "^${k}=" "$ENV" | tail -1 | cut -d= -f2-)
  if [ -z "$v" ] && ! echo " $OPTIONAL_EMPTY " | grep -q " $k "; then
    echo "MISSING_KEY $k" >&2
    exit 3
  fi
  printf "%s=%s\n" "$k" "$v" >> "$DIR/app.env"
done

# NetworkPolicy allow-app-egress разрешает SMTP 25/443/587/993, но не 465.
# Принудительно используем 587 + STARTTLS, чтобы дефект не вернулся.
if grep -q '^SMTP_PORT=' "$DIR/app.env"; then
  sed -i 's/^SMTP_PORT=.*/SMTP_PORT=587/' "$DIR/app.env"
else
  printf 'SMTP_PORT=587\n' >> "$DIR/app.env"
fi
grep -q '^SMTP_PORT=587$' "$DIR/app.env" || { echo "SMTP_PORT_REWRITE_FAILED" >&2; exit 3; }
# перепривязка адресов (только host/схема/порт, креды не трогаем)
# asyncpg через SQLAlchemy не принимает sslmode/sslrootcert как kwargs.
# ssl=require шифрует; проверку CA делает post-deploy-verify через libpq.
sed -i \
  -e 's#order-database-postgres:5432#postgres.acom.svc.cluster.local:5432#' \
  -e 's#^DATABASE_URL=\(postgresql+asyncpg://[^?]*\)$#DATABASE_URL=\1?ssl=require#' \
  -e 's#amqp://\([^@]*\)@rabbitmq:5672/#amqps://\1@rabbitmq.acom.svc.cluster.local:5671/#' \
  -e 's#^S3_ENDPOINT=minio:9000$#S3_ENDPOINT=minio.acom.svc.cluster.local:9000#' \
  -e 's#^S3_SECURE=false$#S3_SECURE=true#' \
  "$DIR/app.env"

# Guardrails: если прод-URL был не в ожидаемом формате, sed мог не сработать.
grep -q '^DATABASE_URL=postgresql+asyncpg://.*@postgres\.acom\.svc\.cluster\.local:5432/.*ssl=require' "$DIR/app.env" \
  || { echo "DATABASE_URL_REWRITE_FAILED" >&2; exit 3; }
grep -q '^RABBITMQ_URL=amqps://.*@rabbitmq\.acom\.svc\.cluster\.local:5671/' "$DIR/app.env" \
  || { echo "RABBITMQ_URL_REWRITE_FAILED" >&2; exit 3; }
grep -q '^S3_ENDPOINT=minio\.acom\.svc\.cluster\.local:9000$' "$DIR/app.env" \
  || { echo "S3_ENDPOINT_REWRITE_FAILED" >&2; exit 3; }
grep -q '^S3_SECURE=true$' "$DIR/app.env" \
  || { echo "S3_SECURE_REWRITE_FAILED" >&2; exit 3; }

# --- 2b) публичная половина IAM для приложения.
# backend в production требует IAM_SIGNING_PUBLIC_KEY (или verification keys)
# и непустой IAM_INTERNAL_SERVICE_TOKEN; приватный ключ сюда не попадает.
for k in IAM_INTERNAL_SERVICE_TOKEN IAM_SIGNING_PUBLIC_KEY IAM_SIGNING_KID IAM_SIGNING_VERIFICATION_KEYS; do
  v=$(grep -E "^${k}=" "$IAM_ENV" | tail -1 | cut -d= -f2- || true)
  if [ -z "$v" ]; then echo "MISSING_KEY $k in $IAM_ENV" >&2; exit 3; fi
  printf "%s=%s\n" "$k" "$v" >> "$DIR/app.env"
done

kubectl -n $NS create secret generic acom-app-secrets --from-env-file="$DIR/app.env" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK acom-app-secrets ($(wc -l < "$DIR/app.env") keys)"

# --- 3) acom-iam-secrets: только сервис iam (включая приватный ключ).
grep -E '^(IAM_DATABASE_URL|IAM_INTERNAL_SERVICE_TOKEN|IAM_AUTH_REQUEST_SECRET|IAM_TOKEN_HASH_SECRET|IAM_SIGNING_PRIVATE_KEY|IAM_SIGNING_PUBLIC_KEY)=' "$IAM_ENV" > "$DIR/iam.env"
for k in IAM_DATABASE_URL IAM_INTERNAL_SERVICE_TOKEN IAM_AUTH_REQUEST_SECRET IAM_TOKEN_HASH_SECRET IAM_SIGNING_PRIVATE_KEY IAM_SIGNING_PUBLIC_KEY; do
  grep -q "^${k}=" "$DIR/iam.env" || { echo "MISSING_KEY $k in $IAM_ENV" >&2; exit 3; }
done
kubectl -n $NS create secret generic acom-iam-secrets --from-env-file="$DIR/iam.env" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK acom-iam-secrets ($(wc -l < "$DIR/iam.env") keys)"

# --- 4) rabbitmq-credentials: 05-credentials.conf из RABBITMQ_URL (user/pass)
RURL=$(grep -E "^RABBITMQ_URL=" "$ENV" | tail -1 | cut -d= -f2-)
RUSER=$(RURL="$RURL" python3 -c 'import os; from urllib.parse import urlparse,unquote; u=urlparse(os.environ["RURL"]); print(unquote(u.username or ""))')
RPASS=$(RURL="$RURL" python3 -c 'import os; from urllib.parse import urlparse,unquote; u=urlparse(os.environ["RURL"]); print(unquote(u.password or ""))')
if [ -z "$RUSER" ] || [ -z "$RPASS" ]; then
  echo "RABBITMQ_CREDENTIALS_EMPTY" >&2
  exit 3
fi
printf 'default_user = %s\ndefault_pass = %s\n' "$RUSER" "$RPASS" > "$DIR/05-credentials.conf"; chmod 600 "$DIR/05-credentials.conf"
kubectl -n $NS create secret generic rabbitmq-credentials --from-file=05-credentials.conf="$DIR/05-credentials.conf" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK rabbitmq-credentials"
echo "ALL_SECRETS_OK"
