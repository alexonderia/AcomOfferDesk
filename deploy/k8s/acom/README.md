# deploy/k8s/acom — прод-оверлей AcomOfferDesk под k3s на VPS `acom-vps`

Перенос прод-стека AcomOfferDesk (сейчас docker compose в `/opt/acome-offer-desk`) в k3s
на ТОМ ЖЕ хосте: namespace `acom`, StorageClass `local-path`, без NodePort/Ingress — вход
через хостовый nginx на `127.0.0.1:8080`.

Манифесты написаны с нуля под фактический состав прод-стека (отчёт разведки
`f5-recon-20260915.md`) и решения блока «Ф5-свод» плана MBO-2. Пилот `k8s-pilot-popos`
(локальный k3s на ПК) в качестве шаблона НЕ использовался.

## Состав (27 файлов оверлея; Keycloak — вне оверлея, см. «Политика: Keycloak запрещён»)

| Путь | Назначение |
|---|---|
| `namespace.yaml` | namespace `acom` (+ labels) |
| `rbac/runtime-serviceaccounts.yaml` | SA `acom-runtime` (без прав, `automountServiceAccountToken: false`) |
| `config/app-configmap.yaml` | неконфиденциальные env-переменные приложения (имена из прод-`.env`, значения — только безопасные дефолты) |
| `config/rabbitmq.conf` | rabbitmq.conf: `listeners.tcp = none` (R-E2), все `ssl_options.*` на 5671 (R-E1/E3), management только по HTTPS |
| `config/rabbitmq-enabled_plugins` | список плагинов (читается только из `/etc/rabbitmq/enabled_plugins`) |
| `config/gateway-nginx.conf` | конфиг nginx-гейтвея: `proxy_pass` на k8s-DNS (`backend:8000`, `web:80`, `maintenance:80`), а не на docker-DNS; локации `/iam/` **выключены** (политика, статический upstream без Service не дал бы nginx подняться) |
| `config/maintenance-default.conf` | страница «ведутся технические работы» |
| `config/secrets.example.yaml` | ПРИМЕР Secret'ов (значения-заглушки), монтируется файлом `05-credentials.conf` |
| `storage/pvcs.yaml` | PVC: rabbitmq-data, minio-data, clamav-data (keycloak-data убран — политика) |
| `data/postgres-statefulset.yaml` | Postgres 16 + pg_cron: StatefulSet + volumeClaimTemplates, QoS **Guaranteed**, `shared_preload_libraries=pg_cron`, `cron.database_name=order_database`, TLS (`ssl=on`) через initContainer (готовит `/tls`, key 0600); Services `postgres` и алиас `order-db` |
| `workloads/rabbitmq.yaml` | Deployment (Recreate) + Service: AMQPS 5671 + management 15672 (HTTPS), учётка из Secret, probes щадящие (liveness `rabbitmq-diagnostics` раз в 60 c — в проде healthcheck каждые 5 c давал 197 % CPU) |
| `workloads/minio.yaml` | StatefulSet + volumeClaimTemplates, non-root UID 1000, TLS `--certs-dir`, тег ЗАПИННЕН |
| — | **Keycloak в оверлее НЕТ** — политика `policy_acom_no_keycloak_cod_jul2026` (Тоток/СБ, 23.07.2026): «полностью запрещён», альтернатива — корп. IAM. Манифест сохранён в `excluded-by-policy/` |
| `workloads/backend.yaml` | Deployment + Service backend:8000 |
| `workloads/web.yaml` | Deployment + Service web:80 |
| `workloads/gateway.yaml` | Deployment + Service gateway:80 (тип ClusterIP — наружу публикует хостовый nginx) |
| `workloads/maintenance.yaml` | Deployment + Service заглушки |
| `workloads/file-guard.yaml` | Deployment + Service `file-guard` (в проде `file_guard` — подчёркивание недопустимо в k8s) |
| `workloads/notifications-worker.yaml` | Deployment `notifications-worker` (в проде `notifications_worker`) |
| `networking/networkpolicy.yaml` | default-deny + точечные allow (edge/app/data), egress к DNS |
| `jobs/restore-db.job.yaml` | одноразовый restore прод-дампа (Ф5-8), destructive — в kustomization НЕ включён |
| `jobs/flyway-migrate.job.yaml` | миграции схемы (Ф5-7), применять после Postgres Ready |
| `jobs/post-deploy-verify.job.yaml` | пост-проверки (Ф5-10) |
| `scripts/import-images.sh` | сборка/ретег образов + `k3s ctr images import` (см. ниже) |
| `scripts/restore-db.sh` | копирует прод-дамп в PVC `acom-restore` + проверяет md5 внутри тома, затем вручную `restore-db.job.yaml` |

## Что обязательно создать ДО `kubectl apply -k`

kustomization НЕ создаёт Secret'ы и часть ConfigMap'ов (там есть значения прод-секретов —
их нельзя держать в git). Имена и ключи:

| Объект | Ключи | Откуда взять |
|---|---|---|
| Secret `acom-db-secret` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `/opt/order_database/.env` (значения не печатать) |
| ~~Secret `acom-kc-secret`~~ | **НЕ создаётся** — Keycloak запрещён политикой (23.07.2026) | — |
| Secret `acom-minio-secret` | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | прод-`.env` (в compose были дефолтные `minioadmin/minioadmin` — нарушение, R-C3) |
| Secret `rabbitmq-credentials` | файл `05-credentials.conf` (`default_user` / `default_pass`) | новый пароль; в k8s НЕ используем `RABBITMQ_DEFAULT_*` |
| Secret `rabbitmq-tls` | `ca.crt`, `server.crt`, `server.key` | сертификат с **SAN `DNS:rabbitmq`** |
| Secret `postgres-tls` | `ca.crt`, `server.crt`, `server.key` | сертификат с **SAN `DNS:postgres`** |
| Secret `minio-tls` | `CAs/ca.crt`, `public.crt`, `private.key` | сертификат с **SAN `DNS:minio`** |
| ~~ConfigMaps `keycloak-*`~~ | **НЕ создаются** — Keycloak в k8s не разворачивается (политика) | — |

**SAN сертификата обязан совпадать с именем Service** — проверено в песочнице Ф5-3:
с сертификатом для `rabbitmq` в роли MinIO проверка TLS по имени `minio` не проходит.

**Авторизация (важно):** Keycloak в k8s-контур НЕ входит. Действующая прод-схема —
`start-dev` + H2-файл (`keycloakdb.mv.db` в томе `acome-offer-desk_keycloak_data`); схема
`keycloak` в дампе `order_database` — артефакт прошлых прогонов, к входу в k8s отношения
не имеет. Целевой auth — корп. IAM (мультифактор): PR #53 (dev) убрал Keycloak из кода и
добавил `.env.iam.*`. Варианты переходного периода — `excluded-by-policy/README.md`.

## Проверено в песочнице Ф5-3 (15.09.2026)

Изолированные одноразовые контейнеры на `acom-vps` (сеть `f5-sandbox`), прод не менялся.

* **Postgres + restore прод-дампа — PASS.** `pg_restore --no-owner --no-privileges -j2
  --exit-on-error` на копию дампа: `exit=0`, схемы `cron,keycloak,public`, 29 таблиц
  `public` + **90 таблиц `keycloak`**, realms `master,acom-offerdesk`, 16 пользователей.
  Обязательное условие — `shared_preload_libraries=pg_cron` (без него `CREATE EXTENSION
  pg_cron` падает и restore обрывается: воспроизведено).
* **Keycloak — ИСКЛЮЧЁН ИЗ ОВЕРЛЕЯ (политика).** В песочнице успели прогнать конфигурацию
  KC 26.5 на postgres, но это НЕ тот путь: прод-Keycloak работает в `start-dev` с H2-файлом
  (`keycloakdb.mv.db`), а главное — Keycloak запрещён в контуре решением СБ/Тоток
  (23.07.2026), и PR #53 в `dev` уже убрал его из кода. Итог: манифест в `excluded-by-policy/`,
  в kustomization не входит; `/iam` в gateway выключен. Проверка KC-на-postgres оставлена
  как **история работ**, не как рецепт.
* Прод-факты входа (пригодятся при переходе на IAM): внешний префикс `/iam` (хостовый nginx),
  проброс `X-Forwarded-*`, health-порт сервиса 9000.
* **curl в образе postgres НЕТ** (есть `psql`, `pg_isready`, `pg_restore`, `openssl`).
  Все HTTP-проверки вынесены в контейнер на образе `acome-offer-desk-backend:latest`
  (там `curl` есть) — `jobs/post-deploy-verify.job.yaml` разделён на `http-verify` и `db-verify`.
* **RabbitMQ:** сертификаты в Secret нужны с `defaultMode: 0440` (иначе нода Erlang UID 999
  не читает ключ и брокер падает) — уже учтено в `workloads/rabbitmq.yaml`.
* **containerd (k3s) НЕ содержит ни одного из нужных образов** (`k3s ctr images ls`):
  без шага 1 (`scripts/import-images.sh`) все поды встанут с `ErrImageNeverPull`.
* MinIO TLS: проверка по имени `minio` (SAN) и через `--cacert` — конфиг `--certs-dir` верный;
  расхождение давал старый скрипт с неверным `docker inspect` (в манифесте не влияет).

## Политика: Keycloak запрещён (в оверлей НЕ возвращать)

* Graph RAG: `policy_acom_no_keycloak_cod_jul2026` (Policy; источник `cursor_session_2026-07-23-totok-meeting`) —
  **«Keycloak полностью запрещён»**, альтернатива — **«Мультифактор (корп. IAM)»**;
  авторитет **Тоток С.И. / СБ, 23.07.2026**; impact: «требуется смена auth-стека для ЦОД;
  текущий OIDC Keycloak на VPS — не канон для ЦОД». В графе: `meeting_totok_acom_cod_jul2026_07_23 -[DECIDED]-> политика`.
* Код: **PR #53** `without_keycloak_and_others` (alexonderia → `dev`, 04.09.2026, merge SHA `a804af5`) —
  `auth.py` −622 строки, добавлены `.env.iam.*`. Ветка `test` (прод-VPS) не тронута.
* Решение по оверлею (15.09.2026): манифест → `excluded-by-policy/keycloak.yaml`, PVC
  `keycloak-data` убран, локации `/iam/` в gateway выключены, KC-секрет и KC-ConfigMap'ы
  не создаются; в verify-Job KC-проверок нет.
* Открытый вопрос владельцу: переходный период — `/iam` отдаёт хостовый nginx прямо в
  compose-контейнер, **или** вход в k8s ждёт готовности корп. IAM.

## Образы (важно)

`imagePullPolicy: Never` у всех подов, а в containerd прод-образов Acom нет. Перед apply
нужно импортировать образы (`scripts/import-images.sh`):

| Тег в манифесте | Источник на хосте |
|---|---|
| `acom-backend:prod-1` | `acome-offer-desk-backend:latest` |
| `acom-web:prod-1` | `acome-offer-desk-web:latest` |
| `acom-file-guard:prod-1` | `acome-offer-desk-file_guard:latest` |
| `acom-notifications-worker:prod-1` | `acome-offer-desk-notifications_worker:latest` |
| `nginx:1.27-alpine` | есть локально |
| `order-database-postgres:with-cron`, `rabbitmq:3-management` | есть локально |
| `minio/minio:RELEASE.2025-09-07T16-13-09Z` | `minio/minio:latest` + **ретег** (`docker tag`) |

Перспектива (решение D7 плана): сборка в CI → GHCR + `imagePullSecret`, тогда
`imagePullPolicy` меняется на `IfNotPresent`, а ретег не нужен.

## Порядок Ф5

1. `scripts/import-images.sh` (или сборка в CI);
2. создать Secret'ы из таблицы выше (ConfigMap'ы Keycloak больше не нужны — политика);
3. `kubectl apply --dry-run=server -k deploy/k8s/acom` — валидация без изменений кластера;
4. `kubectl apply -k deploy/k8s/acom` (namespace `acom` уже существует);
5. `kubectl -n acom wait --for=condition=Ready pod -l app=postgres --timeout=300s`;
6. `kubectl -n acom apply -f jobs/restore-db.job.yaml` — восстановление прод-дампа (Ф5-8);
7. `kubectl -n acom apply -f jobs/flyway-migrate.job.yaml` — миграции (Ф5-7);
8. `kubectl -n acom apply -f jobs/post-deploy-verify.job.yaml` — проверки (Ф5-10);
9. переключение хостового nginx на порт gateway-сервиса (последний шаг, с откатом).

## Откат

Compose-стек не удаляем: `docker compose stop` (не `down`) — прод возвращается одной
командой. Тома Docker (`order_database_pg_data`, `acome-offer-desk_keycloak_data`,
minio) остаются нетронутыми до подтверждённой приёмки.

## Открытые вопросы

* `flyway/flyway` в compose объявлен, но образ не запущен, а `/opt/order_database/deploy/flyway/sql` отсутствует — в манифесте Job использует образ `flyway/flyway:12.1.0`, его тоже нужно импортировать.
* Дайджесты (`RepoDigests`) у всех образов пусты → пиннинг по digest невозможен; пока фиксируем теги.
* `max_bot` и `tg_bot` в k8s сознательно не переносятся (решение «Ф5-свод»).
