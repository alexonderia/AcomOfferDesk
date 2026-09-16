#!/usr/bin/env bash
# Секреты namespace acom из /opt/acome-offer-desk/.env (прод) с перепривязкой адресов.
# ЗНАЧЕНИЯ НЕ ПЕЧАТАЮТСЯ. Временные файлы 0600, удаляются trap-ом.
set -euo pipefail
NS=acom
ENV=/opt/acome-offer-desk/.env
DIR=$(mktemp -d); chmod 700 "$DIR"
trap 'rm -rf "$DIR"' EXIT
export KUBECONFIG=${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}

# --- 1) acom-db-secret: POSTGRES_* + SUPERADMIN_PASSWORD
grep -E "^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|SUPERADMIN_PASSWORD)=" "$ENV" > "$DIR/db.env"
kubectl -n $NS create secret generic acom-db-secret --from-env-file="$DIR/db.env" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK acom-db-secret ($(wc -l < "$DIR/db.env") keys)"

# --- 2) acom-app-secrets: фильтр ключей + перепривязка адресов
ALLOWED="APP_ENV AUTH_ENABLE_LEGACY_PASSWORD_LOGIN JWT_ALGORITHM JWT_EXP_MINUTES JWT_SECRET EMAIL_ADDRESS EMAIL_APP_PASSWORD EMAIL_FROM_NAME EMAIL_REPLY_SECRET EMAIL_REPLY_TTL_SECONDS EMAIL_VERIFICATION_SECRET EMAIL_VERIFICATION_TTL_SECONDS IMAP_HOST IMAP_MAILBOX IMAP_PORT SMTP_HOST SMTP_PORT DATABASE_URL RABBITMQ_URL S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET S3_ENDPOINT S3_PUBLIC_ENDPOINT S3_PRESIGNED_GET_TTL_SECONDS S3_SECURE ADMIN_ROLE_ID CONTRACTOR_ROLE_ID ECONOMIST_ROLE_ID LEAD_ECONOMIST_ROLE_ID SUPERADMIN_ROLE_ID ALLOWED_CREATION_ROLE_IDS SUPERADMIN_PASSWORD REGISTRATION_NOTIFY_ENABLED REGISTRATION_NOTIFY_SERVICE REGISTRATION_NOTIFY_TIMEOUT_SECONDS REGISTRATION_NOTIFY_URL TG_BOT_PUBLIC_URL TG_COOKIE_NAME TG_COOKIE_TTL_SECONDS TG_LINK_SECRET TG_REGISTER_TTL_SECONDS TG_REQUEST_TTL_SECONDS WEB_BASE_URL PUBLIC_BACKEND_BASE_URL REQUEST_UPLOAD_DIR"
: > "$DIR/app.env"
for k in $ALLOWED; do
  v=$(grep -E "^${k}=" "$ENV" | tail -1 | cut -d= -f2-)
  if [ -z "$v" ]; then echo "MISSING_KEY $k" >&2; exit 3; fi
  printf "%s=%s\n" "$k" "$v" >> "$DIR/app.env"
done
# перепривязка адресов (только host/схема/порт, креды не трогаем)
sed -i \
  -e 's#order-database-postgres:5432#postgres.acom.svc.cluster.local:5432#' \
  -e 's#^DATABASE_URL=\(postgresql+asyncpg://[^?]*\)$#DATABASE_URL=\1?ssl=require#' \
  -e 's#amqp://\([^@]*\)@rabbitmq:5672/#amqps://\1@rabbitmq.acom.svc.cluster.local:5671/#' \
  -e 's#^S3_ENDPOINT=minio:9000$#S3_ENDPOINT=minio.acom.svc.cluster.local:9000#' \
  -e 's#^S3_SECURE=false$#S3_SECURE=true#' \
  "$DIR/app.env"
kubectl -n $NS create secret generic acom-app-secrets --from-env-file="$DIR/app.env" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK acom-app-secrets ($(wc -l < "$DIR/app.env") keys)"

# --- 3) rabbitmq-credentials: 05-credentials.conf из RABBITMQ_URL (user/pass)
RURL=$(grep -E "^RABBITMQ_URL=" "$ENV" | tail -1 | cut -d= -f2-)
RUSER=$(python3 -c "from urllib.parse import urlparse,unquote;u=urlparse('$RURL');print(unquote(u.username or ''))")
RPASS=$(python3 -c "from urllib.parse import urlparse,unquote;u=urlparse('$RURL');print(unquote(u.password or ''))")
printf 'default_user = %s\ndefault_pass = %s\n' "$RUSER" "$RPASS" > "$DIR/05-credentials.conf"; chmod 600 "$DIR/05-credentials.conf"
kubectl -n $NS create secret generic rabbitmq-credentials --from-file=05-credentials.conf="$DIR/05-credentials.conf" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "SECRET_OK rabbitmq-credentials"
echo "ALL_SECRETS_OK"
