# Аутентификация и онбординг

## Граница ответственности документа

Этот документ — единый источник по текущей модели входа, регистрации, привязки пользователей и Keycloak-интеграции.

Смежные документы:
- [Окружения и периметр](./environments.md)
- [Runtime-архитектура](./runtime-architecture.md)
- [Production: переменные окружения и секреты](./production-env.md)

## Актуальная модель входа

- Web-вход: Keycloak OIDC (Authorization Code flow).
- Backend обрабатывает callback, синхронизирует identity и связывает локального пользователя с Keycloak subject.
- Бизнес-роли и статусы остаются в локальной БД.
- Внешние email-ссылки не создают сессию напрямую: пользователь проходит обычный login flow через Keycloak.

## Первый вход и auto-link

1. Пользователь логинится в Keycloak.
2. Backend читает claims.
3. Если связка уже есть (`user_auth_accounts`) — используется она.
4. Если нет — применяется правило auto-link текущего окружения.
5. Если связь создать нельзя — callback завершается ошибкой (`not_linked`/аналог).

### Правило для development

- Обычно разрешён auto-link по username.
- Типичный контракт:

```env
APP_ENV=development
KEYCLOAK_VERIFY_EMAIL=false
KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED=true
KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED=false
```

### Правило для production

- Auto-link только по подтверждённому email (`email_verified=true`) и однозначному матчингу.
- Типичный контракт:

```env
APP_ENV=production
KEYCLOAK_VERIFY_EMAIL=true
KEYCLOAK_DEV_AUTO_LINK_BY_USERNAME_ENABLED=false
KEYCLOAK_PROD_AUTO_LINK_BY_VERIFIED_EMAIL_ENABLED=true
```

## Bootstrap superadmin

- Локальный `superadmin` подготавливается заранее.
- При первом входе пользователя `KEYCLOAK_BOOTSTRAP_APP_USERNAME` backend выполняет bootstrap-привязку.
- После этого superadmin входит по обычному OIDC-flow.

## Сотрудники

### Сотрудник создан администратором

- Создание через UI/API формирует локального пользователя и аккаунт в Keycloak.
- Первый вход идёт через `/login` и стандартный OIDC-flow.
- Далее backend завершает привязку identity.

## Контрагенты

### Контрагент создан вручную

- Создаётся локальный пользователь (роль contractor) и аккаунт в Keycloak.
- Пароль задаётся через `Forgot password` на стороне Keycloak.
- После входа backend выполняет обычную sync/link логику.

### Контрагент по invite-ссылке

- Ссылка ведёт в registration/login flow через backend + Keycloak.
- После callback backend может создать локального contractor (`review`) и связать identity.
- Дальнейший допуск определяется локальным статусом и политиками.

## Email invite links и `next`

- Email-ссылки используют модель `login -> callback -> return`.
- Параметр `next` определяет целевую страницу после успешной аутентификации.
- Verify-email endpoint подтверждает email, но не создаёт web-сессию напрямую.

## Verify email и влияние переменных

- `APP_ENV` влияет на режим поведения окружения.
- `KEYCLOAK_VERIFY_EMAIL` влияет на требования верификации в Keycloak bootstrap/realm-конфигурации.
- Для production-потока ключевое требование — подтверждённый email для production auto-link.

## Legacy Telegram

- Telegram-интеграция сохранена как legacy.
- По умолчанию отключена.
- Включается через `LEGACY_TELEGRAM_ENABLED=true` при осознанном сценарии.

## Частые ошибки

- `APP_ENV` не выставлен как production на сервере.
- Для production оставлен `start-dev` или включён dev auto-link.
- Неверный public URL/issuer (`KEYCLOAK_PUBLIC_BASE_URL`, `KEYCLOAK_ISSUER_URL`, `KC_HOSTNAME`).
- Неподтверждённый email при production auto-link.
- Неоднозначный матч одного email на несколько локальных пользователей.
- Внешние ссылки пытаются обходить обычный login flow.

## Куда смотреть в коде

- `backend/app/api/v1/auth.py`
- `backend/app/services/keycloak_oidc.py`
- `backend/app/services/identity_sync.py`
- `backend/app/api/dependencies.py`
- `web/src/app/providers/AuthProvider.tsx`
- `web/src/pages/auth/*`
