# AcomOfferDesk

AcomOfferDesk — внутренняя платформа для работы с заявками и офферами между сотрудниками и контрагентами.

## Коротко о проекте

- frontend: React SPA (`web`)
- backend: FastAPI (`backend`)
- auth: временно недоступна (Stage 1 IAM migration, fail-closed)
- infra runtime: Docker Compose (`gateway`, `rabbitmq`, `minio`, `notifications_worker`)
- внешняя БД: `order_database` (отдельный репозиторий)

## Деплой на VPS (ветка `test`)

- Push в **`test`** запускает GitHub Actions **Deploy to VPS** (`.github/workflows/deploy.yml`).
- На сервере checkout выравнивается с удалённой веткой: **`git reset --hard upstream/test`** (без ручного merge при локальных правках на диске).
- Перед подъёмом приложения workflow **синхронизирует Flyway-миграции** с каталога репозитория **`deploy/order_database/flyway/sql`** в **`/opt/order_database/flyway/sql`**, делает **`pg_dump`** бэкап и выполняет **`flyway migrate`**. Источник правды по SQL по-прежнему — репозиторий **[alexonderia/order_database](https://github.com/alexonderia/order_database)**; снимок в этом репо нужно обновлять при добавлении новых **`V*.sql`** (см. [docs/order-database-vps.md](docs/order-database-vps.md)).
- Команды **`docker compose`** в деплое используют **`--env-file backend/.env`** и **`APP_RUNTIME_ENV_FILE`**.

Ветки **`dev`** и **`test`** для релиза должны содержать одинаковые правки документации и деплоя; после изменений в миграциях БД проверьте обе ветки и smoke на test.

## Карта документации

Полный каталог по категориям: [docs/README.md](docs/README.md)

### Впервые открыть проект

- [Обзор продукта и бизнес-сценариев](docs/product/project-overview.md)
- [Runtime-архитектура и потоки данных](docs/product/runtime-architecture.md)
- [Навигация по кодовой базе](docs/development/developer-guide.md)
- [Стратегия тестирования](docs/development/testing-strategy.md)

### Запустить окружение

- [Окружения, compose, perimeter и admin-only доступ](docs/operations/environments.md)

### Готовить test/prod релиз

- [Контракт production-переменных и секретов](docs/release/production-env.md)
- [Практический release checklist](docs/release/release-checklist.md)

### Менять вход/регистрацию/IAM

- [Аутентификация и онбординг (Stage 1 и legacy reference)](docs/security/auth-and-onboarding.md)
- [Матрица прав (permissions)](docs/security/permissions-matrix.md)

### Решать проблемы на VPS

- [order_database/Flyway/VPS runbook](docs/operations/order-database-vps.md)
- [Краткий VPS troubleshooting](docs/operations/vps-troubleshooting.md)

## Быстрый старт (dev)

1. Подготовить `.env.dev` из `.env.dev.example`.
2. Поднять стек:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

3. IAM обслуживает login/refresh/logout, локальную проверку access token и effective permissions; backend связывает identity только через `user_auth_accounts(provider='iam')`.

Полные сценарии `dev/prod-like/test/prod`, tunnel-профили, perimeter и проверки — в [docs/operations/environments.md](docs/operations/environments.md).

## Testing And CI

- Backend unit tests:
  - PowerShell: `./scripts/test-unit.ps1`
  - Bash: `./scripts/test-unit.sh`
- Backend integration/API contract tests:
  - PowerShell: `./scripts/test-integration.ps1`
  - Bash: `./scripts/test-integration.sh`
- Frontend lint: `npm --prefix web run lint`
- Frontend unit/component tests: `npm --prefix web run test:unit`
- Frontend build: `npm --prefix web run build`
- Release gate (without e2e):
  - PowerShell: `./scripts/test-release.ps1 -EnvFile .env.dev`
  - Bash: `ENV_FILE=.env.dev ./scripts/test-release.sh`
- Release gate (with optional e2e smoke):
  - PowerShell: `./scripts/test-release.ps1 -EnvFile .env.dev -IncludeE2E -StrictE2E`
  - Bash: `ENV_FILE=.env.dev INCLUDE_E2E=true STRICT_E2E=true ./scripts/test-release.sh`
- Frontend e2e smoke: `npm --prefix web run e2e:smoke`
- Frontend extended e2e (manual):
  - `npm --prefix web run e2e:roles`
  - `npm --prefix web run e2e:request-offer`
  - `npm --prefix web run e2e:dashboard`
  - `npm --prefix web run e2e:files-chat`
  - `npm --prefix web run e2e:extended`

CI workflow: `.github/workflows/ci.yml`
- triggers on `push/pull_request` for `dev_process`, `dev`, `test`
- runs backend unit + backend integration + frontend lint + frontend unit tests + frontend build
- does not run extended e2e tags by default

Manual e2e smoke workflow: `.github/workflows/e2e-smoke.yml` (`workflow_dispatch`).
Manual release smoke workflow: `.github/workflows/release-smoke.yml` (`workflow_dispatch`, optional e2e).
Manual workflows use IAM credentials supplied through `E2E_*_USERNAME`/`E2E_*_PASSWORD` secrets.

