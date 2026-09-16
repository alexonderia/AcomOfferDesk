#!/usr/bin/env bash
# TLS-секреты для оверлея acom (postgres-tls, rabbitmq-tls, minio-tls).
# Самоподписанный CA -> серверные сертификаты c SAN под SVC-DNS namespace acom.
# Значения никуда не печатаются: только имена файлов/секретов и exit-коды.
set -euo pipefail
NS=acom
DIR=$(mktemp -d); chmod 700 "$DIR"
trap "rm -rf $DIR" EXIT
gen_ca() {
  openssl req -x509 -newkey rsa:2048 -nodes -days 1825 -subj "/CN=acom-ca" \
    -keyout "$DIR/ca.key" -out "$DIR/ca.crt" >/dev/null 2>&1
}
gen_cert() { # name cn sans...
  local name=$1 cn=$2; shift 2
  local san=""; for d in "$@"; do san="$san,DNS:$d"; done; san=${san#,}
  openssl req -newkey rsa:2048 -nodes -subj "/CN=$cn" \
    -keyout "$DIR/$name.key" -out "$DIR/$name.csr" >/dev/null 2>&1
  openssl x509 -req -in "$DIR/$name.csr" -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" \
    -CAcreateserial -days 825 -out "$DIR/$name.crt" \
    -extfile <(printf "subjectAltName=%s\nextendedKeyUsage=serverAuth" "$san") >/dev/null 2>&1
}
gen_client() { # name cn
  local name=$1 cn=$2
  openssl req -newkey rsa:2048 -nodes -subj "/CN=$cn" \
    -keyout "$DIR/$name.key" -out "$DIR/$name.csr" >/dev/null 2>&1
  openssl x509 -req -in "$DIR/$name.csr" -CA "$DIR/ca.crt" -CAkey "$DIR/ca.key" \
    -CAcreateserial -days 825 -out "$DIR/$name.crt" \
    -extfile <(printf "extendedKeyUsage=clientAuth") >/dev/null 2>&1
}
gen_ca
# postgres: Service postgres + alias order-db
gen_cert pg "postgres.acom.svc.cluster.local" postgres.acom.svc.cluster.local order-db.acom.svc.cluster.local localhost
# rabbitmq
gen_cert rmq "rabbitmq.acom.svc.cluster.local" rabbitmq.acom.svc.cluster.local localhost
gen_client rmq-client "acom-app"
# minio
gen_cert minio "minio.acom.svc.cluster.local" minio.acom.svc.cluster.local localhost
kubectl -n $NS create secret generic postgres-tls \
  --from-file=ca.crt="$DIR/ca.crt" --from-file=server.crt="$DIR/pg.crt" --from-file=server.key="$DIR/pg.key" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl -n $NS create secret generic rabbitmq-tls \
  --from-file=ca.crt="$DIR/ca.crt" --from-file=server.crt="$DIR/rmq.crt" --from-file=server.key="$DIR/rmq.key" \
  --from-file=client.crt="$DIR/rmq-client.crt" --from-file=client.key="$DIR/rmq-client.key" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl -n $NS create secret generic minio-tls \
  --from-file=ca.crt="$DIR/ca.crt" --from-file=public.crt="$DIR/minio.crt" --from-file=private.key="$DIR/minio.key" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
echo "TLS_SECRETS_OK postgres-tls rabbitmq-tls minio-tls"
