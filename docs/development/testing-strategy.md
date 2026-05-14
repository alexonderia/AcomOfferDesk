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
- request-email-verification без реальной отправки email: fake transport, повторный запрос/dedup, duplicate email conflict, review contractor allow и non-contractor/inactive deny;
- `/auth/verify-email`: valid token, repeated verification, invalid token, expired token, wrong-flow token and email-conflict token;
- контракт сессии авторизации: `permissions`, `app_roles`, `delegation_roles`, `status`, `role_id`, `business_access`, `onboarding_state`;
- контракты заявок: у элементов есть `actions`, а глобальные `permissions` не дублируются в ответе;
- контракт рабочего пространства оффера: `request.actions`, `offer.actions`, `chat_actions`, без глобального списка `permissions` в ответе;
- OIDC/auth callback paths: negative (`code/state` missing, wrong/broken `state`, invite mismatch, already-registered invite) и positive callback path (валидный `state`, успешный sync/link, refresh cookie, SPA redirect);
- invite registration callback success: matching email + `allow_user_creation=true` + contractor `review` onboarding path на service/API уровне через fakes;
- refresh session contract и token-lifecycle: refresh без cookie, refresh с невалидной/устаревшей cookie (`401` + clear cookie), rotation/repeated refresh consistency;
- logout behavior: idempotent logout без cookie, повторный logout, битый bearer и очистка local cookies даже при provider/admin API failures.

Как запускать:
- PowerShell: `./scripts/test-integration.ps1`
- Bash: `./scripts/test-integration.sh`

Важно:
- эти проверки отделены от unit-тестов;
- они проверяют API backend, но не запускают браузерные сценарии.
- positive/negative auth callback/refresh/logout scenarios в integration используют monkeypatch/fake services/stubs и не подключаются к реальному Keycloak.

Актуальные integration suites по P0 backend coverage:
- `backend/tests/integration/test_request_lifecycle_integration.py`
- `backend/tests/integration/test_offer_lifecycle_integration.py`
- `backend/tests/integration/test_chat_endpoints_integration.py`
- `backend/tests/integration/test_admin_users_enforcement_integration.py`

Актуальная P1 contract suite (existing API surface):
- `backend/tests/integration/test_p1_backend_contract_gaps_integration.py`:
  dashboard (`/dashboard/responsibility`, `/plans*`), request/offer files upload-delete-download matrix,
  feedback create/list validation, normative files upload paths, manual request email notification endpoint,
  и verify-email lifecycle без реального SMTP/S3/Keycloak.

Что важно для этих suites:
- не подключаться к реальному Keycloak;
- не отправлять реальные email;
- сохранять backend как final enforcement слой для permissions/actions;
- DB-trigger-зависимые сценарии (например auto-reject sibling offers) не маскировать ложным green и не эмулировать в fake repositories; фиксировать как external DB contract boundary.

### DB-trigger contract boundary: auto-reject sibling offers

- Текущее состояние:
  - AcomOfferDesk intentionally не содержит in-memory integration теста, который утверждает auto-reject sibling offers.
  - `backend/tests/integration` покрывает только backend responsibility вокруг accept offer: permissions/forbidden/anonymous, guard по request status и update целевого offer.
- Почему не переводим в green в integration:
  - текущий `backend/tests/integration` контур использует fake UoW/repositories и не исполняет PostgreSQL trigger'ы.
- Как получить настоящий green:
  - запускать отдельный DB-backed contract контур в test suite репозитория `order_database` (stage/VPS или выделенная test DB со схемой/trigger'ами из `order_database`);
  - проверять эффект после `PATCH /api/v1/offers/{id}/status` в `accepted`: sibling submitted offers в БД становятся `rejected`.
- Почему это не часть обычного CI:
  - CI этого репозитория не поднимает и не мигрирует внешний `order_database`, поэтому DB-trigger проверка должна жить вне стандартного `backend/tests/integration -q` прогона.

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
- PowerShell с хоста (рекомендуется для локального стенда Docker):  
  `$env:KEYCLOAK_INTERNAL_BASE_URL='http://127.0.0.1:8080/iam'; ./scripts/check-keycloak.ps1 -EnvFile .env.dev; Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL`
- PowerShell для `prod-like` стенда через публичный gateway/ngrok:
  `$env:KEYCLOAK_INTERNAL_BASE_URL='https://unflossy-noninheritable-aarav.ngrok-free.dev/iam'; ./scripts/check-keycloak.ps1 -EnvFile .env.prod-like; Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL`
- Bash: `./scripts/check-keycloak.sh .env.dev`

Строгий режим для неизвестных атомарных ролей:
- PowerShell: `./scripts/check-keycloak.ps1 -EnvFile .env.dev -StrictUnknownAtomic`
- PowerShell с хоста (локальный стенд Docker):  
  `$env:KEYCLOAK_INTERNAL_BASE_URL='http://127.0.0.1:8080/iam'; ./scripts/check-keycloak.ps1 -EnvFile .env.dev -StrictUnknownAtomic; Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL`
- PowerShell для `prod-like` стенда:
  `$env:KEYCLOAK_INTERNAL_BASE_URL='https://unflossy-noninheritable-aarav.ngrok-free.dev/iam'; ./scripts/check-keycloak.ps1 -EnvFile .env.prod-like -StrictUnknownAtomic; Remove-Item Env:KEYCLOAK_INTERNAL_BASE_URL`
- Bash: `STRICT_UNKNOWN_ATOMIC=true ./scripts/check-keycloak.sh .env.dev`

Важно:
- скрипт ничего не меняет в Keycloak;
- пользователи и роли не создаются, не обновляются и не удаляются;
- отсутствующие обязательные роли считаются критичной ошибкой.
- `KEYCLOAK_INTERNAL_BASE_URL=http://keycloak:8080/iam` работает только внутри Docker-сети; при запуске скрипта с хоста обычно нужен `http://127.0.0.1:8080/iam` или публичный URL стенда.

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
- в manual GitHub workflow `E2E Smoke (Manual)` временные пользователи включены по умолчанию (`provision_users=true`);
- в manual GitHub workflow `Release Smoke (Manual)` временные пользователи для e2e также включены по умолчанию (`provision_e2e_users=true`).

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
5. frontend lint;
6. frontend unit/component tests;
7. frontend typecheck/build;
8. e2e smoke, если он явно включен флагом.

Важно:
- e2e не запускаются по умолчанию;
- при включении e2e в `test-release` временные пользователи включаются по умолчанию (можно выключить только явной настройкой в параметрах запуска/окружении);
- release-проверка удобна перед финальной валидацией, но отдельные наборы все равно можно запускать независимо.

## 7. CI-покрытие

Автоматически в GitHub Actions (workflow `.github/workflows/ci.yml`) на `push/pull_request` для веток `dev_process`, `dev`, `test` запускаются:
- backend unit tests;
- backend integration/API contract tests;
- frontend lint (`npm --prefix web run lint`);
- frontend unit/component tests (`npm --prefix web run test:unit`);
- frontend build.

E2E smoke запускается отдельно вручную (`workflow_dispatch`) через `.github/workflows/e2e-smoke.yml`.

## 8. Frontend unit/component тесты

Добавлены `Vitest + React Testing Library + jsdom` для auth/route/page UX-обвязки:
- `web/src/app/providers/AuthProvider.test.tsx`;
- `web/src/app/routes/ProtectedRoute.test.tsx`;
- `web/src/app/routes/RoleRoute.test.tsx`.
- `web/src/pages/offers/OfferWorkspacePage.test.tsx`;
- `web/src/pages/requests/ContractorRequestDetailsPage.test.tsx`;
- `web/src/features/request-details/ui/RequestDetailsView.test.tsx`;
- `web/src/features/offer-workspace/ui/OfferWorkspaceView.test.tsx`;
- `web/src/features/dashboard/components/ProjectManagerDashboard.test.tsx`;
- `web/src/features/dashboard/components/ProjectManagerSavingsDashboard.test.tsx`;
- `web/src/features/dashboard/components/ProjectManagerPlanDashboard.test.tsx`.

Что покрыто:
- `AuthProvider` bootstrap в состояния `authenticated` и `anonymous`;
- сохранение backend-полей `business_access` и `onboarding_state` в frontend session;
- refresh failure/stale token fallback в `anonymous`, dedup repeated refresh, logout cleanup, explicit `beginLogin(nextPath)` target;
- `ProtectedRoute`: table-driven `anonymous -> /login`, `businessAccess=false -> /account`, и happy-path для `/requests`, `/requests/:id/contractor`, `/offers/:id/workspace`;
- `RoleRoute`: table-driven permission-gated access для `/admin`, `/feedback`, `/pm-dashboard`, `/pm-dashboard/savings`, `/pm-dashboard/plan`;
- page-level guards для contractor-view/workspace routes;
- action-driven CTA visibility по backend `actions` (requests/offers/chat/files/email controls);
- dashboard widget states (`loading/empty/error`) и safe render без `NaN/Infinity/undefined`.

Локальный запуск:
- `npm --prefix web run test:unit` (или `npm --prefix web run test`).

Ограничение:
- frontend tests проверяют только UX-поведение и не являются security-enforcement;
- финальное решение по доступу остается на backend.
- deep-link preservation в guard redirect (`/login?next=...`) пока остается documented/manual gap до отдельного продуктового решения.

## 9. Manual release-smoke workflow

Добавлен ручной workflow `.github/workflows/release-smoke.yml` (`workflow_dispatch`):
- всегда запускает `scripts/smoke-infra.sh` и `scripts/check-keycloak.sh`;
- опционально запускает `scripts/e2e-smoke.sh`, только если `include_e2e=true`;
- e2e credentials берутся только из GitHub Secrets;
- smoke/keycloak шаги рассчитаны на уже поднятый стенд и валидный `env_file`.

## Когда что запускать

Рекомендуемый рабочий ритм:
1. Во время активной разработки запускать `test-unit`.
2. При изменении API backend или контрактов запускать `test-integration`.
3. Во frontend-потоках запускать `npm --prefix web run lint` и `npm --prefix web run test:unit`.
4. На поднятом стенде запускать `smoke-infra` и `check-keycloak`.
5. Для проверки ключевых пользовательских потоков запускать `e2e-smoke`.
6. Перед финальной проверкой к релизу запускать `test-release` и/или `release-smoke` workflow.

## Важные различия

- Unit и integration проверяют корректность кода и контрактов.
- Smoke-проверки проверяют доступность и связность сервисов, но не доказывают корректность бизнес-логики.
- Проверка Keycloak сверяет структуру realm, клиентов и ролей, но ничего не меняет.
- E2E smoke проверяет только основные пользовательские сценарии и не должен превращаться в тяжелую браузерную тестовую базу.

## 10. Email-уведомления: политика тестирования

Что покрыто автоматизированно:
- unit: генерация payload для email (`subject`, `text`, `html`, ссылки, fallback, экранирование, предупреждения по вложениям, UTF-8/кириллица);
- integration: постановка email-событий в outbox/fake transport для сценариев request/invite, валидация email и дедупликация получателей;
- integration: request-email-verification и `/auth/verify-email` используют fake transport/profile repo, не подключаются к SMTP/RabbitMQ и покрывают token lifecycle;
- unit: `notifications_worker` (валидный/невалидный payload, обязательные поля, дедупликация/cooldown, обработка SMTP-ошибок).

Правила безопасности:
- в тестах и CI запрещено использовать реальные SMTP credentials;
- в тестах использовать только fake/in-memory transport или monkeypatch publisher;
- тесты не должны подключаться к реальному RabbitMQ/SMTP и не должны отправлять письма наружу.

Рекомендация для smoke-проверки (P1):
- если в среде нет `MailHog`/`Mailpit`, не внедрять тяжелую инфраструктуру только ради этого;
- для dev/test рекомендована легкая mailbox smoke-проверка через `MailHog`/`Mailpit`, чтобы проверять фактическое попадание письма в тестовый inbox.

## 11. Frontend-тесты навигации/страниц и расширенные e2e-теги

Покрытие frontend unit/component теперь дополнительно включает:
- проверки ролевой конфигурации навигации (`buildHeaderConfig`) для `superadmin`, `economist`, `operator`, `contractor`;
- проверки видимости dashboard/admin на основе backend permissions;
- явную защиту от того, что `RoleRoute` даст доступ по сырым claims `app_roles`/`delegation_roles` без нужных permissions;
- UX-состояния заявок: `loading`, `empty`, `error`;
- action-driven visibility/disabled-state для критичных CTA в request/offer/workspace;
- route-level regression tests для contractor-view/workspace paths;
- dashboard widget states (`loading`, `empty`, `error`) и numeric rendering guards.

Новые Playwright-теги для расширенных/ручных сценариев:
- `@roles` - матрица доступа ролей к страницам для всех 7 ролей с проверками разрешенных/запрещенных маршрутов и защитой от ошибок в консоли;
- `@registration` - поток регистрации по приглашению (ручной, зависит от стенда);
- `@request-offer` - межролевой поток заявка -> оффер -> рабочее пространство -> переход статуса;
- `@dashboard` - страницы PM/LE dashboard, доступность маршрутов, поведение фильтров, защита от NaN/undefined, проверки пустых состояний;
- `@files-chat` - взаимодействия с файлами/чатом в рабочем пространстве и запрет доступа к workspace для роли без доступа.

Политика запуска:
- smoke по умолчанию остается легким и запускает только `@smoke`;
- CI (`.github/workflows/ci.yml`) по-прежнему запускает только backend unit/integration и frontend lint/unit/build;
- браузерный smoke и расширенные e2e запускаются вручную (`scripts/e2e-smoke.*`, ручные workflows, ручные npm-команды `e2e:*`).

## 12. Актуальная карта команд

PowerShell:
- backend unit: `./scripts/test-unit.ps1`
- backend integration/API contracts: `./scripts/test-integration.ps1`
- smoke infra: `./scripts/smoke-infra.ps1 -EnvFile .env.dev`
- Keycloak model check: `./scripts/check-keycloak.ps1 -EnvFile .env.dev`
- e2e smoke: `./scripts/e2e-smoke.ps1 -EnvFile .env.dev -ProvisionUsers`
- release gate без e2e: `./scripts/test-release.ps1 -EnvFile .env.dev`
- release gate с e2e: `./scripts/test-release.ps1 -EnvFile .env.dev -IncludeE2E -ProvisionE2EUsers`

Bash:
- backend unit: `./scripts/test-unit.sh`
- backend integration/API contracts: `./scripts/test-integration.sh`
- smoke infra: `./scripts/smoke-infra.sh .env.dev`
- Keycloak model check: `./scripts/check-keycloak.sh .env.dev`
- e2e smoke: `ENV_FILE=.env.dev PROVISION_USERS=true ./scripts/e2e-smoke.sh`
- release gate без e2e: `ENV_FILE=.env.dev ./scripts/test-release.sh`
- release gate с e2e: `ENV_FILE=.env.dev INCLUDE_E2E=true PROVISION_E2E_USERS=true ./scripts/test-release.sh`

Frontend npm:
- lint: `npm --prefix web run lint`
- unit/component: `npm --prefix web run test:unit`
- build: `npm --prefix web run build`
- e2e smoke: `npm --prefix web run e2e:smoke`
- extended e2e: `npm --prefix web run e2e:roles`, `npm --prefix web run e2e:registration`, `npm --prefix web run e2e:request-offer`, `npm --prefix web run e2e:dashboard`, `npm --prefix web run e2e:files-chat`, `npm --prefix web run e2e:extended`

## 13. Что запускается автоматически и вручную

CI (`.github/workflows/ci.yml`) на `push/pull_request` в `dev_process`, `dev`, `test`:
- `python -m pytest backend/tests/unit -q`;
- `python -m pytest backend/tests/integration -q`;
- `npm --prefix web run lint`;
- `npm --prefix web run test:unit`;
- `npm --prefix web run build`.

Вручную на поднятом стенде:
- `smoke-infra` проверяет web/gateway, backend health, API proxy, PostgreSQL, Keycloak issuer/JWKS, S3/MinIO и RabbitMQ;
- `check-keycloak` сверяет realm, clients, service account, atomic permissions, `app.*` и optional `delegation.*`;
- `e2e-smoke` запускает легкие `@smoke` browser-сценарии;
- `release-smoke` workflow запускает обязательные `smoke-infra` + `check-keycloak` и optional e2e через `include_e2e=true`;
- extended e2e теги запускаются отдельно по риску релиза, а не как часть default smoke.
