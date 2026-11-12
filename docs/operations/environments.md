# Окружения и запуск

## Compose contract

Основной stack запускается из `docker-compose.yml` с нужным overlay:

```powershell
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config --quiet
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Production-like использует `.env.prod-like` и `docker-compose.prod-like.yml`; production — соответствующий private env и `docker-compose.prod.yml`. PostgreSQL доступен через внешнюю сеть `project_net`.

Перед сборкой выберите runtime env через `APP_RUNTIME_ENV_FILE` и явно задайте `EMAIL_ENABLED=false` или `EMAIL_ENABLED=true` в файле для `--env-file`. Шаблоны `.env.example`, `.env.dev.example` и `.env.prod-like.example` начинают с режима без почты. Compose отклоняет отсутствующее или пустое значение и передаёт один флаг в backend и notifications_worker; интерфейс получает режим через API, пересборка web для его смены не нужна. Вне Compose программное значение по умолчанию остаётся `true`.

`EMAIL_ENABLED=false` включает создание аккаунтов с паролем из UI, отключает SMTP/IMAP и потребление почтовой очереди. Почтовые настройки необязательны. Для включения почты нужны `true` и корректные SMTP/почтовые секреты. Порядок применения и перехода между режимами — [работа без почты](no-mail-accounts.md).

Образы собираются из корня проекта через основной Compose и overlay окружения; runtime env не является build argument. Проверка `config --quiet` выполняется до сборки/пересоздания. CI-развёртывание также валидирует конфигурацию до миграций. Для существующих окружений перед обновлением добавьте явный `EMAIL_ENABLED` в их private env.

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
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml config --quiet
.\scripts\check-iam.ps1 -EnvFile .env.dev
.\scripts\smoke-infra.ps1 -EnvFile .env.dev
```

Smoke проверяет gateway/web, backend health, IAM login redirect, public JWKS, изоляцию internal IAM API, PostgreSQL, MinIO и RabbitMQ.
