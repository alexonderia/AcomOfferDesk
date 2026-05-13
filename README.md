# AcomOfferDesk

AcomOfferDesk — внутренняя платформа для работы с заявками и офферами между сотрудниками и контрагентами.

## Коротко о проекте

- frontend: React SPA (`web`)
- backend: FastAPI (`backend`)
- auth: Keycloak OIDC
- infra runtime: Docker Compose (`gateway`, `rabbitmq`, `minio`, `notifications_worker`)
- внешняя БД: `order_database` (отдельный репозиторий)

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
- [Roadmap/ТЗ production-readiness](docs/release/release-preparation-tz.md)

### Менять вход/регистрацию/Keycloak

- [Аутентификация и онбординг (актуальная модель)](docs/security/auth-and-onboarding.md)
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

3. Для init Keycloak:

```bash
docker compose --env-file .env.dev -f docker-compose.init.yml up keycloak_db_prepare
docker compose --env-file .env.dev -f docker-compose.init.yml up keycloak_bootstrap
```

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
  - PowerShell: `./scripts/test-release.ps1 -EnvFile .env.dev -IncludeE2E -ProvisionE2EUsers`
  - Bash: `ENV_FILE=.env.dev INCLUDE_E2E=true PROVISION_E2E_USERS=true ./scripts/test-release.sh`
- Frontend e2e smoke: `npm --prefix web run e2e:smoke`
- Frontend extended e2e (manual):
  - `npm --prefix web run e2e:roles`
  - `npm --prefix web run e2e:registration`
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
Both manual workflows use temporary provisioned e2e users by default (`PROVISION_USERS=true`).

