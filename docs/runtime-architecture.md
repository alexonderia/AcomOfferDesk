# Архитектура и потоки данных

## Граница ответственности документа

Этот документ описывает runtime-слой: контейнеры, интеграции, потоки данных и границы между сервисами.

Смежные документы:
- [Окружения и периметр](./environments.md)
- [Навигация по коду](./developer-guide.md)
- [Аутентификация и онбординг](./auth-and-onboarding.md)

## Общая схема runtime

```text
Browser
   |
   v
gateway (Nginx)
  |-- /            -> web
  |-- /api/*       -> backend
  |-- /iam/*       -> keycloak

backend
  |-- PostgreSQL (external order_database)
  |-- RabbitMQ
  |-- MinIO
  |-- Chat realtime runtime
  |-- Email / mailbox integrations

notifications_worker
  `-- RabbitMQ

tg_bot (legacy, optional)
  `-- backend / gateway
```

## Периметр по режимам

- `dev`: `docker-compose.yml + docker-compose.dev.yml`, localhost-порты и опциональные tunnel-профили.
- `prod-like local`: `docker-compose.yml + docker-compose.prod-like.yml`, локальная публикация gateway для проверки.
- `test`: `docker-compose.yml + docker-compose.prod.yml + docker-compose.test.yml`, только `gateway` на `127.0.0.1:8080` для внешнего edge proxy.
- `prod`: `docker-compose.yml + docker-compose.prod.yml`, без публикации служебных host-портов по умолчанию.

Внешний HTTPS и заголовки безопасности настраиваются на внешнем edge reverse proxy (см. `infra/reverse-proxy/nginx.prod.example.conf`).

## Контейнеры и их роли

### `gateway`

Контейнер `gateway` на `nginx:alpine` - единая публичная точка входа для локального и серверного runtime.

Маршрутизация:

- `/` -> frontend `web`
- `/api/*` -> `backend`
- `/iam/*` -> `keycloak`

Практический смысл:

- frontend использует относительные URL и не знает о внутренних контейнерах;
- backend и Keycloak скрыты за единым host;
- внешние tunnel-решения подключаются к одному входу.

### `web`

SPA-клиент на React/Vite. В production-runtime обслуживается через `nginx` внутри контейнера.

Frontend:

- инициирует редирект на вход;
- отправляет API-запросы в `/api/...`;
- получает action flags и permissions от backend;
- открывает protected routes по состоянию сессии;
- работает с offer-chat через WebSocket-клиент.

### `backend`

Главный бизнес-сервис.

В `backend` сосредоточены:

- REST API;
- обработка OIDC callback;
- синхронизация пользователя из Keycloak в локальные таблицы;
- управление заявками, офферами, файлами и пользователями;
- вычисление разрешенных действий для UI;
- realtime-чат;
- фоновые задачи, связанные с обработкой reply mailbox.

### `keycloak`

Внешний IAM внутри локального compose.

Используется для:

- логина сотрудников и контрагентов;
- OIDC-поток редиректа;
- bootstrap realm;
- хранения аутентификационных аккаунтов.

### `rabbitmq`

Транспорт для очередей и асинхронных уведомлений.

Основной потребитель в текущей архитектуре - `notifications_worker`.

### `notifications_worker`

Отдельный воркер, который принимает события и отправляет email-уведомления.

Такой подход нужен, чтобы не держать тяжелые сетевые операции в request/response-потоке backend.

Подробнее о контрактах и ENV: [`notifications_worker/README.md`](../notifications_worker/README.md).

### `minio`

S3-совместимое хранилище файлов.

Backend:

- валидирует upload;
- создает запись о файле;
- сохраняет объект в хранилище;
- отдает файлы через контролируемый download endpoint.

### `tg_bot`

Legacy-модуль. По умолчанию в основном compose выключен, но логика взаимодействия с backend сохранена.

## Репозиторий и runtime: что где живет

### В этом репозитории

Здесь находятся:

- backend API;
- frontend;
- runtime compose;
- Keycloak bootstrap;
- worker;
- документация;
- legacy telegram bot.

### В другом репозитории

Основная рабочая схема PostgreSQL находится в репозитории `order_database`.

Это важно, потому что:

- миграции живут не здесь;
- часть эксплуатационной диагностики упирается именно в консистентность `order_database`;
- приложение зависит от уже поднятой и корректно промигрированной БД.

## Основные потоки данных

## 1. Поток аутентификации

### Login flow

1. Пользователь открывает `/login`.
2. Frontend направляет пользователя на backend endpoint начала OIDC flow.
3. Backend формирует редирект в Keycloak и ставит state-cookie.
4. Keycloak аутентифицирует пользователя и возвращает callback.
5. Backend обменивает authorization code на токены.
6. Backend синхронизирует identity в локальную модель пользователя.
7. Backend устанавливает refresh-token в `HttpOnly` cookie.
8. SPA получает access-данные через `POST /api/v1/auth/refresh`.

### Почему flow устроен так

- `access_token` не хранится в persistent storage браузера;
- `refresh_token` не доступен JavaScript напрямую;
- backend может централизованно решать, как связывать аккаунт Keycloak с локальным пользователем.

## 2. Поток регистрации контрагента

Есть два основных варианта.

### Регистрация через invite email

1. Контрагент получает invite-ссылку.
2. Переходит на `backend`-маршрут регистрации.
3. Backend валидирует токен приглашения.
4. Backend отправляет пользователя в Keycloak flow создания аккаунта.
5. После callback backend создает локального пользователя и связь с auth-account.
6. Пользователь попадает в систему со статусом `review`.

### Ручное создание контрагента

1. Сотрудник создает контрагента через UI/API.
2. Backend создает локального пользователя и аккаунт в Keycloak.
3. Контрагент задает пароль через стандартный механизм Keycloak `Forgot Password`.

## 3. Поток создания заявки

1. Frontend отправляет форму и файлы.
2. Backend валидирует файлы через `FileService`.
3. `RequestService` создает заявку и метаданные файлов.
4. Файлы сохраняются в MinIO.
5. При необходимости формируются email-уведомления.

Особенность:

- backend пытается не оставлять "висящие" файлы при ошибках и выполняет cleanup уже загруженных объектов.

## 4. Поток работы с оффером

1. Контрагент открывает contractor view заявки.
2. Создает оффер или открывает уже существующий.
3. Backend возвращает offer workspace.
4. Вместе с данными workspace backend вычисляет `actions`, которые разрешены текущему пользователю.
5. Пользователь меняет сумму, добавляет файлы, пишет сообщения, читает чат.
6. Статусы оффера обновляются по ролям и permissions.

## 5. Поток чата

### Запись сообщения

1. Клиент отправляет сообщение в backend.
2. Backend сохраняет сообщение и связанные вложения.
3. Realtime runtime публикует событие в chat channel.
4. Подписанные клиенты получают новое сообщение.

### Статусы доставки и прочтения

Есть отдельные endpoints для:

- `received`;
- `read`.

После обновления статуса backend публикует realtime event, чтобы второй участник видел изменения без перезагрузки страницы.

## Принципы организации backend

## API слой

Находится в `backend/app/api/v1`.

Роль API-слоя:

- принять HTTP-запрос;
- собрать зависимости;
- вызвать сервис;
- превратить результат в response schema;
- вернуть permissions / actions / links.

## Сервисный слой

Находится в `backend/app/services`.

Именно здесь живет бизнес-логика:

- auth;
- users;
- requests;
- offers;
- files;
- notifications;
- identity sync;
- email verification.

## Repository слой

Находится в `backend/app/repositories`.

Отвечает за изоляцию операций чтения и записи в БД.

## Policy и permissions слой

Находится в:

- `backend/app/domain/policies.py`
- `backend/app/domain/permissions.py`
- `backend/app/domain/authorization.py`
- `backend/app/api/action_flags.py`

Это один из ключевых архитектурных элементов проекта.

Логика доступа строится не только на ролях, но и на сочетании:

- роли;
- статуса;
- владения сущностью;
- предметного контекста;
- permission code.

### Почему backend отдает `actions`

UI не должен самостоятельно гадать, какие кнопки доступны. Поэтому backend возвращает готовые action flags:

- для заявок;
- для офферов;
- для чата;
- для пользователей.

Это снижает риск расхождения между бизнес-правилами и интерфейсом.

## Принципы организации frontend

Frontend организован по feature-oriented схеме.

Основные зоны:

- `app` - providers, app shell, routes
- `pages` - страницы
- `features` - сценарии и куски предметной логики
- `entities` - доменные типы и представления сущностей
- `shared` - API-клиент, UI-компоненты, утилиты, константы

## Где искать важную информацию

### Если меняется логин или регистрация

Смотрите:

- `backend/app/api/v1/auth.py`
- `backend/app/services/keycloak_oidc.py`
- `backend/app/services/identity_sync.py`
- `web/src/app/providers/AuthProvider.tsx`
- `docs/auth-and-onboarding.md`

### Если меняется заявка

Смотрите:

- `backend/app/api/v1/requests.py`
- `backend/app/services/requests.py`
- `backend/app/repositories/requests.py`
- `web/src/pages/requests/*`
- `web/src/features/request-details/*`
- `web/src/features/requests/*`

### Если меняется оффер или чат

Смотрите:

- `backend/app/api/v1/offers.py`
- `backend/app/services/offers.py`
- `backend/app/services/chat_realtime.py`
- `backend/app/realtime/*`
- `web/src/pages/offers/OfferWorkspacePage.tsx`
- `web/src/features/offer-workspace/*`
- `web/src/shared/ws/chatSocket.ts`

### Если меняется управление пользователями

Смотрите:

- `backend/app/api/v1/users.py`
- `backend/app/services/users.py`
- `backend/app/domain/policies.py`
- `web/src/features/admin/*`
- `web/src/shared/api/users/*`

## Эксплуатационные замечания

### Keycloak bootstrap вынесен отдельно

`docker-compose.init.yml` содержит одноразовые init-задачи:

- `keycloak_db_prepare`
- `keycloak_bootstrap`

Это позволяет разделить:

- подготовку БД Keycloak;
- запуск постоянных runtime-сервисов;
- одноразовый bootstrap realm и админской конфигурации.

### Проблемы с `order_database` критичны для приложения

Если на сервере неактуальная БД или пустой `flyway/sql`, приложение может стартовать, но падать на прикладных auth и business-сценариях. Для этого в проекте уже есть отдельные runbook-документы в `docs/`.

## Связанные документы

- [Обзор проекта](project-overview.md)
- [Навигация для разработчика](developer-guide.md)
- [Аутентификация и онбординг](auth-and-onboarding.md)
