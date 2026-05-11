# Стратегия тестирования

## Зачем это нужно

В проекте используется несколько уровней проверок. Они закрывают разные риски и запускаются отдельно: быстрые тесты не требуют поднятого стенда, а проверки стенда не подменяют тесты бизнес-логики.

Что проверяем в первую очередь:
- корректность бизнес-логики;
- безопасность авторизации через Keycloak (`permissions` и `actions`);
- доступность и связность инфраструктуры;
- основные пользовательские сценарии;
- возможность запускать каждый набор проверок отдельной командой.

## Подготовка окружения

Перед запуском тестов подготовьте отдельное виртуальное окружение проекта.

Базовые требования:
- Python `3.11` или `3.12` (рекомендуется `3.12`);
- в Windows используйте PowerShell-скрипты `*.ps1`;
- для `*.sh` нужен `bash` (WSL/Git Bash/Linux/macOS).

Подготовка backend-зависимостей (PowerShell):
```powershell
cd C:\Users\alexonderia\Work\AcomOfferDesk
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -r backend\requirements.txt
pip install pytest pytest-asyncio
```

Подготовка frontend/e2e-зависимостей:
```powershell
npm --prefix web ci
npm --prefix web exec -- playwright install
```

Частые ошибки и причины:
- `No module named pytest`:
  зависимости не установлены в текущем окружении или не активирован `.venv`.
- `Failed building wheel for asyncpg/pydantic-core` на Windows:
  обычно запуск на Python `3.14`; используйте Python `3.11/3.12`.
- `./scripts/*.sh` не распознано в PowerShell:
  используйте `./scripts/*.ps1` или запускайте `*.sh` через `bash`.

## 1. Быстрые unit-тесты backend

Проверяют:
- как `CurrentUser` собирается из ролей Keycloak;
- фильтрацию неизвестных/пустых ролей Keycloak;
- что `app.*` и `delegation.*` сами по себе не становятся atomic permissions;
- что `app.superadmin` без atomic permission-кодов не дает доступ автоматически;
- как `authorization.has_permission(...)` учитывает права и статус пользователя;
- как `require_permission(...)` и `require_any_permission(...)` учитывают статусы `active/review/inactive/blacklist`;
- критичные ветки политик `RequestPolicy`, `OfferPolicy` и `UserPolicy`;
- сборку доступных действий через `RequestActionBuilder`, `OfferActionBuilder`, `ChatActionBuilder` и `UserActionBuilder`.

Как запускать:
- PowerShell: `./scripts/test-unit.ps1`
- Bash: `./scripts/test-unit.sh`

Важно:
- не требуют PostgreSQL, Keycloak, RabbitMQ или MinIO;
- должны выполняться быстро;
- подходят для частого запуска во время разработки.

## 2. Интеграционные тесты и API-контракты backend

Проверяют:
- `401` для endpoint без `Authorization` и с невалидным Bearer token;
- `403` для пользователя без нужного permission;
- статусные ограничения (`review/inactive/blacklist`) на protected действиях;
- успешный protected-path для `active` пользователя с нужными permission;
- контракт сессии авторизации: `permissions`, `app_roles`, `delegation_roles`, `status`, `role_id`, `business_access`, `onboarding_state`;
- контракты заявок: у элементов есть `actions`, а глобальные `permissions` не дублируются в ответе;
- контракт рабочего пространства оффера: `request.actions`, `offer.actions`, `chat_actions`, без глобального списка `permissions` в ответе;
- OIDC/auth edge-cases: callback без `code/state`, callback с неправильным/битым `state`, refresh без cookie, refresh с невалидной cookie, logout при недоступном Keycloak API.

Как запускать:
- PowerShell: `./scripts/test-integration.ps1`
- Bash: `./scripts/test-integration.sh`

Важно:
- эти проверки отделены от unit-тестов;
- они проверяют API backend, но не запускают браузерные сценарии.

## 3. Безопасная smoke-проверка инфраструктуры

Проверяет поднятый стенд:
- доступен ли web/gateway;
- отвечает ли `health` endpoint backend;
- проходит ли маршрут через API-прокси;
- доступна ли PostgreSQL и выполняется ли `SELECT 1`;
- доступны ли issuer и JWKS Keycloak;
- существует ли и читается ли бакет в MinIO/S3;
- устанавливается ли AMQP-соединение с RabbitMQ.

Как запускать:
- PowerShell: `./scripts/smoke-infra.ps1 -EnvFile .env.dev`
- PowerShell с другим базовым URL: `./scripts/smoke-infra.ps1 -EnvFile .env.dev -BaseUrl http://localhost:8080`
- PowerShell с явными override приватных зависимостей:
  `./scripts/smoke-infra.ps1 -EnvFile .env.prod-like -BaseUrl https://<gateway> -DatabaseUrl postgresql://... -S3Endpoint localhost:9000 -RabbitmqUrl amqp://user:pass@localhost:5672/`
- Bash: `./scripts/smoke-infra.sh .env.dev`
- Bash с override приватных зависимостей:
  `ENV_FILE=.env.prod-like BASE_URL=https://<gateway> SMOKE_DATABASE_URL=postgresql://... SMOKE_S3_ENDPOINT=localhost:9000 SMOKE_RABBITMQ_URL=amqp://user:pass@localhost:5672/ ./scripts/smoke-infra.sh`

Формат отчета:
- `[OK]` - проверка прошла;
- `[WARN]` - есть проблема, но она не считается критичной;
- `[FAIL]` - критичная проверка не прошла.

Поведение при ошибках:
- при критичных сбоях команда завершается с ненулевым кодом.

Безопасность:
- по умолчанию smoke-проверка ничего не создает и не удаляет;
- заявки и офферы не создаются;
- email не отправляются;
- разрушающие операции с очередями и хранилищем не выполняются.

Важно для запуска с хоста (вне Docker-сети):
- если в `.env` указаны внутренние DNS-имена (`minio`, `rabbitmq`, `order-database-postgres`), используйте override-параметры `-DatabaseUrl`, `-S3Endpoint`, `-RabbitmqUrl` или переменные `SMOKE_DATABASE_URL`, `SMOKE_S3_ENDPOINT`, `SMOKE_RABBITMQ_URL`;
- `DATABASE_URL` со схемой `postgresql+asyncpg://` поддерживается автоматически и приводится к формату, который понимает `asyncpg`.
- `S3_PUBLIC_ENDPOINT` из `.env` подхватывается автоматически и используется для smoke раньше, чем `S3_ENDPOINT`.

## 4. Проверка модели Keycloak

Проверяет модель Keycloak в режиме только для чтения:
- существует ли realm и включен ли он;
- совпадает ли issuer и доступен ли JWKS;
- корректно ли настроен клиент `acom-web`;
- есть ли в `acom-api` роли из `PermissionCodes`, роли `app.*` и composite-роли;
- совпадают ли backend `PermissionCodes` с ролями в Keycloak;
- что происходит с `delegation.*`: роли показываются в отчете, но не изменяются;
- настроена ли сервисная учетная запись клиента `acom-admin-service`;
- существует ли начальный superadmin и есть ли у него роль `app.superadmin`.

Как запускать:
- PowerShell: `./scripts/check-keycloak.ps1 -EnvFile .env.dev`
- PowerShell для `prod-like` стенда через публичный gateway/ngrok:
  `$env:KEYCLOAK_INTERNAL_BASE_URL='https://unflossy-noninheritable-aarav.ngrok-free.dev/iam'; ./scripts/check-keycloak.ps1 -EnvFile .env.prod-like; Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL`
- Bash: `./scripts/check-keycloak.sh .env.dev`

Строгий режим для неизвестных атомарных ролей:
- PowerShell: `./scripts/check-keycloak.ps1 -EnvFile .env.dev -StrictUnknownAtomic`
- PowerShell для `prod-like` стенда:
  `$env:KEYCLOAK_INTERNAL_BASE_URL='https://unflossy-noninheritable-aarav.ngrok-free.dev/iam'; ./scripts/check-keycloak.ps1 -EnvFile .env.prod-like -StrictUnknownAtomic; Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL`
- Bash: `STRICT_UNKNOWN_ATOMIC=true ./scripts/check-keycloak.sh .env.dev`

Важно:
- скрипт ничего не меняет в Keycloak;
- пользователи и роли не создаются, не обновляются и не удаляются;
- отсутствующие обязательные роли считаются критичной ошибкой.

## 5. E2E smoke в браузере

Проверяет основные пользовательские потоки через Playwright:
- вход через Keycloak;
- базовые сценарии заявок (`economist`, `contractor`, `superadmin`);
- ролевой доступ для всех ролей системы (`superadmin`, `admin`, `project_manager`, `lead_economist`, `economist`, `operator`, `contractor`);
- корректные редиректы при попытке открыть недоступные разделы (`/admin`, `/pm-dashboard`, `/feedback`);
- отсутствие явных ошибок в консоли во время smoke-сценариев.

Как запускать:
- PowerShell: `./scripts/e2e-smoke.ps1`
- PowerShell со строгой проверкой учетных данных: `./scripts/e2e-smoke.ps1 -StrictCredentials`
- PowerShell с временными пользователями: `./scripts/e2e-smoke.ps1 -EnvFile .env.dev -ProvisionUsers`
- Bash: `./scripts/e2e-smoke.sh`
- Bash с временными пользователями: `ENV_FILE=.env.dev PROVISION_USERS=true ./scripts/e2e-smoke.sh`

Переменные окружения для учетных данных:
- `E2E_SUPERADMIN_USERNAME`
- `E2E_SUPERADMIN_PASSWORD`
- `E2E_ADMIN_USERNAME`
- `E2E_ADMIN_PASSWORD`
- `E2E_PROJECT_MANAGER_USERNAME`
- `E2E_PROJECT_MANAGER_PASSWORD`
- `E2E_LEAD_ECONOMIST_USERNAME`
- `E2E_LEAD_ECONOMIST_PASSWORD`
- `E2E_ECONOMIST_USERNAME`
- `E2E_ECONOMIST_PASSWORD`
- `E2E_OPERATOR_USERNAME`
- `E2E_OPERATOR_PASSWORD`
- `E2E_CONTRACTOR_USERNAME`
- `E2E_CONTRACTOR_PASSWORD`

Дополнительные переменные окружения:
- `E2E_BASE_URL` - базовый адрес стенда, по умолчанию `http://localhost:8080`;
- `E2E_STRICT_CREDENTIALS=true` - падать с ошибкой, если учетные данные не заданы.

Важно:
- реальные пароли нельзя хранить в репозитории;
- e2e запускаются отдельно и не входят в unit или integration;
- эти сценарии должны оставаться легкими: цель - проверить ключевые потоки, а не каждую кнопку интерфейса;
- `-ProvisionUsers`/`PROVISION_USERS=true` создают временных пользователей `e2e_*` в Keycloak и локальной БД, назначают им роли `app.*`, запускают тесты и затем удаляют этих пользователей;
- в режиме `-ProvisionUsers` автоматически создаются пользователи всех 7 ролей `app.*`;
- если `-BaseUrl` не передан, `e2e-smoke` берет базовый URL из `WEB_BASE_URL` (или `PUBLIC_BACKEND_BASE_URL`) в выбранном env-файле;
- в режиме `-ProvisionUsers` скрипт пытается использовать локальный `KEYCLOAK_INTERNAL_BASE_URL=http://127.0.0.1:8080/iam` (если доступен), иначе использует публичный URL из env;
- режим подготовки временных пользователей изменяет стенд и поэтому включается только явно;
- временный state-файл с учетными данными создается в `.tmp/e2e` и удаляется при очистке; каталог `.tmp/` игнорируется Git.

## 6. Полная release-проверка

Запускает несколько наборов проверок одной командой.

Как запускать:
- PowerShell: `./scripts/test-release.ps1 -EnvFile .env.dev`
- PowerShell вместе с E2E: `./scripts/test-release.ps1 -EnvFile .env.dev -IncludeE2E`
- PowerShell вместе с E2E и временными пользователями: `./scripts/test-release.ps1 -EnvFile .env.dev -IncludeE2E -ProvisionE2EUsers`
- Bash: `ENV_FILE=.env.dev ./scripts/test-release.sh`
- Bash вместе с E2E: `ENV_FILE=.env.dev INCLUDE_E2E=true ./scripts/test-release.sh`
- Bash вместе с E2E и временными пользователями: `ENV_FILE=.env.dev INCLUDE_E2E=true PROVISION_E2E_USERS=true ./scripts/test-release.sh`

Порядок выполнения:
1. unit-тесты;
2. интеграционные тесты и API-контракты;
3. smoke-проверка инфраструктуры;
4. проверка модели Keycloak;
5. frontend typecheck/build;
6. e2e smoke, если он явно включен флагом.

Важно:
- e2e не запускаются по умолчанию;
- release-проверка удобна перед финальной валидацией, но отдельные наборы все равно можно запускать независимо.

## 7. CI-покрытие

Автоматически в GitHub Actions (workflow `.github/workflows/ci.yml`) на `push/pull_request` для веток `dev_process`, `dev`, `test` запускаются:
- backend unit tests;
- backend integration/API contract tests;
- frontend build.

E2E smoke запускается отдельно вручную (`workflow_dispatch`) через `.github/workflows/e2e-smoke.yml`.

## 8. Frontend unit/component тесты (статус)

Сейчас основная frontend-проверка в CI — `build` и e2e smoke.  
Минимальный следующий шаг (P1), если хотим локально поймать регрессии раньше e2e:
- добавить `Vitest + React Testing Library` только для `AuthProvider`, `ProtectedRoute`, `RoleRoute`;
- покрыть сценарии `anonymous/bootstrapping/authenticated`, `businessAccess=false`, permission-based route access.

## Когда что запускать

Рекомендуемый рабочий ритм:
1. Во время активной разработки запускать `test-unit`.
2. При изменении API backend или контрактов запускать `test-integration`.
3. На поднятом стенде запускать `smoke-infra` и `check-keycloak`.
4. Для проверки ключевых пользовательских потоков запускать `e2e-smoke`.
5. Перед финальной проверкой к релизу запускать `test-release`.

## Важные различия

- Unit и integration проверяют корректность кода и контрактов.
- Smoke-проверки проверяют доступность и связность сервисов, но не доказывают корректность бизнес-логики.
- Проверка Keycloak сверяет структуру realm, клиентов и ролей, но ничего не меняет.
- E2E smoke проверяет только основные пользовательские сценарии и не должен превращаться в тяжелую браузерную тестовую базу.
