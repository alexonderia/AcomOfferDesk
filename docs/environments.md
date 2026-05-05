# Окружения

## Граница ответственности документа

Этот документ — единый источник по режимам `dev/test/prod`, compose-слоям, сетевому периметру и admin-only доступу.

Смежные документы:
- [Runtime-архитектура](./runtime-architecture.md)
- [Production переменные/секреты](./production-env.md)
- [Чек-лист релиза](./release-checklist.md)
- [Аутентификация и онбординг](./auth-and-onboarding.md)

## Модель окружений

| Окружение | Назначение | Публичный вход | Tunnel-инструменты | Публикация host ports |
|---|---|---|---|---|
| `dev` | Локальная разработка на одном ПК | `http://localhost:8080` через `gateway` | Разрешены (`ngrok`, `localtunnel`, `cloudflared`) | Разрешены для локальной диагностики |
| `prod-like` | Локальная production-like проверка | Локальный `gateway` | Не часть production ingress-модели | Обычно только `gateway:8080` |
| `test` | Предрелизный VPS-контур | Внешний HTTPS reverse proxy | Запрещены | Только perimeter, без публичных service ports |
| `prod` | Боевой контур | Внешний HTTPS reverse proxy | Запрещены | Только perimeter, без публичных service ports |

Ключевое правило: `ngrok` и другие tunnel-решения используются только в `dev`.

## Compose-файлы и назначение

| Файл | Назначение |
|---|---|
| `docker-compose.yml` | Базовый internal-first runtime: `expose`, сети, зависимости, healthchecks |
| `docker-compose.dev.yml` | Dev override: localhost ports, dev-профили и `start-dev` для Keycloak |
| `docker-compose.prod-like.yml` | Локальная production-like проверка |
| `docker-compose.prod.yml` | Override для production-периметра в `test/prod` |
| `docker-compose.test.yml` | Test helper: loopback-публикация `gateway` на том же VPS |
| `docker-compose.init.yml` | One-shot init: `keycloak_db_prepare`, `keycloak_bootstrap` |

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
