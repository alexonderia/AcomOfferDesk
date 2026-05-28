# Каталог тестов системы

## Зачем нужен этот документ

Этот файл отвечает на вопрос: **какие тесты есть в проекте и что именно они проверяют**.

Если нужен порядок запуска и практический workflow, используйте отдельный документ:
- [Стратегия тестирования](./testing-strategy.md)

## Карта тестовых уровней

| Уровень | Где лежит | Что проверяет | Когда запускать |
|---|---|---|---|
| Backend unit | `backend/tests/unit` | Чистую бизнес-логику и правила доступа без внешних сервисов | Постоянно во время разработки backend |
| Backend integration/API contract | `backend/tests/integration` | Контракты API, коды ошибок, auth/permission enforcement | После изменений API, auth, permissions, action-флагов |
| Backend guard/compat | `backend/tests/test_*.py` (в корне) | Регрессионные и контрактные проверки по миграции ролей/permissions и схемам | При изменениях auth/Keycloak/permission-модели |
| Frontend unit/component | `web/src/app/**/*.test.tsx` | UX-логику auth-провайдеров и route-guard'ов | При изменениях маршрутов, AuthProvider, сессии |
| Browser E2E smoke | `web/e2e/*.smoke.spec.ts` | Ключевые пользовательские сценарии через реальный браузер | Перед релизом и после изменений auth/ролей |
| Infra smoke | `scripts/smoke-infra.*` + `backend/app/scripts/smoke_services.py` | Доступность и связность стенда (gateway/backend/db/keycloak/s3/rabbitmq) | На поднятом окружении перед релизом/диагностикой |
| Keycloak model checks | `scripts/check-keycloak.*` + `backend/app/scripts/check_keycloak_permission_model.py` | Корректность realm/клиентов/ролей/композитов/issuer/JWKS | Перед релизом, после изменений permission-модели |
| Aggregated release checks | `scripts/test-release.*` | Последовательный прогон unit + integration + smoke + keycloak + build (+e2e опционально) | Финальная локальная проверка |
| CI workflows | `.github/workflows/*.yml` | Автоматическая проверка в GitHub Actions | На `push` и `pull_request` |
| Legacy Telegram test | `tg_bot/tests/test_main.py` | Устойчивость polling-цикла бота к сетевым ошибкам Telegram | При изменениях `tg_bot` |

## Backend unit-тесты (`backend/tests/unit`)

### `test_auth_context_unit.py`

Проверяет сборку `CurrentUser` из ролей Keycloak:
- atomic permissions выделяются отдельно от `app.*` и `delegation.*`;
- пустые/неизвестные роли не попадают в `permissions`;
- `app.superadmin` сам по себе не превращается в список всех прав.

### `test_authorization_unit.py`

Проверяет доменную авторизацию (`has_permission`, `require_permission`, `require_any_permission`):
- `active` пользователь с правом проходит;
- без права доступ запрещается;
- `review`-contractor ограничен onboarding-safe действиями;
- `inactive` и `blacklist` блокируются даже при наличии права.

### `test_policies_unit.py`

Проверяет критические ветки policy-правил (`RequestPolicy`, `OfferPolicy`, `UserPolicy`):
- owner vs non-owner для редактирования заявки;
- ограничения contractor на работу только со своим оффером;
- обязательные permission-предпосылки;
- role-specific ограничения (например, operator не может управлять заявками даже при части прав).

### `test_action_builders_unit.py`

Проверяет сборку backend action-флагов:
- `RequestActionBuilder`, `OfferActionBuilder`, `ChatActionBuilder`, `UserActionBuilder`;
- flags соответствуют permissions + бизнес-контексту;
- contractor не получает внутренние действия (`accept/reject`, admin-like controls).

### `test_permissions_unit.py`

Проверяет набор известных permission-кодов:
- в `get_known_permissions()` есть atomic permissions;
- там нет `app.*`/`delegation.*` ролей;
- набор не пустой.

### `unit/conftest.py`

Фикстура `make_current_user`:
- создает легковесного `CurrentUser`;
- помогает писать быстрые изолированные тесты без тяжелых моков инфраструктуры.

## Backend integration/API contract (`backend/tests/integration`)

### `test_auth_enforcement_contract.py`

Проверяет enforcement на реальных route-хендлерах FastAPI:
- `401` без `Authorization`;
- `401` при невалидном bearer token;
- успешный protected-path для `active` пользователя с нужным permission;
- блокировки `review/inactive/blacklist` для защищенных действий;
- точечное исключение для `review` contractor в разрешенном onboarding-сценарии.

### `test_auth_session_contract.py`

Проверяет контракт `/api/v1/auth/refresh`:
- в ответе присутствуют `permissions`, `app_roles`, `delegation_roles`, `status`, `role_id`, `business_access`, `onboarding_state`;
- права в сессии берутся из токена/claims, а не выводятся только из локального `role_id`.

### `test_auth_oidc_flows.py`

Проверяет негативные/edge сценарии OIDC:
- callback без `code/state`;
- неверный или испорченный `state`;
- refresh без cookie или с невалидной cookie;
- logout должен очистить cookie даже если Keycloak-сервисы временно недоступны.

### `test_api_contracts.py`

Проверяет контракты ключевых API-ответов:
- в списках/деталях есть per-entity `actions`;
- глобальные `permissions` не дублируются в местах, где их быть не должно;
- поля с суммами скрываются без нужного permission;
- workspace оффера содержит `request.actions`, `offer.actions`, `chat_actions`;
- негативные authorization-сценарии возвращают `403`.

### `integration/conftest.py`

Тестовый хранилище-контур для integration:
- поднимает минимальный FastAPI app;
- использует dependency overrides для `get_current_user` и `get_uow`;
- позволяет тестировать API-контракты без живых внешних сервисов.

## Backend guard/compat тесты в корне `backend/tests`

Эти тесты дополняют unit/integration и полезны как регрессионные проверки при изменениях в auth/Keycloak/permissions.

### `test_permissions_migration.py`

Проверяет:
- разбор Keycloak JWT claims (`resource_access`) и выделение API-ролей;
- устойчивость к отсутствующим/несовпадающим `resource_access`;
- фильтрацию известных permissions;
- что dependency `require_permission(...)` реально использует доменную авторизацию.

### `test_keycloak_role_sync.py`

Проверяет синхронизацию `app.*` ролей в Keycloak:
- корректный mapping локальных `role_id -> app.*`;
- удаляются только конфликтующие `app.*` роли;
- операция идемпотентна, если нужная роль уже назначена;
- целевая роль корректно резолвится перед синком.

### `test_response_permissions_contract.py`

Проверяет контракт схем response-моделей:
- где `permissions` должны присутствовать (например, auth session, `me`);
- где `permissions` должны отсутствовать (списки заявок/пользователей).

### `backend/tests/conftest.py`

Глобальный bootstrap env для тестов backend:
- задает безопасные дефолты env-переменных;
- убирает зависимость от локальных секретов/`.env`.

## Frontend unit/component тесты (`web/src/app/**/*.test.tsx`)

### `AuthProvider.test.tsx`

Проверяет:
- bootstrap authenticated-сессии через `refreshWebSession`;
- fallback в `anonymous`, если refresh упал;
- сохранение полей `business_access` и `onboarding_state` из backend-сессии.

### `ProtectedRoute.test.tsx`

Проверяет route-guard:
- `anonymous -> /login`;
- `businessAccess=false -> /account`;
- happy-path для authenticated пользователя;
- отображение loader в статусе `bootstrapping`.

### `RoleRoute.test.tsx`

Проверяет permission-based роутинг:
- без сессии редирект на `/login`;
- без business access редирект на `/account`;
- с нужным permission доступ разрешен;
- без permission редирект на роль-специфичный default-path.

Важно: это UX-проверки фронта, не финальное security-enforcement. Финальная авторизация всегда на backend.

## Browser E2E smoke (`web/e2e/*.smoke.spec.ts`)

### `auth.smoke.spec.ts`

Проверяет базовый login/logout сценарий через Keycloak.

### `requests.smoke.spec.ts`

Проверяет smoke-потоки для ключевых ролей:
- economist: открытие `/requests` + отсутствие критичных ошибок консоли;
- contractor: переходы по contractor-маршрутам заявок;
- superadmin: доступ к `/admin`.

### `roles.smoke.spec.ts`

Проверяет матрицу доступа по ролям (`superadmin/admin/project_manager/lead_economist/economist/operator/contractor`):
- доступность `/admin`, `/pm-dashboard`, `/feedback`;
- корректные редиректы при запрете маршрута.

### `web/e2e/helpers.ts`

Вспомогательная логика:
- безопасное чтение кредов из env;
- вход через Keycloak UI;
- общие шаги logout и ожиданий.

## Инфраструктурные и системные smoke/check скрипты

### `scripts/smoke-infra.ps1` / `scripts/smoke-infra.sh`

Запускают `backend/app/scripts/smoke_services.py`, который проверяет:
- доступность gateway/web root;
- backend health endpoint;
- API proxy маршрут;
- доступность `/iam`;
- подключение к PostgreSQL + `SELECT 1` + наличие критичных таблиц;
- issuer/JWKS Keycloak;
- доступность bucket в MinIO/S3;
- AMQP-подключение к RabbitMQ.

Скрипт не создает и не удаляет данные (non-destructive smoke).

### `scripts/check-keycloak.ps1` / `scripts/check-keycloak.sh`

Запускают `backend/app/scripts/check_keycloak_permission_model.py` **на хосте** с env-файлом из репозитория (например `.env.dev`).

На **VPS** с уже поднятым контейнером `backend` используйте не `check-keycloak.sh`, а `./scripts/run-keycloak-check-backend.sh` или `./scripts/post-deploy-verify.sh` (env с хоста `backend/.env` → compose → снимок в контейнере). Путь `/app/backend/.env` внутри образа отсутствует.

Скрипт проверяет:
- realm и его enabled-состояние;
- соответствие issuer и доступность JWKS;
- настройки клиента `acom-web`;
- наличие и корректность ролей в `acom-api`;
- соответствие `PermissionCodes` ролям Keycloak;
- composite-состав `app.superadmin`;
- наличие/структуру `delegation.*`;
- настройки `acom-admin-service` и service-account ролей;
- наличие bootstrap superadmin и роли `app.superadmin`.

Скрипт read-only: не изменяет Keycloak.

### `scripts/e2e-smoke.ps1` / `scripts/e2e-smoke.sh`

Запускают Playwright smoke (`@smoke`) и поддерживают режимы:
- обычный прогон с существующими кредами;
- strict credentials;
- временный provisioning пользователей (`app.scripts.e2e_provision_users`), запуск и последующий cleanup.

## Агрегированные проверки

### `scripts/test-unit.*`

Команда на backend unit (`pytest backend/tests/unit -q`).

### `scripts/test-integration.*`

Команда на backend integration (`pytest backend/tests/integration -q`).

### `scripts/test-release.*`

Последовательно запускает:
1. backend unit;
2. backend integration/API contract;
3. infra smoke;
4. keycloak model check;
5. frontend build.

Опционально `IncludeE2E/INCLUDE_E2E=true` добавляет e2e smoke как шаг 6.

## CI и ручные workflows

### Автоматический CI (`.github/workflows/ci.yml`)

На `push/pull_request` в `dev_process`, `dev`, `test`:
- backend unit;
- backend integration;
- frontend lint;
- frontend unit;
- frontend build.

### Manual E2E (`.github/workflows/e2e-smoke.yml`)

Ручной запуск browser smoke с параметрами:
- `env_file`, `base_url`, `strict_credentials`;
- `provision_users` (по умолчанию `true`), `keep_provisioned_users`.

### Manual Release Smoke (`.github/workflows/release-smoke.yml`)

Ручной запуск для стенда:
- infra smoke;
- keycloak model check;
- опционально e2e smoke.

## Legacy Telegram test

### `tg_bot/tests/test_main.py`

Проверяет устойчивость `run_bot`:
- при `TelegramNetworkError` polling перезапускается;
- корректно закрываются сессии;
- выполняется retry-пауза.

Этот тест важен, потому что legacy Telegram функциональность в проекте сохраняется.

## Что не покрывается полностью

- Unit и integration не доказывают доступность внешней инфраструктуры стенда.
- Smoke-инфраструктура не проверяет глубоко бизнес-логику.
- Frontend unit проверяет UX-поведение, но не заменяет backend authorization enforcement.
- E2E smoke покрывает только критичный минимум сценариев, а не весь UI.
