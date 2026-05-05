# AcomOfferDesk

AcomOfferDesk — внутренняя платформа для работы с заявками и офферами между сотрудниками и контрагентами.

## Коротко о проекте

- frontend: React SPA (`web`)
- backend: FastAPI (`backend`)
- auth: Keycloak OIDC
- infra runtime: Docker Compose (`gateway`, `rabbitmq`, `minio`, `notifications_worker`)
- внешняя БД: `order_database` (отдельный репозиторий)

## Карта документации

### Впервые открыть проект

- [Обзор продукта и бизнес-сценариев](docs/project-overview.md)
- [Runtime-архитектура и потоки данных](docs/runtime-architecture.md)
- [Навигация по кодовой базе](docs/developer-guide.md)

### Запустить окружение

- [Окружения, compose, perimeter и admin-only доступ](docs/environments.md)

### Готовить test/prod релиз

- [Контракт production-переменных и секретов](docs/production-env.md)
- [Практический release checklist](docs/release-checklist.md)
- [Roadmap/ТЗ production-readiness](docs/release-preparation-tz.md)

### Менять вход/регистрацию/Keycloak

- [Аутентификация и онбординг (актуальная модель)](docs/auth-and-onboarding.md)

### Решать проблемы на VPS

- [order_database/Flyway/VPS runbook](docs/order-database-vps.md)
- [Краткий VPS troubleshooting](docs/vps-troubleshooting.md)

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

Полные сценарии `dev/prod-like/test/prod`, tunnel-профили, perimeter и проверки — в [docs/environments.md](docs/environments.md).

