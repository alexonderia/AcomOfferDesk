# Backend (`/backend`)

## Граница ответственности документа

Этот README описывает устройство backend-модуля.
Единый источник правды по запуску окружений и compose-слоям:
- `docs/environments.md`

Статус локальных compose-файлов в `/backend`:
- `backend/docker-compose.yml` и `backend/docker-compose.ngrok.yml` — legacy standalone-сценарии, не основной путь запуска проекта.

`backend` - основной API и бизнес-слой AcomOfferDesk. Именно здесь сосредоточены HTTP endpoints, правила доступа, orchestration бизнес-сценариев, работа с файлами, интеграция с Keycloak, отправка событий и realtime-логика чата.

## Роль модуля в системе

Backend отвечает за:

- аутентификацию и синхронизацию identity;
- управление пользователями, заявками и офферами;
- вычисление разрешенных действий для UI;
- работу с файлами и хранилищем;
- генерацию ссылок login/registration flow;
- публикацию уведомлений;
- realtime-чат в offer workspace;
- ряд фоновых внутренних задач runtime.

## Что важно знать в первую очередь

- frontend не должен сам решать, какие действия доступны пользователю; backend возвращает `actions` и `permissions`;
- вход в web-интерфейс построен через Keycloak OIDC flow;
- локальная рабочая БД находится в отдельном репозитории `order_database`;
- файловые объекты живут в `MinIO`, но доступ к ним контролирует backend;
- логика доступа строится на сочетании ролей, статусов, ownership и permission codes.

## Стек

- FastAPI
- SQLAlchemy 2
- Pydantic / pydantic-settings
- aio-pika
- MinIO SDK
- Keycloak OIDC + Admin API integration

## Архитектурная схема backend

Основной поток внутри модуля:

`API -> Service -> Repository -> DB / Infrastructure`

Дополнительно участвуют:

- `domain` для правил доступа и исключений;
- `core` для конфигурации, токенов и unit of work;
- `realtime` для websocket/chat runtime.

## Структура `app/`

```text
app/
  api/v1/            REST и WS endpoints
  services/          бизнес-слой
  repositories/      доступ к БД
  domain/            policies, permissions, exceptions, auth context
  schemas/           pydantic-контракты API
  infrastructure/    DB, email, S3, publisher
  realtime/          runtime WebSocket-чата
  core/              конфиг, токены, cookies, UoW, security
```

## Как ориентироваться по коду

### `api/v1/`

Входная точка HTTP API.

Что здесь искать:

- endpoint;
- request/response wiring;
- auth dependencies;
- вызов нужного сервиса;
- сборку response со `links`, `permissions` и `actions`.

Ключевые зоны:

- `api/v1/auth.py`
- `api/v1/users.py`
- `api/v1/requests.py`
- `api/v1/offers.py`
- `api/v1/dashboard.py`
- `api/v1/ws.py`

### `services/`

Главный слой бизнес-логики.

Ищите здесь:

- правила создания и изменения сущностей;
- orchestration между repository и внешними сервисами;
- auth/session flows;
- file handling;
- email notifications;
- identity sync;
- чат и связанные сценарии.

Особенно важные файлы:

- `services/identity_sync.py`
- `services/keycloak_oidc.py`
- `services/users.py`
- `services/requests.py`
- `services/offers.py`
- `services/files.py`
- `services/chat_realtime.py`

### `repositories/`

Слой чтения и записи в БД.

Ищите здесь:

- ORM-запросы;
- выборки для UI;
- связи между пользователями, заявками, офферами, сообщениями и файлами.

### `domain/`

Один из самых важных слоев проекта.

Содержит:

- `policies.py`
- `permissions.py`
- `authorization.py`
- `exceptions.py`
- `auth_context.py`

Если меняется доступ, права, видимость данных или условия выполнения действий, почти всегда нужно менять именно этот слой и связанный с ним `api/action_flags.py`.

### `api/action_flags.py`

Отдельная важная зона backend.

Здесь вычисляются разрешенные действия для:

- заявок;
- офферов;
- чата;
- пользователей.

Это backend-driven контракт для UI, который сильно влияет на то, какие кнопки и действия frontend показывает пользователю.

### `core/`

Базовые runtime-механизмы:

- конфиг;
- session tokens;
- auth cookies;
- OIDC state tokens;
- invite tokens;
- unit of work;
- security helpers.

### `realtime/`

Зона websocket/chat runtime.

Здесь реализованы:

- контракты событий;
- manager подключений;
- runtime публикации;
- координация realtime-потока.

## Внешние зависимости

- PostgreSQL из репозитория `order_database`
- RabbitMQ
- MinIO
- Keycloak

Все они подключаются в корневом `docker-compose.yml`.

## Как backend встроен в runtime

Через `gateway` backend доступен по пути:

- `/api/*` -> `backend:8000`

А сам `gateway` также проксирует:

- `/` -> `web`
- `/iam/*` -> `keycloak`

Практически это означает, что frontend работает через единый host и единый внешний вход.

## Ключевые потоки внутри backend

### Auth flow

Основные точки:

- `/api/v1/auth/oidc/login`
- `/api/v1/auth/oidc/register`
- `/api/v1/auth/callback`
- `/api/v1/auth/refresh`
- `/api/v1/auth/logout`

Что происходит:

1. Backend инициирует OIDC flow.
2. Обрабатывает callback.
3. Обменивает `code` на токены.
4. Синхронизирует локального пользователя через `IdentitySyncService`.
5. Отдает session context для SPA.

### Поток заявок

Ключевая зона:

- `api/v1/requests.py`
- `services/requests.py`
- `repositories/requests.py`

Сюда входят:

- создание заявки;
- изменение заявки;
- вложения;
- contractor/open/offered представления;
- email notifications;
- deleted alerts.

### Поток офферов и чата

Ключевая зона:

- `api/v1/offers.py`
- `services/offers.py`
- `services/chat_realtime.py`
- `realtime/*`

Сюда входят:

- создание оффера;
- manual offer flow;
- workspace оффера;
- файлы оффера;
- сообщения;
- read/received статусы;
- realtime-публикация событий.

### Поток пользователей

Ключевая зона:

- `api/v1/users.py`
- `services/users.py`
- `repositories/users.py`

Сюда входят:

- список пользователей;
- профиль текущего пользователя;
- subordinate profile;
- manual contractor flow;
- смена статуса;
- смена роли;
- смена менеджера;
- unavailability periods.

## Запуск

Рекомендуемый путь — запуск в составе корневого стека.

Dev:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Production-like локально:

```bash
docker compose --env-file .env.prod-like.local -f docker-compose.yml -f docker-compose.prod-like.yml up -d --build
```

API будет доступен через:

- `http://localhost:8080/api/v1/...`

## Конфигурация

Основной runtime/env-contract задается корневыми env-файлами (`.env.dev`, `.env.prod-like.local`, `.env.test`, `.env.prod`) и передается в сервисы через root compose.

`backend/.env` — legacy-артефакт и не является источником правды для основного сценария запуска.

Ключевая точка входа в коде:

- `app/core/config.py`

## На что смотреть при изменениях

### Если меняется auth

Смотрите:

- `api/v1/auth.py`
- `api/dependencies.py`
- `services/keycloak_oidc.py`
- `services/identity_sync.py`
- `core/auth_cookies.py`
- `core/oidc_state_tokens.py`

### Если меняются права доступа

Смотрите:

- `domain/policies.py`
- `domain/permissions.py`
- `domain/authorization.py`
- `api/action_flags.py`

### Если меняются файлы

Смотрите:

- `services/files.py`
- `infrastructure/minio_client.py`
- `repositories/files.py`
- соответствующие endpoints в `requests.py` и `offers.py`

### Если меняются уведомления

Смотрите:

- `services/email_notifications.py`
- `services/contractor_email_notifications.py`
- `infrastructure/notification_publisher.py`
- `notifications_worker/`

## Связанные документы

- корневой обзор: `README.md`
- общая архитектура: `docs/runtime-architecture.md`
- навигация по проекту: `docs/developer-guide.md`
- аутентификация и онбординг: `docs/auth-and-onboarding.md`
- окружения и perimeter: `docs/environments.md`
