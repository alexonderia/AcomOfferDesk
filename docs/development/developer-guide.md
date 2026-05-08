# Навигация для разработчика

## Граница ответственности документа

Этот документ — навигация по кодовой базе и слоям приложения.

Смежные документы:
- [Обзор продукта](./project-overview.md)
- [Runtime-архитектура](./runtime-architecture.md)
- [Аутентификация и онбординг](./auth-and-onboarding.md)
- [Окружения](./environments.md)

## Зачем нужен этот документ

Этот файл помогает быстро сориентироваться в кодовой базе и понять:

- где лежит нужная функциональность;
- через какие слои проходит информация;
- где искать точки чтения, изменения и доставки данных;
- какие технологии и архитектурные принципы используются в проекте.

## Быстрая карта репозитория

```text
backend/               Backend API и бизнес-логика
web/                   Frontend SPA
notifications_worker/  Фоновая отправка уведомлений
tg_bot/                Legacy Telegram-интеграция
infra/keycloak/        Конфигурация и bootstrap Keycloak
docs/                  Документация
scripts/               Вспомогательные скрипты
shared/                Общие runtime-артефакты
```

## Как ориентироваться по backend

### Главная мысль

Backend в основном организован по схеме:

`API -> Service -> Repository -> DB/Infrastructure`

Дополнительно есть `domain`-слой для правил доступа и исключений.

## Структура `backend/app`

### `api/`

Точка входа HTTP API.

Что здесь искать:

- объявление endpoint;
- тип входного payload;
- тип выходного response;
- wiring зависимостей;
- вызов нужного сервиса.

Ключевые файлы:

- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/users.py`
- `backend/app/api/v1/requests.py`
- `backend/app/api/v1/offers.py`
- `backend/app/api/v1/dashboard.py`
- `backend/app/api/v1/ws.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/action_flags.py`

### `services/`

Бизнес-логика.

Ищите здесь:

- правила изменения сущностей;
- orchestration между repository и infrastructure;
- compose бизнес-сценариев;
- побочные эффекты вроде уведомлений, синхронизации и загрузки файлов.

Типовые сервисы:

- `services/auth.py`
- `services/auth_session.py`
- `services/identity_sync.py`
- `services/keycloak_oidc.py`
- `services/users.py`
- `services/requests.py`
- `services/offers.py`
- `services/chat_realtime.py`
- `services/files.py`
- `services/email_notifications.py`

### `repositories/`

Слой доступа к данным.

Ищите здесь:

- SQL/ORM-запросы;
- чтение и изменение таблиц;
- выборки для экранов и списков;
- привязку файлов, чатов, сообщений и пользователей.

Если нужно понять, откуда берутся данные для страницы или действия, почти всегда надо посмотреть соответствующий repository после service-слоя.

### `schemas/`

Контракты API.

Ищите здесь:

- request payload;
- response payload;
- вложенные схемы сущностей;
- формат данных, который frontend реально получает.

### `domain/`

Предметные ограничения и правила доступа.

Ключевые файлы:

- `domain/policies.py`
- `domain/permissions.py`
- `domain/authorization.py`
- `domain/exceptions.py`
- `domain/auth_context.py`

Это обязательное место для изучения, если вы меняете права, доступность кнопок, видимость сущностей или условия выполнения операций.

### `core/`

Базовые механизмы runtime.

Здесь находятся:

- конфигурация;
- токены и cookies;
- unit of work;
- security helpers;
- служебные генераторы state / invite / session токенов.

Полезные файлы:

- `core/config.py`
- `core/uow.py`
- `core/session_tokens.py`
- `core/auth_cookies.py`
- `core/oidc_state_tokens.py`
- `core/registration_invite_tokens.py`

### `infrastructure/`

Интеграции с внешними сервисами.

Примеры:

- DB engine;
- email transport;
- notification publisher;
- MinIO client.

### `realtime/`

Runtime веб-сокетного чата.

Ищите здесь:

- менеджер подключений;
- runtime pub/sub;
- контракты realtime-событий.

## Как ориентироваться по frontend

### Главная мысль

Frontend организован по feature-oriented структуре. Искать код лучше не "по технологии", а "по пользовательскому сценарию".

## Структура `web/src`

### `app/`

Каркас приложения.

Здесь лежат:

- корневой `App`;
- providers;
- маршрутизация;
- layout;
- guard-компоненты.

Ключевые файлы:

- `web/src/app/App.tsx`
- `web/src/app/routes/AppRoutes.tsx`
- `web/src/app/routes/ProtectedRoute.tsx`
- `web/src/app/providers/AuthProvider.tsx`
- `web/src/app/providers/ChatRealtimeProvider.tsx`

### `pages/`

Страницы как точки входа маршрутов.

Если вы знаете URL, почти всегда начинайте отсюда.

Примеры:

- `pages/auth/*`
- `pages/requests/*`
- `pages/offers/*`
- `pages/admin/*`
- `pages/dashboard/*`

### `features/`

Основная прикладная логика интерфейса.

Именно здесь обычно живут:

- составные UI-блоки;
- page hooks;
- form orchestration;
- прикладные вычисления для экранов.

Примеры:

- `features/requests/*`
- `features/request-details/*`
- `features/offer-workspace/*`
- `features/admin/*`
- `features/dashboard/*`
- `features/header/*`

### `entities/`

Доменные типы и более "чистые" представления сущностей.

Обычно это хороший слой для понимания предметной модели frontend.

### `shared/`

Общий фундамент фронтенда.

Здесь лежат:

- API-функции;
- UI-компоненты общего назначения;
- утилиты;
- константы ролей;
- тема;
- WebSocket client.

Если нужно понять, как фронтенд получает или отправляет данные, первым делом смотрите:

- `web/src/shared/api/*`
- `web/src/shared/ws/*`

## Как движется информация по системе

## 1. HTTP API поток

Наиболее частый сценарий:

1. Пользователь взаимодействует со страницей в `pages/`.
2. Feature-hook или UI-компонент вызывает функцию из `shared/api/`.
3. Запрос уходит в backend endpoint из `api/v1/`.
4. Endpoint вызывает сервис.
5. Сервис читает/меняет данные через repository.
6. Backend возвращает schema response.
7. Frontend преобразует и отображает результат.

## 2. Поток аутентификации

1. `AuthProvider` и auth-страницы инициируют вход.
2. Backend auth endpoints запускают OIDC flow.
3. Keycloak отдает callback.
4. Backend синхронизирует identity.
5. Frontend восстанавливает сессию через refresh endpoint.

Где искать:

- frontend: `web/src/app/providers/AuthProvider.tsx`, `web/src/pages/auth/*`
- backend: `backend/app/api/v1/auth.py`, `backend/app/services/keycloak_oidc.py`, `backend/app/services/identity_sync.py`

## 3. Файловый поток

1. Пользователь загружает файл.
2. Frontend отправляет multipart/form-data.
3. Backend валидирует upload через `FileService`.
4. Файл сохраняется в MinIO.
5. В БД создается метадата.
6. Скачивание всегда идет через backend download endpoint, а не напрямую из хранилища.

Где искать:

- `backend/app/services/files.py`
- `backend/app/infrastructure/minio_client.py`
- `backend/app/api/v1/requests.py`
- `backend/app/api/v1/offers.py`

## 4. Чат и realtime

1. Сообщение сохраняется через backend endpoint.
2. Backend публикует realtime event.
3. Клиенты получают событие через websocket runtime.
4. Отдельно обновляются delivery/read статусы.

Где искать:

- backend: `backend/app/services/chat_realtime.py`, `backend/app/realtime/*`, `backend/app/api/v1/offers.py`
- frontend: `web/src/app/providers/ChatRealtimeProvider.tsx`, `web/src/shared/ws/chatSocket.ts`, `web/src/features/offer-workspace/*`

## Как backend сообщает frontend, что можно делать

Одна из важных особенностей проекта - backend возвращает не только данные, но и `actions`.

Примеры:

- `RequestActionsSchema`
- `OfferActionsSchema`
- `ChatActionsSchema`
- `UserActionsSchema`

Практический смысл:

- frontend не кодирует правила доступа самостоятельно;
- backend централизованно решает, какие действия доступны;
- UI рендерит кнопки и формы исходя из уже посчитанных флагов.

Если в интерфейсе "пропала" или "не появилась" кнопка, почти всегда нужно смотреть:

- `backend/app/api/action_flags.py`
- `backend/app/domain/policies.py`
- `backend/app/domain/permissions.py`

## Как искать нужное изменение

### Нужно изменить страницу или кнопку

Смотрите:

1. `web/src/pages/...`
2. `web/src/features/...`
3. `web/src/shared/api/...`
4. backend endpoint, который дергает эта кнопка

### Нужно изменить ответ API

Смотрите:

1. `backend/app/api/v1/...`
2. `backend/app/schemas/...`
3. `backend/app/services/...`
4. `backend/app/repositories/...`

### Нужно изменить бизнес-правила доступа

Смотрите:

1. `backend/app/domain/policies.py`
2. `backend/app/domain/permissions.py`
3. `backend/app/api/action_flags.py`
4. frontend-компонент, который использует `actions`

### Нужно изменить auth

Смотрите:

1. `backend/app/api/v1/auth.py`
2. `backend/app/services/keycloak_oidc.py`
3. `backend/app/services/identity_sync.py`
4. `backend/app/api/dependencies.py`
5. `web/src/app/providers/AuthProvider.tsx`
6. `web/src/pages/auth/*`

### Нужно изменить создание пользователей или контрагентов

Смотрите:

1. `backend/app/api/v1/users.py`
2. `backend/app/services/users.py`
3. `web/src/features/admin/*`
4. `web/src/shared/api/users/*`

## Что важно помнить при изменениях

### 1. В проекте много cross-layer связей

Изменение одного поля часто требует правок сразу в нескольких местах:

- schema backend;
- service;
- repository;
- frontend types;
- frontend API mapper;
- UI feature/page.

### 2. Права завязаны не только на роль

Нужно проверять одновременно:

- роль;
- статус;
- permission code;
- ownership;
- context конкретной сущности.

### 3. Аутентификация и онбординг тесно связаны с документацией

При изменениях в auth, login-links, регистрации или роли/статусах нужно синхронизировать:

- `README.md`
- `docs/auth-and-onboarding.md`

### 4. БД не в этом репозитории

Если кажется, что "код правильный, а данные странные", обязательно проверьте состояние `order_database`.

## Рекомендуемая последовательность чтения для нового разработчика

1. `README.md`
2. `docs/project-overview.md`
3. `docs/runtime-architecture.md`
4. `backend/REAME.md`
5. `web/README.md`
6. конкретные `api`, `services`, `features` по вашему сценарию

## Связанные документы

- [Обзор проекта](project-overview.md)
- [Архитектура и потоки данных](runtime-architecture.md)
- [Аутентификация и онбординг](auth-and-onboarding.md)
<!-- run-scenarios-source-of-truth-2026-04-29 -->
## Единый источник по окружениям

Единые команды запуска для `dev`, `test`, `prod`, `prod-like`, а также проверки `docker compose ... config` и init-сценарии описаны в:
- [environments.md](./environments.md)

Если меняется compose/env-контракт, сначала обновляйте `environments.md`, а затем синхронизируйте ссылки на него.
