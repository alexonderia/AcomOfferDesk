#!/usr/bin/env bash
# Готовит PVC `acom-restore` к jobs/restore-db.job.yaml (прод-дамп не читается из /root
# подом напрямую — файлы сначала копируются в том).
#
# Шаги: PVC + staging-под → kubectl cp → md5 ВНУТРИ тома (сверить с шагом 0) → удалить под.
# Job запускается ОТДЕЛЬНО, вручную:
#   kubectl -n acom apply -f jobs/restore-db.job.yaml
#
# Запуск: на VPS, под root.  NS=acom SRC=/root/mbo2-backups-20260915 ./restore-db.sh
set -euo pipefail

NS="${NS:-acom}"
SRC="${SRC:-/root/mbo2-backups-20260915}"
KUBECTL="${KUBECTL:-kubectl}"
STAGE_POD="restore-stage"
PCA="acom-restore"

DUMP="$SRC/order_database.dump"
ROLES="$SRC/roles_order_db.sql"
[ -f "$DUMP" ] || { echo "нет дампа: $DUMP" >&2; exit 1; }

echo "0/4 md5 источников (сверить с реестром бэкапов в плане):"
md5sum "$DUMP"; [ -f "$ROLES" ] && md5sum "$ROLES" || true

echo "1/4 PVC + staging-под"
"$KUBECTL" -n "$NS" apply -f - <<YAML
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ${PCA}
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: ${STAGE_POD}
  labels:
    app: ${STAGE_POD}
spec:
  restartPolicy: Never
  automountServiceAccountToken: false
  containers:
    - name: stage
      image: order-database-postgres:with-cron
      imagePullPolicy: Never
      command: ["sh", "-ec", "sleep 3600"]
      volumeMounts:
        - name: backup
          mountPath: /backup
  volumes:
    - name: backup
      persistentVolumeClaim:
        claimName: ${PCA}
YAML

echo "2/4 ждём pod/${STAGE_POD}"
"$KUBECTL" -n "$NS" wait --for=condition=Ready "pod/${STAGE_POD}" --timeout=180s

echo "3/4 копируем в том"
"$KUBECTL" -n "$NS" cp "$DUMP" "${STAGE_POD}:/backup/order_database.dump"
if [ -f "$ROLES" ]; then
  "$KUBECTL" -n "$NS" cp "$ROLES" "${STAGE_POD}:/backup/roles_order_db.sql"
fi
echo "--- md5 ВНУТРИ тома (обязан совпасть с шагом 0):"
"$KUBECTL" -n "$NS" exec "$STAGE_POD" -- md5sum /backup/order_database.dump

echo "4/4 убираем staging-под (PVC остаётся)"
"$KUBECTL" -n "$NS" delete pod "$STAGE_POD" --wait=true

echo "дальше: $KUBECTL -n $NS apply -f jobs/restore-db.job.yaml"
echo "и проверка: $KUBECTL -n $NS logs job/restore-db | tail -20"
