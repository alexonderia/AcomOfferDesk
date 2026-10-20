# Окружения и запуск

## Compose contract

Основной stack запускается из `docker-compose.yml` с нужным overlay:

```powershell
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Production-like использует `.env.prod-like` и `docker-compose.prod-like.yml`; production — соответствующий private env и `docker-compose.prod.yml`. PostgreSQL доступен через внешнюю сеть `project_net`.

## IAM env

Backend contract:

- `IAM_INTERNAL_BASE_URL`;
- `IAM_PUBLIC_BASE_URL`;
- `IAM_ISSUER`;
- `IAM_AUDIENCE`;
- `IAM_SIGNING_PUBLIC_KEY`;
- `IAM_SIGNING_KID`;
- `IAM_INTERNAL_SERVICE_TOKEN`;
- IAM cookie names и timeout.

Private IAM runtime/signing settings находятся в `.env.iam`; migration DB settings — в `.env.iam-db`.

## Проверки

```powershell
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config
.\scripts\check-iam.ps1 -EnvFile .env.dev
.\scripts\smoke-infra.ps1 -EnvFile .env.dev
```

Smoke проверяет gateway/web, backend health, IAM login redirect, public JWKS, изоляцию internal IAM API, PostgreSQL, MinIO и RabbitMQ.
