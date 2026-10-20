#!/usr/bin/env bash
# Ф5-3 (повтор, для протокола): проверка config/rabbitmq.conf из манифеста —
# только AMQPS 5671 с mTLS, plaintext-слушателя 5672 нет (R-E1/E2/E3).
set -u
NET=f5verify; D=/tmp/f5v
docker network create $NET >/dev/null 2>&1 || true
rm -rf "$D"; mkdir -p "$D/tls" "$D/cfg" "$D/data"
cd "$D/tls" || exit 1
echo "=== TLS: CA + server(SAN=rabbitmq) + client ==="
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 2 -subj "/CN=f5-verify-ca" >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj "/CN=rabbitmq" >/dev/null 2>&1
printf "subjectAltName=DNS:rabbitmq\n" > san.cnf
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 2 -extfile san.cnf >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -keyout client.key -out client.csr -subj "/CN=f5-client" >/dev/null 2>&1
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 2 >/dev/null 2>&1
echo "SAN: $(openssl x509 -in server.crt -noout -ext subjectAltName | tail -1)"
# права как в манифесте (readOnly + fsGroup): rabbitmq в образе — uid 999
chown 999:999 ca.crt server.crt server.key; chmod 440 ca.crt server.crt server.key
cp /tmp/f5v-in/rabbitmq.conf "$D/cfg/10-acom.conf"
printf 'default_user = f5v\ndefault_pass = f5v-pass-verify\n' > "$D/cfg/05-credentials.conf"
cp /tmp/f5v-in/enabled_plugins "$D/cfg/enabled_plugins"
chmod 644 "$D/cfg/"*.conf "$D/cfg/enabled_plugins"; chown 999:999 "$D/cfg/"*
# ВАЖНО: каталог данных rabbitmq должен быть доступен на запись uid 999 (иначе
# .erlang.cookie: eacces). В k8s это делает securityContext.fsGroup=999 у пода.
chown 999:999 "$D/data"; chmod 750 "$D/data"
docker rm -f f5v-rmq >/dev/null 2>&1
docker run -d --name f5v-rmq --network $NET --hostname rabbitmq \
  -v "$D/cfg/10-acom.conf:/etc/rabbitmq/conf.d/10-acom.conf:ro" \
  -v "$D/cfg/05-credentials.conf:/etc/rabbitmq/conf.d/05-credentials.conf:ro" \
  -v "$D/cfg/enabled_plugins:/etc/rabbitmq/enabled_plugins:ro" \
  -v "$D/tls:/etc/rabbitmq/certs:ro" \
  rabbitmq:3-management >/dev/null
echo "=== под каким uid работает контейнер ==="; sleep 3; docker exec f5v-rmq id 2>&1 | head -2
echo "=== ждём готовности ==="
for i in $(seq 1 24); do
  docker exec f5v-rmq rabbitmq-diagnostics -q listeners >/dev/null 2>&1 && { echo "готов после ~$((i*5))с"; break; }
  docker ps --format '{{.Names}}' | grep -q f5v-rmq || { echo "КОНТЕЙНЕР УПАЛ"; docker logs f5v-rmq 2>&1 | tail -15; exit 1; }
  sleep 5
done
echo "=== listeners (ожидаем tls 5671 и https 15672, БЕЗ 5672) ==="
docker exec f5v-rmq rabbitmq-diagnostics -q listeners 2>&1 | tail -6
echo "=== лог: стартовавшие интерфейсы ==="
docker logs f5v-rmq 2>&1 | grep -iE "started .*(listener|accept)|listeners.tcp|interface" | head -6
echo "=== ошибки применения конфига (если есть) ==="
docker logs f5v-rmq 2>&1 | grep -iE "error|invalid|refused|failed" | grep -viE "epmd|erlang" | head -4 || echo "(ошибок нет)"
echo "=== plaintext 5672 (ожидаем отказ соединения) ==="
docker run --rm --network $NET --entrypoint bash rabbitmq:3-management -c 'timeout 5 bash -c "</dev/tcp/rabbitmq/5672" 2>/dev/null && echo "ПЛОХО: 5672 открыт" || echo "ОК: 5672 закрыт (connection refused)"'
echo "=== AMQPS 5671 С клиентским сертификатом (ожидаем успех, verify code 0) ==="
docker run --rm --network $NET -v "$D/tls:/t:ro" --entrypoint openssl rabbitmq:3-management \
  s_client -connect rabbitmq:5671 -CAfile /t/ca.crt -cert /t/client.crt -key /t/client.key -verify_return_error </dev/null 2>&1 \
  | grep -E "Verify return code|Protocol|Cipher|subject=" | head -5
echo "=== AMQPS 5671 БЕЗ клиентского сертификата (mTLS: ожидаем отказ) ==="
docker run --rm --network $NET -v "$D/tls:/t:ro" --entrypoint openssl rabbitmq:3-management \
  s_client -connect rabbitmq:5671 -CAfile /t/ca.crt </dev/null 2>&1 \
  | grep -iE "verify|alert|error|peer closed" | head -4
echo "=== уборка ==="
docker rm -f f5v-rmq >/dev/null 2>&1
docker network rm $NET >/dev/null 2>&1
rm -rf "$D"
echo "VERIFY_DONE"
