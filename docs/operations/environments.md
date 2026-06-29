# Окружения

## Граница ответственности документа

Этот документ — единый источник по режимам `dev/test/prod`, compose-слоям, сетевому периметру и admin-only доступу.

**Слияние `dev` → `test` (деплой):** см. [`branch-merge-policy.md`](branch-merge-policy.md) — PR, CI gate `Promotion to test`, защита ветки `test` в GitHub.

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
| `docker-compose.maintenance.yml` | Override для ручного maintenance mode: переводит `gateway` в режим полной заглушки без пересборки `backend/web` |
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
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml -f docker-compose.dev.yml --profile ngrok up -d --build keycloak file_guard backend web gateway rabbitmq minio notifications_worker ngrok max_bot
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
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.maintenance.yml config
docker compose --env-file .env.test -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.test.yml -f docker-compose.maintenance.yml config
```

## Maintenance mode

### Автоматический fallback

- Базовый `gateway` всегда поднимается вместе с внутренним сервисом `maintenance`.
- Если недоступен `web`, запросы на `/` и SPA-маршруты получают maintenance page вместо стандартного nginx `502`.
- Если недоступен `backend`, запросы на `/api/*` получают контролируемый `503` JSON:

```json
{"detail":"Система временно недоступна. Ведутся технические работы."}
```

- `/iam/*` продолжает проксироваться в `keycloak`, пока сам Keycloak доступен.
- `maintenance` не публикуется наружу отдельным портом и остается доступным только внутри `project_net`.

### Ручной maintenance mode

Ручной режим включается дополнительным compose-override `docker-compose.maintenance.yml`. В этом режиме:

- `/` и `/iam/*` отдают maintenance page;
- `/api/*` отдает `503` JSON;
- `/health` отвечает из maintenance-контура, чтобы сам `gateway` оставался доступным.

Включить `dev`:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.maintenance.yml up -d gateway maintenance
```

Выключить `dev`:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d gateway maintenance
```

Включить `prod-like`:

```bash
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml -f docker-compose.maintenance.yml up -d gateway maintenance
```

Выключить `prod-like`:

```bash
docker compose --env-file .env.prod-like -f docker-compose.yml -f docker-compose.prod-like.yml up -d gateway maintenance
```

Включить `test`:

```bash
docker compose --env-file .env.test -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.test.yml -f docker-compose.maintenance.yml up -d gateway maintenance
```

Выключить `test`:

```bash
docker compose --env-file .env.test -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.test.yml up -d gateway maintenance
```

Включить `prod`:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.maintenance.yml up -d gateway maintenance
```

Выключить `prod`:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d gateway maintenance
```

### Локальная проверка

1. Проверить итоговый compose:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.maintenance.yml config
```

2. Поднять `dev`-стенд:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

3. Проверить обычный режим:

```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/api/health
curl -i "http://localhost:8080/api/v1/auth/oidc/login?next_path=%2F"
curl -i http://localhost:8080/iam/
```

4. Проверить автоматический fallback frontend:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml stop web
curl -i http://localhost:8080/
```

5. Проверить автоматический fallback API:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml stop backend
curl -i "http://localhost:8080/api/v1/auth/oidc/login?next_path=%2F"
curl -i http://localhost:8080/api/health
curl -i http://localhost:8080/health
```

6. Проверить ручной maintenance mode:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.maintenance.yml up -d gateway maintenance
curl -i http://localhost:8080/
curl -i http://localhost:8080/api/health
curl -i http://localhost:8080/iam/
```

7. Вернуть обычный режим:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d gateway maintenance web backend
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

### Смена `trycloudflare` адреса в `dev`

`cloudflared` quick tunnel на `trycloudflare.com` выдает новый публичный hostname после перезапуска контейнера. При смене адреса нужно обновить не только сам tunnel URL, но и все публичные OIDC/Keycloak значения, иначе логин ломается либо на `1033`, либо на `redirect_uri`.

Обязательные точки синхронизации в `.env.dev`:

- `KEYCLOAK_PUBLIC_BASE_URL=https://<new-host>.trycloudflare.com/iam`
- `KEYCLOAK_ISSUER_URL=https://<new-host>.trycloudflare.com/iam/realms/acom-offerdesk`
- `KC_HOSTNAME=https://<new-host>.trycloudflare.com/iam`
- `WEB_BASE_URL=https://<new-host>.trycloudflare.com`
- `PUBLIC_BACKEND_BASE_URL=https://<new-host>.trycloudflare.com`

Дополнительно проверьте прокси-слой: `backend/nginx.conf` и maintenance gateway config должны считать `*.trycloudflare.com` HTTPS-хостом для `X-Forwarded-Proto`, иначе OIDC redirect и issuer начинают расходиться с публичным URL.

После изменения env нужно пересоздать runtime-сервисы, которые читают новый публичный base URL:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml --profile tunnel up -d --force-recreate keycloak backend web gateway cloudflared
```

В `docker-compose.dev.yml` dev-Keycloak теперь сам запускает `infra/keycloak/bootstrap.sh` при старте, поэтому после пересоздания `keycloak` клиент `acom-web` автоматически получает актуальные:

- `redirectUris`
- `webOrigins`
- `rootUrl`
- `baseUrl`

Если нужно быстро переприменить bootstrap вручную без полного пересоздания dev-стека, используйте штатный one-shot init:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.init.yml run --rm --no-deps keycloak_bootstrap
```

Если нужен только срочный фикс OIDC-клиента без полного bootstrap, достаточно обновить client `acom-web` через `kcadm` в running `keycloak`.

Минимальная проверка после смены адреса:

```bash
curl -I https://<new-host>.trycloudflare.com/
curl -I "https://<new-host>.trycloudflare.com/api/v1/auth/oidc/login?next_path=%2F"
curl -I "https://<new-host>.trycloudflare.com/iam/realms/acom-offerdesk/protocol/openid-connect/auth?client_id=acom-web&response_type=code&redirect_uri=https%3A%2F%2F<new-host>.trycloudflare.com%2Fapi%2Fv1%2Fauth%2Fcallback"
```

Ожидаемое поведение:

- главная страница отвечает `200`
- `/api/v1/auth/oidc/login` отвечает `302`
- `Location` в этом `302` указывает только на текущий `https://<new-host>.trycloudflare.com/...`
- OIDC auth endpoint больше не возвращает `Неверный параметр: redirect_uri`

Если открыть старый quick-tunnel hostname после перезапуска `cloudflared`, Cloudflare вернет `Error 1033`, потому что предыдущий временный tunnel уже не существует.

## Внутренний сервисный поток

| Откуда | Куда | Порт |
|---|---|---|
| `gateway` | `web` | `80` |
| `gateway` | `maintenance` | `80` |
| `gateway` | `backend` | `8000` |
| `gateway` | `keycloak` | `8080` |
| `backend` | PostgreSQL (`order_database`) | `5432` |
| `backend` / `notifications_worker` | `rabbitmq` | `5672` |
| `backend` | `file_guard` | `8080` |
| `backend` | `minio` | `9000` |
| `backend` / `notifications_worker` / `keycloak` | SMTP/IMAP | provider ports |

## File Guard upload scanning

- `file_guard` — внутренний FastAPI-сервис проверки загружаемых файлов перед сохранением в MinIO и перед записью связей в БД.
- Сервис не публикуется наружу через `ports`, не подключается к `gateway` и доступен только по service name `http://file_guard:8080` внутри `project_net`.
- Backend работает в fail-closed режиме: если `file_guard` недоступен или вернул ошибку, пользовательский файл не должен попадать в MinIO и БД.
- Результат проверки не сохраняется в отдельную бизнес-таблицу БД; это только gate перед текущей логикой хранения.
- MVP allowlist: `.pdf`, `.docx`, `.xlsx`, `.jpg`, `.jpeg`, `.png`.
- Базовые env-переменные backend/runtime:
  - `FILE_GUARD_ENABLED=true`
  - `FILE_GUARD_URL=http://file_guard:8080`
  - `FILE_GUARD_TIMEOUT_SECONDS=10`
  - `FILE_GUARD_MAX_FILE_SIZE_BYTES=5242880`
- Локальная проверка runtime-контура:
  - `docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config`
  - `docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build file_guard backend web gateway`
- Проверка должна завершаться до постоянного хранения файла. Разрешённый файл продолжает текущий flow, заблокированный — возвращает безопасную ошибку frontend.
- Если ручной smoke включает backend upload с реальным сохранением (например, `POST /api/v1/normative-files`), cleanup обязателен: после подтверждения happy-path нужно удалить созданную запись и storage object, чтобы не оставлять тестовые артефакты в БД и MinIO.
- Для cleanup сохраняйте `normative_id` из ответа upload и проверяйте ожидаемое имя файла перед удалением. Пример для удаления тестового normative file через runtime backend container:

```bash
docker exec backend sh -lc "cd /app && python - <<'PY'
import asyncio
from sqlalchemy import text
from app.core.uow import UnitOfWork
from app.services.files import FileService

TARGET_NORMATIVE_ID = 8
TARGET_FILE_NAME = 'ok.png'

async def main():
    async with UnitOfWork() as uow:
        row = await uow.files.get_normative_file_row(normative_id=TARGET_NORMATIVE_ID)
        if row is None:
            print('already_absent')
            return
        if row.original_name != TARGET_FILE_NAME:
            raise RuntimeError(f'unexpected normative file: {row}')
        await uow.session.execute(
            text('DELETE FROM normative_files WHERE id = :id'),
            {'id': TARGET_NORMATIVE_ID},
        )
        await uow.session.flush()
        await FileService(uow.files).delete_file(file_id=row.file_id)
        print(
            {
                'deleted_normative_id': TARGET_NORMATIVE_ID,
                'deleted_file_id': row.file_id,
                'original_name': row.original_name,
            }
        )

asyncio.run(main())
PY"
```

- Минимальная post-cleanup проверка:

```bash
docker exec backend sh -lc "cd /app && python - <<'PY'
import asyncio
from app.core.uow import UnitOfWork

TARGET_NORMATIVE_ID = 8
TARGET_FILE_ID = 64

async def main():
    async with UnitOfWork() as uow:
        row = await uow.files.get_normative_file_row(normative_id=TARGET_NORMATIVE_ID)
        db_file = await uow.files.get_by_id(TARGET_FILE_ID)
        print({'normative_exists': row is not None, 'file_exists': db_file is not None})

asyncio.run(main())
PY"
```

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

Keycloak SMTP (realm `smtpServer`):

- Переменные `SMTP_*` / `KEYCLOAK_SMTP_*` в `.env` **не попадают в realm автоматически** при обычном `docker compose up keycloak`.
- После смены SMTP в env примените настройки в realm (быстро, без полного bootstrap):

```bash
ENV_FILE=.env.prod-like ./scripts/apply-keycloak-smtp.sh
```

- Полный `keycloak_bootstrap` (роли/клиенты) по-прежнему в `docker-compose.init.yml`; SMTP в нём теперь применяется в начале и перед тяжёлой синхронизацией ролей.

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

### Department delegation bootstrap note (2026-05)

`infra/keycloak/bootstrap.sh` now creates department delegation roles in `acom-api`:

- atomic `department.*` roles;
- composite `delegation.department.*` roles;
- one-to-one composite mapping `delegation.department.X -> department.X`.

Operational invariants:

- `delegation.department.*` are not auto-assigned to all users;
- `delegation.department.*` are not included in default `app.*` composites;
- `keycloak_user_role_sync` reconciles only `app.*` by `users.id_role` and should not wipe manually assigned delegation roles.
