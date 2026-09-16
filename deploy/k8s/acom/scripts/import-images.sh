#!/usr/bin/env bash
# Импорт образов AcomOfferDesk в containerd k3s на acom-vps.
#
# Зачем: у всех подов оверлея `imagePullPolicy: Never` (в проде RepoDigests пусты,
# registry отсутствует — решение D7 плана: в будущем CI → GHCR + imagePullSecret).
# Значит нужный тег ОБЯЗАН лежать в containerd, иначе под встанет с ErrImageNeverPull.
#
# По умолчанию скрипт только ПОКАЗЫВАЕТ команды. Ничего не делает без --apply.
# Вариант «перетегировать то, что уже крутится в проде» = точный паритет с текущим
# прод-стеком (новых сборок нет). Свежая сборка из репозитория — отдельная задача CI.
#
# Использование:
#   scripts/import-images.sh                 # dry: печатает план
#   scripts/import-images.sh --apply         # ретег + save + ctr images import
#   scripts/import-images.sh --apply --from-ghcr   # когда появится GHCR (D7)
set -euo pipefail

APPLY=0
FROM_GHCR=0
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --from-ghcr) FROM_GHCR=1 ;;
    *) echo "неизвестный аргумент: $a" >&2; exit 2 ;;
  esac
done

# манифест-тег  ←→  локальный прод-образ
MAP=(
  "acom-backend:prod-1=acome-offer-desk-backend:latest"
  "acom-web:prod-1=acome-offer-desk-web:latest"
  "acom-file-guard:prod-1=acome-offer-desk-file_guard:latest"
  "acom-notifications-worker:prod-1=acome-offer-desk-notifications_worker:latest"
  # minio: тег в манифесте запіннен (R-B3) по фактической версии прод-образа,
  # проверено в песочнице Ф5-3: RELEASE.2025-09-07T16-13-09Z
  "minio/minio:RELEASE.2025-09-07T16-13-09Z=minio/minio:latest"
)
# образы, которые уже лежат локально под нужным тегом — только импорт
PASSTHROUGH=(
  "nginx:1.27-alpine"
  "order-database-postgres:with-cron"
  "rabbitmq:3-management"
  # Keycloak НЕ импортируем: в k8s он не разворачивается (политика 23.07.2026)
)

run() { if [ "$APPLY" = 1 ]; then echo "+ $*"; "$@"; else echo "  [dry] $*"; fi; }

if [ "$FROM_GHCR" = 1 ]; then
  echo "GHCR-вариант: здесь будет docker pull ghcr.io/<org>/<image>:<tag> + импорт."
  echo "Пока не реализовано — D7 плана, отдельная фаза (нужен imagePullSecret)."
  exit 0
fi

echo "=== проверка источников ==="
for pair in "${MAP[@]}"; do
  src="${pair#*=}"
  if docker image inspect "$src" >/dev/null 2>&1; then
    echo "  OK   $src"
  else
    echo "  НЕТ  $src  (образ отсутствует — сначала сборка/выгрузка)" >&2
    MISSING=1
  fi
done
for img in "${PASSTHROUGH[@]}"; do
  docker image inspect "$img" >/dev/null 2>&1 && echo "  OK   $img" || { echo "  НЕТ  $img" >&2; MISSING=1; }
done
if [ "${MISSING:-0}" = 1 ]; then
  echo
  echo "Не все источники на месте. Варианты: собрать образы (см. docker-compose.yml"
  echo "проекта: backend/file_guard/notifications_worker/web) или получить их из CI."
  exit 1
fi

echo
echo "=== ретег под теги манифестов ==="
for pair in "${MAP[@]}"; do
  dst="${pair%%=*}"; src="${pair#*=}"
  run docker tag "$src" "$dst"
done

echo
echo "=== импорт в containerd k3s ==="
TAGS=()
for pair in "${MAP[@]}"; do TAGS+=("${pair%%=*}"); done
TAGS+=("${PASSTHROUGH[@]}")
run docker save "${TAGS[@]}" -o /tmp/acom-images.tar
run k3s ctr images import /tmp/acom-images.tar

echo
echo "=== проверка в containerd (должны быть все теги манифестов) ==="
if [ "$APPLY" = 1 ]; then
  k3s ctr images ls -q | grep -E "acom-|minio/minio:RELEASE|rabbitmq|nginx|order-database" || true
else
  echo "  [dry] k3s ctr images ls -q | grep …"
fi
echo
echo "Готово. Дальше: создать Secret/ConfigMap (см. README.md) → --dry-run=server → apply."
