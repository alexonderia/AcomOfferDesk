# Окружения

## Граница ответственности документа

Этот документ — единый источник по режимам `dev/test/prod`, compose-слоям, сетевому периметру и admin-only доступу.

Смежные документы:
- [Runtime-архитектура](../product/runtime-architecture.md)
- [Production переменные/секреты](../release/production-env.md)
- [Чек-лист релиза](../release/release-checklist.md)
- [Аутентификация и онбординг](../security/auth-and-onboarding.md)

## Модель окружений

| Окружение | Назначение | Публичный вход | Tunnel-инструменты | Публикация host ports |
|---|---|---|---|---|
| `dev` | Локальная разработка на одном ПК | `http://localhost:8080` через `gateway` | Разрешены (`ngrok`, `localtunnel`, `cloudflared`) | Разрешены для локальной диагностики |
| `prod-like` | Локальная production-like проверка | Локальный `gateway` | Не часть production ingress-модели | Обычно только `gateway:8080` |
| `test` | Предрелизный VPS-контур | Внешний HTTPS reverse proxy | Запрещены | Только perimeter, без публичных service ports |
| `prod` | Боевой контур | Внешний HTTPS reverse proxy | Запрещены | Только perimeter, без публичных service ports |

Ключевое правило: `ngrok` и другие tunnel-решения используются только в `dev`.

## Auth/Permissions env contract

Для всех окружений используйте разделение Keycloak clients:

- `KEYCLOAK_WEB_CLIENT_ID=acom-web` (public SPA login client).
- `KEYCLOAK_API_CLIENT_ID=acom-api` (источник application permissions в access token).
- `KEYCLOAK_ADMIN_CLIENT_ID=acom-admin-service` + `KEYCLOAK_ADMIN_CLIENT_SECRET` (backend-only admin API access).

Источник permissions:

- backend в первую очередь читает permissions из `resource_access.<KEYCLOAK_API_CLIENT_ID>.roles`;
- если в токене используется новый permission-формат без client roles, backend дополнительно читает `authorization.permissions` и `permissions`.
- legacy/local режим выбора источника permissions удален.

Важно:
- frontend не хранит client secret;
- frontend получает permissions/action metadata только из backend response;
- `users.id_role` остается бизнес-ролью, а не источником security permissions.
- `delegation.*` роли в текущем bootstrap не создаются и не удаляются автоматически (optional extension).
- `delegation.*` сами по себе не являются atomic permissions; чтобы они давали действия, их нужно делать composite и включать коды из `PermissionCodes`.
- `KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE=true` включает init-синхронизацию `app.*` ролей для уже связанных пользователей.
- Для актуализации текущей test-ветки оставляйте `KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE=true`.

## Compose-файлы и назначение

| Файл | Назначение |
|---|---|
| `docker-compose.yml` | Базовый runtime: сервисы, сети, healthchecks; **`gateway`** публикует **127.0.0.1:8080→80** для хостового reverse proxy на VPS (`test`/production perimeter) |
| `docker-compose.dev.yml` | Dev override: localhost ports, dev-профили и `start-dev` для Keycloak |
| `docker-compose.prod-like.yml` | Локальная production-like проверка |
| `docker-compose.prod.yml` | Override для production-периметра в `test/prod` |
| `docker-compose.test.yml` | Test helper: loopback-публикация `gateway` на том же VPS |
| `docker-compose.init.yml` | One-shot init: `keycloak_db_prepare`, `keycloak_bootstrap`, `keycloak_user_role_sync` |

Внешний reverse proxy пример: `infra/reverse-proxy/nginx.prod.example.conf`.

## Сценарии запуска

### Dev

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Dev tunnel profiles:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml --profile ngrok up -d ngrok
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml --profile tunnel up -d localtunnel
```

### Prod-like (локально)

```bash
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml up -d --build
```

Prod-like + `ngrok` (только для внешней проверки callback/email-ссылок в локальной среде):

Предусловия:
- есть верифицированный аккаунт ngrok;
- в `.env.prod-like` задан `NGROK_AUTHTOKEN=<ваш_токен>`.

```bash
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml -f docker-compose.dev.yml --profile ngrok up -d --build keycloak backend web gateway rabbitmq minio notifications_worker ngrok
```

### Test (VPS)

```bash
docker compose --env-file .env.test -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.test.yml up -d --build
```

### Prod

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Рендер итоговой конфигурации

```bash
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml config
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml -f docker-compose.dev.yml --profile ngrok config
docker compose --env-file .env.test -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.test.yml config
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml config
```

Примечание по env-файлам в репозитории:
- уже есть: `.env`, `.env.dev`, `.env.prod-like` и `*.example`;
- `.env.test` и `.env.prod` создаются отдельно под соответствующие контуры.

## Публичный поток (`test/prod`)

1. Пользователь/контрагент -> внешний reverse proxy (`443`, опционально `80 -> 443`).
2. Reverse proxy -> внутренний `gateway`.
3. `gateway` маршрутизирует:
- `/` -> `web`
- `/api/*` -> `backend`
- `/iam/*` -> `keycloak`

Public ingress только через HTTPS reverse proxy.

## Dev tunnel flow

1. Внешний тестировщик -> временный HTTPS tunnel endpoint.
2. Tunnel -> локальный `gateway`.
3. Внутри Docker маршрутизация та же, что и обычно.

Этот flow допустим только для `dev`.

## Внутренний сервисный поток

| Откуда | Куда | Порт |
|---|---|---|
| `gateway` | `web` | `80` |
| `gateway` | `backend` | `8000` |
| `gateway` | `keycloak` | `8080` |
| `backend` | PostgreSQL (`order_database`) | `5432` |
| `backend` / `notifications_worker` | `rabbitmq` | `5672` |
| `backend` | `minio` | `9000` |
| `backend` / `notifications_worker` / `keycloak` | SMTP/IMAP | provider ports |

## Admin-only flow

Служебные интерфейсы (`RabbitMQ UI`, `MinIO Console`, будущий `pgAdmin`) не являются публичными endpoint.

Доступ в `test/prod`:
1. Через терминальный сервер / VPN / private network.
2. Без публикации в интернет.

## Запрещённые публичные порты (`test/prod`)

Нельзя публиковать наружу:
- `8000` (`backend`)
- `8080` (прямой `keycloak`)
- `5432` (PostgreSQL)
- `5672` (RabbitMQ AMQP)
- `15672` (RabbitMQ UI)
- `9000` (MinIO API)
- `9001` (MinIO Console)
- `5050` (pgAdmin)

## Проверки после запуска

### Dev

- `http://localhost:8080` открывается.
- При необходимости доступны localhost admin ports из dev override.
- При `ngrok` публичные callback/email ссылки корректны.

### Test/Prod perimeter

- Внешний вход только через HTTPS.
- OIDC `issuer` и URI редиректа соответствуют домену.
- Служебные порты недоступны из публичного интернета.

### Командные проверки

Linux/macOS:

```bash
bash scripts/check-prod-perimeter.sh
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-prod-perimeter.ps1
```

VPS deploy (`test` branch): `scripts/keycloak-init-deploy.sh` skips the long `keycloak_bootstrap` container when read-only `check_keycloak_permission_model` passes and `infra/keycloak/bootstrap.sh` is unchanged (state: `.deploy-state/keycloak-bootstrap.sha256`). On post-deploy failure it runs `run-keycloak-check-backend.sh --repair`. Force full bootstrap: `KEYCLOAK_BOOTSTRAP_FORCE=1` before deploy.

Keycloak permission model on VPS (running `backend` container):

- **Do not** `docker exec backend python -m app.scripts.check_keycloak_permission_model --env-file /app/backend/.env` — that file is not baked into the image; env is injected by `docker compose --env-file backend/.env` on the host.
- **Do** from `/opt/acome-offer-desk` on the host:
  - `./scripts/post-deploy-verify.sh` — full post-deploy gate (smoke + Keycloak);
  - `./scripts/run-keycloak-check-backend.sh` — Keycloak only (add `--repair` if deploy gate failed and repair is intended).
- CI deploy runs the same pattern via `post-deploy-verify.sh` after `docker compose up`.

Local/dev Keycloak model check (host Python, repo env file): `./scripts/check-keycloak.sh .env.dev` (see `docs/development/testing-strategy.md`).

### Keycloak Admin API (backend: создание пользователей / контрагентов)

- Учётные данные для Admin API задаются в **runtime env** (`backend/.env` на VPS): `KC_BOOTSTRAP_ADMIN_*` и/или `KEYCLOAK_ADMIN_*`, плюс `KEYCLOAK_ADMIN_CLIENT_ID` / `KEYCLOAK_ADMIN_CLIENT_SECRET` для `acom-admin-service`.
- В **`docker-compose.yml` не задавать** `KEYCLOAK_ADMIN_USERNAME` / `KEYCLOAK_ADMIN_PASSWORD` пустыми строками в `environment:` — это перекрывает `env_file` и ломает fallback на bootstrap (ошибка UI: «Unable to authenticate in Keycloak admin API»).
- Если service account без admin-ролей, backend использует password grant bootstrap-админа (`master` realm) — те же переменные, что для `check-keycloak-bootstrap.sh`.

Keycloak bootstrap validation:

Linux/macOS:

```bash
ENV_FILE=.env.prod-like ./scripts/check-keycloak-bootstrap.sh
```

PowerShell:

```powershell
$env:ENV_FILE=".env.prod-like"
powershell -ExecutionPolicy Bypass -File .\scripts\check-keycloak-bootstrap.ps1
```

## WebSocket ticket env defaults

- `WS_TICKET_TTL_SECONDS=30` (recommended range: 30-60).
- `WS_LEGACY_QUERY_TOKEN_ENABLED=false` for prod-like/prod.
- Legacy `?token=` websocket fallback is temporary dev compatibility only and should stay disabled by default.
- `BACKEND_WORKERS=1` while ws-ticket storage is in-memory (without Redis/shared ticket store).
