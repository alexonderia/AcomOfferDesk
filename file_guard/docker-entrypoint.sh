#!/bin/sh
set -eu

cleanup() {
  if [ -n "${CLAMD_PID:-}" ]; then
    kill "${CLAMD_PID}" 2>/dev/null || true
    wait "${CLAMD_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "[file_guard] Подготавливаем каталоги ClamAV и права доступа"
mkdir -p /run/clamav /var/lib/clamav /var/log/clamav
chown -R clamav:clamav /run/clamav /var/lib/clamav /var/log/clamav

if [ "${FILE_GUARD_ANTIVIRUS_ENABLED:-true}" = "true" ]; then
  if [ "${FILE_GUARD_CLAMAV_UPDATE_ON_START:-true}" = "true" ]; then
    echo "[file_guard] Обновляем антивирусные базы ClamAV перед запуском"
    freshclam --config-file=/etc/clamav/freshclam.conf || true
  fi

  echo "[file_guard] Запускаем локальный процесс clamd"
  clamd --foreground=true --config-file=/etc/clamav/clamd.conf &
  CLAMD_PID="$!"
else
  echo "[file_guard] Антивирусная проверка отключена настройкой FILE_GUARD_ANTIVIRUS_ENABLED=false"
fi

echo "[file_guard] Запускаем FastAPI-сервис проверки файлов"
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
