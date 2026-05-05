# Notifications Worker (`/notifications_worker`)

## Граница ответственности документа

Этот README описывает код и контракт уведомлений воркера.
Единый источник правды по окружениям/запуску:
- `docs/environments.md`

`notifications_worker` - отдельный процесс, который доставляет уведомления, отправляя письма (и опционально legacy Telegram-сообщения) на основе событий из RabbitMQ.

Это вынесенный асинхронный слой: тяжелая внешняя доставка (SMTP / Telegram HTTP API) не выполняется в request/response потоке backend.

## Роль модуля в системе

В runtime воркер используется для доставки уведомлений, которые backend публикует в очередь:

- email-уведомления для событий бизнес-доменов (например, по заявкам/офертам);
- legacy Telegram-уведомления для отката/совместимости (обычно выключены).

## Что делает воркер (high-level)

1. Подключается к RabbitMQ по `RABBITMQ_URL`.
2. Создает/подписывается на exchange `app.events`.
3. Потребляет очереди:
   - `notify.email` по routing key `email.send`;
   - `notify.tg` по routing key `telegram.send` (только если включен `LEGACY_TELEGRAM_ENABLED`).
4. Для каждого сообщения:
   - распаковывает JSON payload;
   - вызывает `send_email(payload)` или `send_tg(payload)`.

## Где лежит код

```text
notifications_worker/
  app/
    main.py          # подключение к RabbitMQ и subscribe на очереди
    consumers.py     # обработчик входящих сообщений (routing по routing_key)
    email_sender.py  # SMTP-отправка email с дедупликацией и анти-spam кулдауном
    tg_sender.py     # legacy Telegram отправка через Telegram Bot API
  requirements.txt
  Dockerfile
```

## Контракт событий (payload) для email

Backend публикует email через `shared.broker.EXCHANGE` и `shared.broker.RK_EMAIL`.

Ожидаемый payload для очереди email (`notify.email`) включает поля:

- `to_email`: получатель
- `subject`: тема
- `text_content`: plain text контент
- `html_content`: html контент (опционально)
- `attachments`: список вложений (опционально)
  - `filename`
  - `mime_type`
  - `content_base64`
- `reply_token`: токен для Reply-To адреса (опционально)
- `recipient_context`: контекст получателя для логов (опционально)
  - обычно `user_login`, `tg_id`
- `from_address`: SMTP from
- `from_name`: SMTP from display name

Источник payload:
- backend `SMTPEmailService.send_email()` публикует сообщение в RabbitMQ c `routing_key=RK_EMAIL`.

## Очереди и routing keys

Константы брокера находятся в `shared/broker.py` и используются и backend, и воркером:

- exchange: `app.events`
- очередь email: `notify.email`
- routing key email: `email.send`
- очередь legacy telegram: `notify.tg` (rollback compatibility)
- routing key telegram: `telegram.send` (legacy)

## ENV-переменные воркера

### RabbitMQ

- `RABBITMQ_URL` (default: `amqp://guest:guest@rabbitmq:5672/`)

### Включение legacy Telegram

- `LEGACY_TELEGRAM_ENABLED` (default: `false`)

Если выключен, воркер подписывается только на email очередь и legacy Telegram события пропускает.

### SMTP email

- `SMTP_HOST`
- `SMTP_PORT` (default: `465`)
- `SMTP_SECURITY` (default: `auto`)
  - `auto`: `465 -> ssl`, `587 -> starttls`, other ports -> plain SMTP
  - `ssl`: implicit TLS (SMTPS)
  - `starttls`: SMTP + TLS upgrade via STARTTLS
  - `none`: plain SMTP without TLS
- `EMAIL_ADDRESS` (логин для SMTP)
- `EMAIL_APP_PASSWORD` (пароль/токен приложения)
- `EMAIL_FROM_NAME` (default: `AcomOfferDesk`, display name)

Если SMTP env vars не настроены, воркер логирует предупреждение и пропускает отправку email.

### Анти-спам и дедупликация

- `EMAIL_DEDUP_TTL_SECONDS` (default: `120`)
  - дедуп по “fingerprint” payload в окне TTL
- `EMAIL_SPAM_COOLDOWN_SECONDS` (default: `600`, min: 60)
  - кулдаун адреса при SMTP подозрении на spam

## Реакция воркера на ошибки

- При ошибках SMTP:
  - если ошибка распознается как suspected spam (SMTP 554 + сигналы), адрес блокируется на кулдаун;
  - в остальных случаях “fingerprint” очищается, логируется исключение.
- Повторная доставка:
  - обработчик сообщения использует `message.process(requeue=False)`, то есть при падении сообщения оно не requeue-ится повторно “мягко”.

## Как локально запускать

Рекомендуется запускать воркер в составе root runtime:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build notifications_worker
```

Проверить:

- что backend публикует события в `app.events`;
- что `notifications_worker` логирует `Connected to RabbitMQ` и начало consumption.

## Что менять при изменении email-уведомлений

Три уровня:

1. Backend-пейлоад и content.
   - формирование `subject/text_content/html_content/attachments/reply_token`
   - где: `backend/app/infrastructure/email/*` и use-case’ы уведомлений.
2. Контракт payload.
   - если меняете поля, обновляйте соответствующую часть `notifications_worker/app/email_sender.py`.
3. Delivery-логика.
   - где: `notifications_worker/app/email_sender.py` (dedup/spam кулдауны, Reply-To адрес, attachments).

## Связанные документы

- `docs/runtime-architecture.md` (где воркер находится в схеме runtime)
- `docs/environments.md` (какой compose-слой использовать в dev/test/prod)
- backend email архитектура:
  - `backend/app/infrastructure/email/smtp_email_service.py`
  - `backend/app/infrastructure/notification_publisher.py`
