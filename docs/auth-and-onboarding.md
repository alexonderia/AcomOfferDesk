# Аутентификация, Регистрация И Keycloak

## Граница ответственности документа

Этот документ описывает:
- текущую рабочую модель авторизации и регистрации;
- разделение ответственности между Keycloak, backend и frontend;
- структуру Keycloak для проекта;
- актуальный режим permissions;
- операционные шаги проверки и диагностики.

Смежные документы:
- [Окружения и периметр](./environments.md)
- [Runtime-архитектура](./runtime-architecture.md)
- [Production: переменные окружения и секреты](./production-env.md)

## Краткая архитектура

- `frontend` (React SPA) выполняет login/logout и отображение UX.
- `backend` (FastAPI) является финальным enforcement-слоем бизнес-правил.
- `keycloak` является IdP/OIDC-провайдером и источником назначенных access-ролей.

Ключевой принцип:
- Keycloak отвечает на вопрос «что назначено пользователю в IAM».
- Backend отвечает на вопрос «что разрешено делать в бизнес-контексте здесь и сейчас».

## Источник истины по данным

- Источник permissions: Keycloak access token (`resource_access.<KEYCLOAK_API_CLIENT_ID>.roles`).
- Источник локального бизнес-контекста: БД backend (`users`, `profiles`, `user_auth_accounts`, связи и статусы).
- `users.id_role`:
  - остается бизнесовой ролью/типом пользователя;
  - не считается источником IAM permissions в `keycloak` режиме.
- `users.status` (`review`, `active`, `inactive`, `blacklist`) всегда проверяется backend.

## Структура Keycloak (текущая)

### Realm

- Realm: `acom-offerdesk` (настраивается через `KEYCLOAK_REALM`).

### Clients

1. `acom-web`
- Назначение: public SPA client для login/logout.
- Flow: Authorization Code + PKCE.
- Использование:
  - только браузерный OIDC поток;
  - без client secret во frontend.

2. `acom-api`
- Назначение: namespace для application roles (permissions + `app.*`).
- Использование:
  - роли попадают в `resource_access.acom-api.roles`;
  - backend извлекает и фильтрует роли.

3. `acom-admin-service`
- Назначение: backend-only client для Keycloak Admin API.
- Тип: confidential + service account.
- Использование:
  - server-to-server вызовы из backend (`ensure_user`, logout sessions и т.д.);
  - frontend не получает admin-токены.

### Роли в `acom-api`

1. Atomic permissions
- Роли с кодами из `backend/app/domain/permissions.py`:
  - `users.read`, `requests.update`, `offers.create`, и т.д.
- Эти коды считаются известными permissions в backend.

2. Composite `app.*` (текущая модель)
- `app.superadmin`
- `app.admin`
- `app.project_manager`
- `app.lead_economist`
- `app.economist`
- `app.operator`
- `app.contractor`

3. `delegation.*` (опционально, не используется в текущем bootstrap)
- Backend поддерживает парсинг ролей с префиксом `delegation.` и отдаёт их в `delegation_roles`.
- В текущем проектном bootstrap по умолчанию `delegation.*` не создаются и не назначаются.
- Если понадобится, их можно добавить вручную/скриптом как расширение.
- Роли `delegation.*` сами по себе не считаются atomic permissions: чтобы давать действия, их нужно делать composite и включать в них permission-коды из `PermissionCodes`.

## Регистрация и онбординг: текущие потоки

## 1) Login (обычный web-поток)

1. Пользователь открывает `/auth/oidc/login`.
2. Backend генерирует state + PKCE и редиректит в Keycloak.
3. Keycloak аутентифицирует пользователя.
4. Callback приходит в backend (`/api/v1/auth/callback`).
5. Backend:
  - валидирует state;
  - обменивает code на token;
  - декодирует/валидирует access token (issuer/signature/audience/azp);
  - запускает `IdentitySyncService`.
6. Backend ставит refresh cookie и возвращает пользователя в SPA.
7. SPA поднимает сессию через `/api/v1/auth/refresh`.

## 2) Первый вход и linking

`IdentitySyncService`:
- сначала ищет link в `user_auth_accounts` по `(provider=keycloak, sub)`;
- если link отсутствует:
  - пытается auto-link согласно env policy;
  - при registration flow может создать локального пользователя;
  - иначе возвращает отказ (`Local application account is not linked`).

Главный идентификатор после linking:
- Keycloak `sub` (не email, не username).

## 3) Registration flows

- Invite/email и Telegram-legacy потоки продолжают идти через callback backend.
- Внешняя ссылка не создает полноценную сессию напрямую без OIDC flow.
- Для новых contractor backend может создавать локальный аккаунт со `status=review`.

## 4) Refresh/logout

- Refresh: `/api/v1/auth/refresh` через refresh cookie.
- Logout:
  - локальная очистка cookies;
  - provider logout refresh token;
  - попытка завершить Keycloak-сессии через Admin API.

## Контракт backend -> frontend

Frontend получает авторизационные данные только от backend:
- `permissions` (отфильтрованные известные коды);
- `app_roles`;
- `delegation_roles`;
- `status`;
- `role_id` (бизнесовая локальная роль);
- resource-level `actions` на сущностях.

Frontend не принимает security-решения по raw JWT claims.

## Извлечение и фильтрация ролей в backend

- Источник: `resource_access.<KEYCLOAK_API_CLIENT_ID>.roles`.
- Нормализация:
  - пустые/невалидные строки игнорируются;
  - неизвестные роли не становятся permissions.
- Разделение:
  - `permissions` = пересечение с `PermissionCodes`;
  - `app_roles` = роли с префиксом `app.`;
  - `delegation_roles` = роли с префиксом `delegation.`.

Даже при наличии role в токене доступ по endpoint проверяется backend-политиками и бизнес-правилами.

## Режим permissions

- Legacy/local режим выбора источника permissions удален.
- Backend всегда использует роли из `resource_access.<KEYCLOAK_API_CLIENT_ID>.roles`.
- `users.id_role` остается бизнес-ролью и не используется как IAM-источник прав.

## Проверки статуса пользователя

Backend не пропускает критические действия только на основании role:
- `status=active` обязателен для защищённых действий;
- `review/inactive/blacklist` ограничиваются policy-слоем.

## Auto-link policy по окружениям

### Development

Типично:
```env
APP_ENV=development
KEYCLOAK_VERIFY_EMAIL=false
KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED=true
KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED=false
```

### Production

Типично:
```env
APP_ENV=production
KEYCLOAK_VERIFY_EMAIL=true
KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED=false
KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED=true
```

## Bootstrap и инициализация Keycloak

One-shot init:
- `docker-compose.init.yml` поднимает:
  - `keycloak_db_prepare`;
  - `keycloak_bootstrap`;
  - `keycloak_user_role_sync` (актуализирует `app.*` роли для уже связанных пользователей по `users.id_role`).

`infra/keycloak/bootstrap.sh` в текущей конфигурации:
- создает/обновляет `acom-web`, `acom-api`, `acom-admin-service`;
- создает atomic permissions и `app.*` роли;
- синхронизирует composites `app.*`;
- назначает `app.superadmin` bootstrap-пользователю;
- обеспечивает `realm-management` роли для service-account `acom-admin-service`;
- не создает `delegation.*` роли по умолчанию и не удаляет вручную созданные `delegation.*` роли.
- при `KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE=true` выполняет дополнение/выравнивание `app.*` ролей у существующих linked users.
- `keycloak_user_role_sync` изменяет только взаимоисключающие `app.*` роли по `users.id_role` и не удаляет `delegation.*` или вручную назначенные atomic permissions.

## Optional delegation roles: как добавлять при необходимости

Если потребуется `delegation.*`:
1. Добавить client roles в `acom-api` (например, `delegation.user-manager`).
2. Сделать эти роли composite и добавить в них нужные atomic permission-коды из `PermissionCodes`.
3. Назначить роли нужным пользователям или включить в нужные composites.
4. Убедиться, что токен содержит эти роли в `resource_access.<client>.roles`.
5. Backend автоматически отдаст их в `delegation_roles`.
6. Бизнес-ограничения по endpoint все равно должны оставаться в backend policy/service слое.

## Диагностика и проверки

### 0) Актуализация текущей test-ветки

Для веток, где уже есть локальные пользователи и keycloak-linking:
- в рабочем env обязательно включить `KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE=true`;
- затем запустить one-shot init (`docker-compose.init.yml`), чтобы сервис `keycloak_user_role_sync` выровнял `app.*` роли в Keycloak по `users.id_role`.

### 1) Проверка bootstrap модели Keycloak

PowerShell:
```powershell
$env:ENV_FILE=".env.prod-like"
powershell -ExecutionPolicy Bypass -File .\scripts\check-keycloak-bootstrap.ps1
```

Bash:
```bash
ENV_FILE=.env.prod-like ./scripts/check-keycloak-bootstrap.sh
```

### 2) Частая причина «пустые app_roles»

Проверьте:
- токен действительно содержит `resource_access.<KEYCLOAK_API_CLIENT_ID>.roles`;
- `KEYCLOAK_API_CLIENT_ID` совпадает в env backend и в token payload.

### 3) Проверка link между локальным пользователем и Keycloak

Проверить таблицу `user_auth_accounts` по `provider='keycloak'` и `external_subject_id`.

## Ограничения текущей реализации

- `delegation.*` не участвуют в bootstrap по умолчанию.
- Frontend не должен получать admin secret/token.
- `_links` не считаются primary контрактом authorization; основа — `permissions + actions`.

## Куда смотреть в коде

- `backend/app/api/v1/auth.py`
- `backend/app/api/dependencies.py`
- `backend/app/domain/auth_context.py`
- `backend/app/domain/permissions.py`
- `backend/app/services/keycloak_oidc.py`
- `backend/app/services/identity_sync.py`
- `backend/app/services/keycloak_admin.py`
- `web/src/app/providers/AuthProvider.tsx`

## Контракт авторизации: session vs entity

Актуальный контракт для authorization-данных между frontend и backend:

- Session endpoint (`POST /api/v1/auth/refresh`) — основной источник глобального пользовательского контекста:
  - `permissions`
  - `app_roles`
  - `delegation_roles`
  - `status`, `role_id`, `business_access`, `onboarding_state`
- Entity list/detail endpoint'ы возвращают данные сущностей и вычисленные backend-ом `actions`.
- Entity list/detail endpoint'ы не должны дублировать глобальные `permissions` рядом с `items`/`item`.

Примеры:

```json
{
  "data": {
    "permissions": ["requests.read", "offers.create"],
    "app_roles": ["app.contractor"],
    "delegation_roles": []
  }
}
```

```json
{
  "data": {
    "items": [
      {
        "request_id": 9,
        "actions": {
          "can_open_contractor_view": true,
          "can_create_offer": true
        }
      }
    ]
  }
}
```

Правило использования на frontend:
- использовать `AuthProvider.session.permissions` для видимости разделов/страниц/меню;
- использовать `item.actions` / `entity.actions` для конкретных действий на строке/карточке/объекте.

Правило безопасности:
- видимость на frontend — только UX;
- backend остается enforcement-слоем для всех защищенных endpoint'ов.

