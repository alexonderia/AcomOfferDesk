# Техническое задание: подготовка AcomOfferDesk к production-релизу

## Граница ответственности документа

Этот документ — roadmap/ТЗ готовности к production: приоритеты, этапы и критерии завершения.

Смежные документы:
- [Окружения](./environments.md)
- [Чек-лист релиза](./release-checklist.md)
- [Production переменные/секреты](./production-env.md)
- [Аутентификация и онбординг](./auth-and-onboarding.md)

## 1. Назначение

Подготовить AcomOfferDesk к безопасному, воспроизводимому и поддерживаемому production-запуску.

ТЗ фиксирует не только изменения в `.env`, но и обязательные работы по сетевой схеме, безопасности, CI/CD, качеству кода, наблюдаемости, файловой структуре и пользовательским сообщениям.

## 2. Текущая картина проекта

Система состоит из:

- `gateway`: Nginx, единая точка входа;
- `web`: React SPA;
- `backend`: FastAPI API;
- `keycloak`: OIDC/IAM;
- `rabbitmq`: очередь для уведомлений;
- `minio`: S3-совместимое файловое хранилище;
- `notifications_worker`: обработчик email/legacy notification events;
- `tg_bot`: legacy Telegram-модуль, по умолчанию отключён;
- `order_database`: внешняя PostgreSQL БД в отдельном репозитории/контуре.

Важные текущие риски:

- `gateway` слушает только HTTP внутри текущего compose;
- `keycloak` по умолчанию стартует через `start-dev`;
- `backend` healthcheck сейчас завязан на `/docs`;
- RabbitMQ UI и MinIO API/Console публикуются через `ports`;
- MinIO и RabbitMQ имеют небезопасные fallback credentials;
- WebSocket передаёт access token в query string;
- есть deploy workflow, но нет отдельного обязательного CI-gate;
- frontend `lint` заявлен в `package.json`, но требует рабочей ESLint-конфигурации;
- проектовые стандарты разработки пока не заполнены реальными правилами.

## 3. Целевое состояние

Перед production-релизом система должна соответствовать следующим требованиям:

- публичный доступ идёт только через HTTPS;
- наружу опубликована только публичная точка входа приложения;
- Keycloak, cookies, OIDC-редирект и WebSocket работают в production-совместимом режиме;
- служебные интерфейсы доступны только через административный канал;
- секреты не имеют дефолтных fallback-значений;
- deploy невозможен без базовых проверок качества;
- у команды есть release checklist, rollback plan и smoke-test процедура;
- пользователи получают понятные сообщения о статусах, ошибках и дальнейших действиях;
- критичные ошибки видны через логи/мониторинг/error tracking.

## 4. Рекомендуемый подход

Не смешивать dev и production в одном наборе настроек.

Проект развивается через три ветки и три режима эксплуатации:

- `dev`: локальная разработка на одном ПК. На этом же проекте проверяются решения и предварительно тестируется production-подобный режим. Для внешнего доступа используется бесплатный `ngrok`, внешний VPS не используется.
- `test`: ветка интеграционного тестирования. Актуальные изменения из `dev` пушатся в `test`, после чего запускается авто-деплой на другой ПК/серверный контур с платным VPS и нужным публичным именем.
- `prod`: production-ветка и production-контур. Приложение работает во внутреннем контуре компании для сотрудников и имеет частичный внешний доступ для контрагентов.

Из этого следует важное ограничение: production-hardening должен быть оформлен через профили, override-файлы и env contracts, а не через ломку локального `dev`-режима. Один локальный ПК должен уметь запускать и обычную разработку, и production-like проверку через `ngrok`.

Рекомендуется сохранить текущий `docker-compose.yml` как базовый dev/test-compatible runtime и добавить production-слой:

- `docker-compose.prod.yml` для production override;
- `docker-compose.dev-prodlike.yml` или documented compose profile для локальной проверки production-подобного режима через `ngrok`;
- `backend/nginx.prod.conf` или отдельный внешний reverse proxy config;
- `docs/release-checklist.md`;
- `.github/workflows/ci.yml`;
- `.dockerignore` для build context;
- release smoke-test script в `scripts/`.

Если production обслуживается внешним Nginx/Caddy/Traefik на VPS, TLS лучше завершать на внешнем reverse proxy, а контейнерный `gateway` оставить внутренним сервисом. Если внешнего reverse proxy нет, TLS можно добавить прямо в `gateway`, но тогда нужно отдельно управлять сертификатами и renewal.

Поток веток должен быть явным:

- `dev -> test`: после локальной разработки и production-like проверки через `ngrok`;
- `test -> prod`: только после авто-деплоя, smoke-тестов и ручной проверки бизнес-сценариев в test;
- hotfix: отдельная процедура, где исправление проходит через `test`, если нет аварийного решения с отдельным approval.

## 4.1. Чеклист этапов

Статус этапов фиксируется прямо в этом документе и обновляется по мере появления
артефактов в репозитории и подтверждённых изменений в runtime.

| Этап | Статус | Что уже есть | Что ещё нужно для завершения |
|---|---|---|---|
| Этап 1. Окружения и branch flow | `[~] В работе` | Есть `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod-like.yml`, `docker-compose.init.yml`, `.env.dev.example`, `.env.prod-like.example`, документы `docs/environments.md` и `docs/runtime-architecture.md`, а также `deploy.yml` для ветки `test`. | Добавить `docs/release-checklist.md`, зафиксировать финальный `dev -> test -> prod` gate через отдельный CI и подтвердить, что production-процедура не использует dev/tunnel profiles. |
| Этап 2. Production-периметр | `[~] В работе` | Добавлены `docker-compose.prod.yml`, `docker-compose.test.yml`, `infra/reverse-proxy/nginx.prod.example.conf`, `docs/production-env.md`, `docs/release-checklist.md`, `scripts/check-prod-perimeter.sh`; обновлены документы по окружениям и периметру. | Подтвердить итоговые настройки на реальном test VPS/домене: TLS, firewall, smoke-проверку issuer/URI редиректа и недоступность служебных UI из публичного интернета. |
| Этап 3. Аутентификация, health и runtime-hardening | `[ ] Не начат` | Цели и требования сформулированы в этом ТЗ. | Внедрить ticket/cookie auth для WebSocket, `/health/live`, `/health/ready`, отключение публичных docs и readiness checks зависимостей. |
| Этап 4. CI и качество | `[ ] Не начат` | Есть только `deploy.yml`; отдельного обязательного CI-gate пока нет. | Добавить `.github/workflows/ci.yml`, рабочий ESLint, backend tests, smoke coverage, `.dockerignore` и `npm ci` в Docker build. |
| Этап 5. Observability и recovery | `[ ] Не начат` | Требования описаны на уровне плана и DoD. | Добавить structured logging, request id, error tracking, alerts, backup/rollback runbooks. |
| Этап 6. UX-сообщения и стандарты | `[ ] Не начат` | Требования к notification layer и стандартам разработки уже сформулированы. | Внедрить единый слой уведомлений, унифицировать error/empty/retry states, заполнить проектные стандарты разработки, оформить release checklist. |

Обозначения статусов:

- `[x]` выполнен;
- `[~]` в работе;
- `[ ]` не начат.

### Чеклист P0-задач

| P0-задача | Статус | Текущее состояние | Что нужно закрыть |
|---|---|---|---|
| `5.0` Разделение режимов `dev`, `test`, `prod` | `[~] В работе` | Уже есть отдельные compose-файлы, env-примеры и документ `environments.md`, который фиксирует модель окружений, perimeter и branch flow. | Добавить release checklist, финально закрепить CI-gate перед `test/prod` и подтвердить production-процедуру без dev/tunnel profiles. |
| `5.1` HTTPS и заголовки безопасности | `[~] В работе` | Добавлен пример внешнего reverse proxy с редиректом `80 -> 443`, `X-Forwarded-*`, заголовками безопасности, WebSocket upgrade и лимитом загрузки. | Проверить на реальном домене/сертификате в test и зафиксировать итоговый edge-конфиг в инфраструктуре VPS. |
| `5.2` Keycloak production mode | `[~] В работе` | Для `prod`-override зафиксирован запуск Keycloak через `kc.sh start`; env-contract для `KC_HOSTNAME`/proxy/issuer документирован. | Подтвердить в test runtime, что все test/prod env-файлы используют `KEYCLOAK_START_COMMAND=start` и issuer полностью совпадает. |
| `5.3` Закрытие служебных портов | `[~] В работе` | В `docker-compose.prod.yml` служебные порты не публикуются; для test добавлена loopback-публикация только `gateway` (`127.0.0.1:8080`). | Валидировать firewall/NAT на VPS и проверить извне, что `8000/8080(keycloak direct)/5432/5672/15672/9000/9001/5050` недоступны публично. |
| `5.4` Секреты и credentials | `[~] В работе` | Добавлен `docs/production-env.md` с перечнем обязательных секретов, минимальными требованиями и ротацией; `.env.prod-like.example` уже без `guest/guest` и `minioadmin/minioadmin`. | Добавить runtime fail-fast в следующих этапах и подтвердить назначение владельцев секретов в операционном контуре. |
| `5.5` WebSocket auth hardening | `[ ] Не начат` | В ТЗ прямо отмечен текущий риск с access token в query string. | Убрать token из URL, внедрить ticket/cookie-based auth и добавить проверки на invalid/expired/reused сценарии. |
| `5.6` Health, readiness и API docs | `[ ] Не начат` | В ТЗ прямо отмечен текущий риск: healthcheck завязан на `/docs`. | Внедрить `/health/live`, `/health/ready`, readiness зависимостей и закрыть публичный Swagger/OpenAPI в production. |

## 5. P0: блокирующие задачи до релиза

### 5.0. Разделение режимов `dev`, `test`, `prod`

Что сделать:

- формализовать различия между локальной разработкой, тестовым авто-деплоем и production-контуром;
- задокументировать, какие compose-файлы, env keys и профили используются в каждом режиме;
- исключить попадание tunnel/dev-настроек в `test` и `prod`.

Режим `dev`:

- запускается на одном локальном ПК;
- используется для разработки и предварительной production-like проверки;
- допускает бесплатный `ngrok` для внешней проверки callback, email links и контрагентских сценариев;
- не должен требовать внешнего VPS;
- может использовать dev-friendly defaults, но не должен маскировать production-only ошибки.

Режим `test`:

- разворачивается после push/merge в ветку `test`;
- использует авто-деплой;
- работает на отдельном ПК/серверном контуре с платным VPS и нужным публичным доменом;
- должен быть максимально близок к production по сетевой схеме, TLS, Keycloak, cookies, CORS и storage settings;
- используется для ручного бизнес-тестирования перед отдачей версии в production.

Режим `prod`:

- разворачивается из ветки `prod`;
- работает во внутреннем контуре компании для сотрудников;
- имеет контролируемый частичный внешний доступ для контрагентов;
- не использует `ngrok`, `localtunnel`, `cloudflared` dev profiles;
- допускает только production secrets и production-compatible runtime.

Что внедрить:

- таблицу env contracts для `dev`, `test`, `prod`;
- отдельные compose overrides или profiles для production-like локального запуска;
- release checklist с явной стадией `dev -> test -> prod`;
- проверку, что `ngrok`/tunnel profiles не активны в `test` и `prod`.

Критерии приёмки:

- разработчик на одном локальном ПК может запускать dev и production-like проверку без ручного переписывания compose;
- `test` после auto-deploy повторяет production-сетевую схему настолько близко, насколько возможно;
- `prod` не содержит dev-туннелей и публичных служебных портов;
- путь продвижения версии между ветками описан и повторяем.

### 5.1. HTTPS и заголовки безопасности

Что сделать:

- настроить production-домен и TLS-сертификат;
- включить редирект `HTTP -> HTTPS`;
- передавать корректные `X-Forwarded-Proto`, `X-Forwarded-Host`, `X-Forwarded-Port`;
- добавить заголовки безопасности на публичной точке входа.

Что внедрить:

- `Strict-Transport-Security`;
- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: SAMEORIGIN` или `DENY`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- базовый `Content-Security-Policy`;
- лимиты на размер запроса для upload endpoints.

Что убрать/исключить:

- штатную работу production через публичный HTTP;
- зависимость auth/cookie flow от tunnel/dev-исключений.

Артефакты:

- production reverse proxy config;
- документированный порядок выпуска/обновления сертификатов;
- smoke-check: login, callback, refresh, logout, WebSocket через HTTPS.

Критерии приёмки:

- `WEB_BASE_URL`, `PUBLIC_BACKEND_BASE_URL`, `KEYCLOAK_PUBLIC_BASE_URL` используют `https://`;
- refresh-cookie выставляется с `Secure`;
- OIDC callback не даёт смешанный контент или несовпадение URI редиректа;
- браузер получает заголовки безопасности на HTML/API-ответах.

### 5.2. Keycloak production mode

Что сделать:

- убрать `start-dev` из production runtime;
- настроить production startup Keycloak;
- явно задать hostname/proxy-related параметры Keycloak;
- разделить одноразовый bootstrap и постоянный runtime.

Что внедрить:

- `KEYCLOAK_START_COMMAND=start` для production;
- production env contract для `KC_HOSTNAME`, `KC_PROXY_HEADERS`/proxy mode, `KC_HTTP_RELATIVE_PATH=/iam`;
- проверку realm import/bootstrap в release checklist;
- запрет dev auto-link флагов в production.

Что убрать/исключить:

- fallback на `KEYCLOAK_START_COMMAND:-start-dev` в production;
- ручной bootstrap без проверки результата.

Артефакты:

- production env section в release checklist;
- smoke-check auth flow после bootstrap;
- rollback-инструкция на случай неудачного realm/bootstrap.

Критерии приёмки:

- Keycloak стартует в production mode;
- login/register/callback/refresh/logout работают с production-доменом;
- issuer в токене совпадает с `KEYCLOAK_ISSUER_URL`.

### 5.3. Закрытие служебных портов

Что сделать:

- убрать публикацию RabbitMQ UI и MinIO Console наружу;
- оставить доступ к служебным интерфейсам только через SSH tunnel/VPN/private network;
- проверить firewall на VPS.

Что внедрить:

- production override без `ports` для `rabbitmq`, `minio`, `ngrok`, tunnel-профилей;
- административный способ доступа через `ssh -L` или VPN;
- проверку открытых портов в release checklist.

Что убрать/исключить:

- публичные `15672`, `9000`, `9001`, `4040`;
- запуск tunnel/ngrok/cloudflared/localtunnel в production.

Артефакты:

- `docker-compose.prod.yml`;
- firewall checklist;
- runbook "как администратору попасть в RabbitMQ/MinIO".

Критерии приёмки:

- снаружи доступен только публичный HTTP/HTTPS вход;
- MinIO Console и RabbitMQ UI не открываются с публичного интернета;
- `docker compose --profile tunnel` не является частью production-процедуры.

### 5.4. Секреты и credentials

Что сделать:

- убрать небезопасные fallback credentials;
- описать обязательные production secrets;
- проверить длину и уникальность ключей.

Что внедрить:

- `docs/production-env.md` или раздел в release checklist;
- секреты для MinIO, RabbitMQ, JWT, refresh tokens, email verification, reply tokens, Keycloak admin;
- процедуру ротации секретов.

Что убрать/исключить:

- `minioadmin/minioadmin`;
- `guest/guest`;
- слабые пароли;
- хранение production `.env` в git.

Критерии приёмки:

- production не стартует с дефолтными секретами;
- все секреты перечислены и имеют владельца;
- `.env` не коммитится и не передаётся через артефакты CI.

### 5.5. WebSocket auth hardening

Что сделать:

- убрать передачу access token в query string WebSocket URL;
- заменить механизм авторизации realtime-соединения.

Рекомендуемый вариант:

- endpoint `POST /api/v1/auth/ws-ticket` выдаёт короткоживущий одноразовый ticket;
- WebSocket подключается с `?ticket=...`;
- backend валидирует ticket, связывает его с user/session и сразу инвалидирует.

Альтернатива:

- cookie-based WebSocket auth через HttpOnly refresh/session cookie, если текущая auth-модель будет расширена под handshake.

Что убрать/исключить:

- bearer/access token в URL;
- логирование URL с секретными параметрами.

Артефакты:

- backend endpoint для `ws_ticket`;
- frontend обновление `chatSocket.ts`;
- тесты на expired/invalid/reused ticket;
- проверка reconnect после refresh.

Критерии приёмки:

- access token не появляется в WebSocket URL;
- повторное использование ticket невозможно;
- при истечении access token пользовательский reconnect flow остаётся понятным.

### 5.6. Health, readiness и API docs

Что сделать:

- заменить backend healthcheck с `/docs` на dedicated endpoints;
- разделить liveness и readiness;
- ограничить публичный доступ к Swagger/Redoc/OpenAPI в production.

Что внедрить:

- `GET /health/live`: процесс жив;
- `GET /health/ready`: критичные зависимости готовы;
- настройку `docs_url`, `redoc_url`, `openapi_url` в зависимости от `APP_ENV`;
- production healthcheck в compose через `/health/live` или `/health/ready`.

Readiness должен проверять минимум:

- DB connection;
- Keycloak/JWKS доступность или приемлемое состояние cache;
- S3 bucket доступен;
- RabbitMQ доступен, если backend зависит от publish path.

Критерии приёмки:

- container healthcheck не ходит в `/docs`;
- Swagger недоступен публично в production или защищён;
- readiness отражает реальное состояние зависимостей.

## 6. P1: качество, CI/CD и воспроизводимость

### 6.1. CI gate перед deploy

Что сделать:

- добавить отдельный `ci.yml`;
- сделать deploy зависимым от зелёного CI;
- защитить релизную ветку обязательными status checks.
- разделить правила для веток `dev`, `test`, `prod`.

Минимальный CI:

- `web`: `npm ci`, `npm run lint`, `npm run build`;
- `backend`: dependency install, import check, unit/integration tests;
- `notifications_worker`: dependency install, import/smoke check;
- `tg_bot`: тесты только если legacy включается или меняется;
- Docker build check для основных образов.

Что поправить в текущем подходе:

- текущий `deploy.yml` не должен быть единственным quality gate;
- SSH deploy не должен стартовать при красном CI;
- в CI нельзя полагаться на локальный `node_modules`.

Правила по веткам:

- `dev`: CI может быть advisory, но перед merge/push в `test` локально должны проходить build/lint/smoke checks;
- `test`: CI обязателен, auto-deploy запускается только после успешных checks;
- `prod`: deploy только после успешного `test`, ручного подтверждения и release checklist.

Артефакты:

- `.github/workflows/ci.yml`;
- обновлённый `deploy.yml` или branch protection;
- README-раздел с локальными командами проверки.

Критерии приёмки:

- PR/merge в релизную ветку невозможен без CI;
- deploy не идёт после failed build/test;
- CI можно воспроизвести локально.

### 6.2. Lint, tests и smoke coverage

Что сделать:

- добавить рабочую ESLint-конфигурацию;
- добавить backend test runner;
- покрыть минимальные production-critical сценарии.

Минимальный набор тестов:

- аутентификация: редирект на вход, ошибки callback, refresh, logout;
- permissions: роли и статусы `review`, `active`, `inactive`, `blacklist`;
- requests/offers: основные happy/forbidden paths;
- files: расширения, magic signature, размер, пустой файл;
- email notifications: publish failure и retry/логирование;
- realtime: invalid/expired auth и reconnect handling.

Frontend smoke:

- `/login`;
- `/auth/callback`;
- `/account`;
- `/requests`;
- `/requests/:id`;
- `/offers/:id/workspace`;
- admin/dashboard routes по ролям.

Критерии приёмки:

- `npm run lint` не падает из-за отсутствия config;
- `npm run build` проходит в CI;
- backend tests запускаются одной документированной командой;
- критичные сценарии имеют хотя бы smoke/regression coverage.

### 6.3. Docker build hygiene

Что сделать:

- добавить `.dockerignore`;
- заменить `npm install` на `npm ci` в `web/Dockerfile`;
- исключить попадание локальных артефактов в image context;
- рассмотреть non-root user для production containers.

Что внедрить:

- `.dockerignore` на уровне repo root и/или сервисов;
- pinning базовых образов на стабильные версии;
- Docker build check в CI.

Что убрать/исключить:

- `node_modules`, `dist`, `.env`, `.trellis`, `.agents`, artifacts в build context;
- production build, зависящий от локального состояния машины разработчика.

Критерии приёмки:

- image собирается воспроизводимо с чистого checkout;
- build context не содержит секретов и лишних артефактов;
- `web` image строится через lockfile.

## 7. P1: эксплуатация и наблюдаемость

### 7.1. Structured logging

Что сделать:

- привести backend и worker к единому формату логов;
- добавить request/correlation id;
- логировать критичные интеграционные ошибки с контекстом.

Что внедрить:

- JSON logs или единый key-value format;
- request id propagation через gateway/backend;
- отдельные события для auth, file upload, email delivery, RabbitMQ publish, S3 operations, WebSocket disconnect.

Критерии приёмки:

- по логам можно восстановить путь запроса;
- ошибки email/S3/RabbitMQ/auth видны без чтения stack trace в одиночку;
- секреты и токены не попадают в логи.

### 7.2. Monitoring и alerting

Что сделать:

- подключить error tracking и базовые alerts;
- определить минимальный набор метрик.

Что внедрить:

- Sentry или аналог для `web` и `backend`;
- uptime monitor для публичного URL;
- alert на рост 5xx;
- alert на недоступность Keycloak/DB/RabbitMQ/MinIO;
- alert на очередь email или ошибки отправки.

Критерии приёмки:

- команда узнаёт о production-проблеме без ручного захода на сервер;
- frontend errors и backend exceptions попадают в единый triage-процесс.

### 7.3. Backup, rollback и recovery

Что сделать:

- описать release rollback;
- описать backup policy;
- проверить восстановление хотя бы на тестовом окружении.

Что внедрить:

- backup БД `order_database`;
- backup Keycloak volume/config или документированный bootstrap replay;
- backup MinIO data/volume или внешнее object storage strategy;
- rollback script/инструкция на предыдущий git ref/image;
- runbooks по отказам зависимостей.

Критерии приёмки:

- есть понятный путь отката релиза;
- есть проверенный путь восстановления данных;
- release engineer знает, где смотреть причину failed deploy.

## 8. P1/P2: пользовательские уведомления и диалог

### 8.1. Единый слой сообщений

Что сделать:

- унифицировать success/error/warning/info сообщения;
- убрать разрозненность локальных `Alert`, где нужна глобальная обратная связь;
- оставить inline `Alert` там, где сообщение относится к конкретному блоку формы или таблицы.

Что внедрить:

- `NotificationProvider`/`SnackbarProvider`;
- общий API для `notifySuccess`, `notifyError`, `notifyWarning`, `notifyInfo`;
- единый mapper backend errors -> пользовательские тексты;
- стандарт для dismiss/retry actions.

Критерии приёмки:

- пользователь получает одинаково оформленные сообщения по всему приложению;
- ошибки содержат следующий шаг: повторить, проверить данные, обратиться к администратору;
- технические exception-тексты не просачиваются в UI.

### 8.2. Обязательные пользовательские состояния

Нужно проверить и доработать сообщения для сценариев:

- вход не выполнен;
- сессия истекла;
- доступ ожидает подтверждения;
- доступ выдан или отклонён;
- действие успешно завершено;
- сервис временно недоступен;
- уведомление отправлено или не отправлено;
- чат временно недоступен;
- файл отклонён с конкретной причиной;
- нет данных для отображения;
- нет прав на действие.

Критерии приёмки:

- на каждом ключевом экране есть loading, empty, forbidden, error и retry/fallback state;
- пользователь понимает, что произошло и что делать дальше.

## 9. P2: структура и документация проекта

### 9.1. Чек-лист релиза

Создать `docs/release-checklist.md`.

Документ должен включать:

- проверку env/secrets;
- проверку доменов и TLS;
- проверку Keycloak issuer и URI редиректа;
- проверку доступности `order_database`;
- запуск миграций/проверку Flyway history;
- порядок Keycloak bootstrap;
- порядок deploy;
- smoke checks после deploy;
- rollback steps;
- список контактов/ответственных.

### 9.2. Runbooks

Создать или расширить runbooks для:

- Keycloak недоступен;
- OAuth callback даёт ошибку;
- БД недоступна или миграции неполные;
- RabbitMQ недоступен;
- MinIO недоступен;
- email не отправляются;
- WebSocket/realtime не работает;
- frontend отдаёт HTML вместо API JSON.

### 9.3. Проектные стандарты

Заполнить раздел проектных стандартов реальными правилами проекта:

- backend directory structure;
- frontend feature structure;
- API/service/repository responsibilities;
- error handling;
- logging;
- testing requirements;
- type safety;
- UI notification rules.

Критерии приёмки:

- новый разработчик понимает архитектурные правила без устной передачи знаний;
- разработчики получают конкретные проектные стандарты, а не пустые placeholders.

## 10. План внедрения

### Этап 1. Окружения и branch flow

Результат: понятно, как одна кодовая база живёт в `dev`, `test` и `prod`.

Задачи:

- описать env contracts для `dev`, `test`, `prod`;
- добавить/описать production-like локальный запуск через `ngrok`;
- зафиксировать `dev -> test -> prod` поток продвижения;
- разделить auto-deploy в `test` и ручной допуск в `prod`;
- исключить dev tunnel profiles из `test` и `prod`.

### Этап 2. Production-периметр

Результат: внешний контур безопасен.

Задачи:

- HTTPS;
- заголовки безопасности;
- Keycloak production mode;
- закрытие служебных портов;
- замена дефолтных credentials;
- tunnel/ngrok профили исключены из production.

### Этап 3. Аутентификация, health и runtime-hardening

Результат: auth/realtime/runtime не завязаны на dev-механики.

Задачи:

- WebSocket ticket/cookie auth;
- `/health/live` и `/health/ready`;
- отключение публичных API docs в production;
- readiness checks зависимостей;
- production compose override.

### Этап 4. CI и качество

Результат: deploy проходит через воспроизводимый quality gate.

Задачи:

- `ci.yml`;
- рабочий ESLint;
- backend tests;
- smoke coverage;
- `.dockerignore`;
- `npm ci` в Dockerfile.

### Этап 5. Observability и recovery

Результат: проблемы видны и есть путь восстановления.

Задачи:

- structured logs;
- request id;
- Sentry/error tracking;
- alerts;
- backup/rollback runbooks.

### Этап 6. UX-сообщения и стандарты

Результат: пользовательские сценарии понятны при успехе и сбоях.

Задачи:

- единый notification layer;
- унификация ошибок;
- empty/error/retry states;
- release checklist;
- заполнение проектных стандартов разработки.

## 11. Критерии завершения

Релизная подготовка считается завершённой, если:

- production доступен через HTTPS;
- cookies/auth/OIDC работают с production-доменом;
- Keycloak не стартует в dev-mode;
- служебные порты не опубликованы наружу;
- дефолтные credentials исключены;
- WebSocket не передаёт access token в URL;
- healthcheck не использует `/docs`;
- readiness отражает состояние критичных зависимостей;
- CI блокирует deploy при failed lint/build/test;
- Docker images собираются с чистого checkout;
- есть release checklist и rollback plan;
- есть базовая наблюдаемость и error tracking;
- пользовательские ошибки и статусы унифицированы;
- раздел проектных стандартов содержит реальные правила проекта.

## 12. Приоритеты

Блокирует релиз:

- формализованный `dev -> test -> prod` flow;
- production-like проверка на локальном `dev` через `ngrok` без изменения production contracts;
- auto-deploy в `test` только после успешного CI;
- HTTPS и headers;
- Keycloak production mode;
- закрытие служебных портов;
- секреты без дефолтов;
- WebSocket auth hardening;
- health/readiness вместо `/docs`;
- минимальный CI gate.

Очень желательно до релиза:

- structured logging;
- Sentry/error tracking;
- backup/rollback runbooks;
- smoke tests;
- production compose override;
- `.dockerignore` и `npm ci`.

Можно завершить сразу после первого production-запуска:

- расширение regression coverage;
- углублённый monitoring;
- полный notification center;
- финальная чистка legacy;
- оптимизация frontend bundle.


