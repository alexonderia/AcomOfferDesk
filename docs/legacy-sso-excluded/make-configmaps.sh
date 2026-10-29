#!/usr/bin/env bash
# Собирает ConfigMap'ы для Keycloak-пода из прод-каталогов на VPS.
# Нужны ДО `kubectl apply -k`: в workloads/keycloak.yaml том realm-import объявлен
# с `optional: false` — без ConfigMap под не стартует.
#
# Источники (прод-compose монтирует их как bind-тома):
#   /opt/acome-offer-desk/infra/keycloak/realm-import/*.json → keycloak-realm-import
#   /opt/acome-offer-desk/infra/keycloak/themes/**           → keycloak-theme
#   prepare-theme.sh, apply-realm-smtp.sh                    → keycloak-bootstrap-scripts
#
# Значения секретов не читаются и не печатаются. Запуск: на VPS, под root.
set -euo pipefail

NS="${NS:-acom}"
SRC="${SRC:-/opt/acome-offer-desk/infra/keycloak}"
KUBECTL="${KUBECTL:-kubectl}"

[ -d "$SRC/realm-import" ] || { echo "нет каталога $SRC/realm-import" >&2; exit 1; }

echo "1/3 keycloak-realm-import  <- $SRC/realm-import"
"$KUBECTL" -n "$NS" create configmap keycloak-realm-import \
  --from-file="$SRC/realm-import" \
  --dry-run=client -o yaml | "$KUBECTL" apply -f -

echo "2/3 keycloak-theme         <- $SRC/themes"
"$KUBECTL" -n "$NS" create configmap keycloak-theme \
  --from-file="$SRC/themes" \
  --dry-run=client -o yaml | "$KUBECTL" apply -f -

echo "3/3 keycloak-bootstrap-scripts <- prepare-theme.sh + apply-realm-smtp.sh"
"$KUBECTL" -n "$NS" create configmap keycloak-bootstrap-scripts \
  --from-file=prepare-theme.sh="$SRC/prepare-theme.sh" \
  --from-file=apply-realm-smtp.sh="$SRC/apply-realm-smtp.sh" \
  --dry-run=client -o yaml | "$KUBECTL" apply -f -

echo "готово. проверка:"
"$KUBECTL" -n "$NS" get cm keycloak-realm-import keycloak-theme keycloak-bootstrap-scripts
