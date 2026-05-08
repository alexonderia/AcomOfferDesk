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

