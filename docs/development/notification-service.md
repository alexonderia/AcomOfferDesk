# Сервис Уведомлений (Backend)

## Назначение

`user_notifications` — источник истины для данных центра уведомлений.

Подробная классификация событий находится в документе:

- `docs/operations/notifications-matrix.md`

## Категории Уведомлений

В проекте используются две категории:

1. `system_ui`
- Локальная обратная связь интерфейса на текущей странице (например: сохранение, создание, загрузка, валидация).
- Такие уведомления **не** пишутся в `user_notifications`.
- Целевое размещение: `top-center` toast (часть текущих сценариев пока использует inline `Alert`).

2. `business`
- Кросс-страничные бизнес-сигналы, важные независимо от текущего экрана.
- Такие уведомления пишутся в `user_notifications`.
- Отображаются в центре уведомлений.
- Online-доставка выполняется через `/api/v1/ws/realtime` событием `notification.created`.
- Polling не является основным push-механизмом и используется только как sync/fallback (открытие центра, reconnect, редкий fallback-опрос).

Backend поддерживает два независимых RabbitMQ-потока:

1. Поток обратной связи по доставке email (существовал ранее):
- `email.delivery.succeeded`
- `email.delivery.failed`

2. Поток процессных уведомлений (централизованный путь):
- `offer.created`
- `message.created`
- `request.status_changed`
- `system.warning`

## WebSocket Каналы (Текущее Состояние)

- Основной канал realtime: `/api/v1/ws/realtime?ticket=...`.
- Через `/ws/realtime` работают и чат, и центр уведомлений.
- Для `/ws/realtime` используется ws-ticket с `purpose = realtime_ws`.
- `purpose = chat_ws` удален из backend/frontend контрактов.
- `notification.created` отправляется после успешного создания записи в `user_notifications` (best-effort: offline user не ошибка, ошибка отправки только логируется).
- `/api/v1/ws/chat` удален. Единый websocket transport в браузере: только `/api/v1/ws/realtime`.
- Backend wire-протокол чата использует только canonical event types `chat.*`:
  - `chat.message.created`
  - `chat.message.delivered`
  - `chat.message.read`
  - `chat.typing.started`
  - `chat.typing.stopped`
- Inbound client request types остаются без изменений: `message.send`, `message.read`, `typing.start`, `typing.stop`, `chat.sync`.

## Контракт Realtime Envelope

Базовый формат для всех realtime-событий:

```json
{
  "type": "chat.message.created",
  "event_id": "uuid",
  "ts": "2026-05-22T12:00:00Z",
  "data": {}
}
```

Примеры:

- `notification.created`:
  - `data.notification` — объект уведомления для UI;
  - `data.has_unread` — флаг red dot.
- `chat.message.created`:
  - `data.chat_id`, `data.message`.
- `chat.message.read`:
  - `data.chat_id`, `data.user_id`, `data.message_ids`, `data.last_read_message_id`.
- `chat.typing.started` / `chat.typing.stopped`:
  - `data.chat_id`, `data.user_id`.

## Пайплайн Процессных Уведомлений

Пайплайн (publish-after-commit, без outbox):

`Business Service` -> `DB commit succeeded` -> `notification_publisher.publish_process_notification_event()` -> `RabbitMQ` -> `ProcessNotificationConsumerRuntime` -> `ProcessNotificationEventHandler` -> `NotificationService` -> `user_notifications`.

Важно:
- Нет `notification_outbox`.
- Нет Redis.
- Нет миграции БД для dedupe.

## Контракты RabbitMQ

Exchange / queue / routing keys:

- exchange: `app.events`
- process queue: `notify.process`
- process routing key: `notification.process`
- email queue: `notify.email`
- email delivery queue: `notify.email.delivery`
- email delivery routing keys:
  - `email.delivery.succeeded`
  - `email.delivery.failed`

## Конверт Process Event

Общий контракт: `shared/process_notifications.py`.

Формат payload:

```json
{
  "event_id": "uuid",
  "event_type": "offer.created",
  "occurred_at": "2026-05-18T12:00:00Z",
  "actor_user_id": "user-id-or-null",
  "entity_type": "offer",
  "entity_id": "123",
  "request_id": 42,
  "offer_id": 123,
  "chat_id": 123,
  "message_id": 555,
  "dedupe_key": "offer.created:123",
  "payload": {}
}
```

Правила:
- `event_id`, `event_type`, `occurred_at` — обязательны.
- `actor_user_id`, `entity_type/entity_id`, `request_id/offer_id/chat_id/message_id`, `dedupe_key` — опциональны.
- `payload` по умолчанию `{}`.

## Publish-After-Commit

`UnitOfWork` поддерживает after-commit hooks (`add_after_commit_hook`).

Бизнес-сервисы планируют процессные события в этот hook:
- `OfferService.create_offer` -> `offer.created`
- `OfferService.create_message` -> `message.created`
- `RequestService.update_request` (смена статуса) -> `request.status_changed`

Поведение:
- Если commit в БД падает -> событие не публикуется.
- Если commit в БД успешен, но публикация в RabbitMQ окончательно провалилась -> бизнес-операция остается успешной, ошибка только логируется.

## Поведение Publisher

Реализация: `backend/app/infrastructure/notification_publisher.py`.

Для process events:
- использует текущий стиль подключения/конфига RabbitMQ;
- публикует через `notification.process`;
- делает retry с backoff (100ms / 300ms / 1000ms);
- при финальной ошибке пишет структурированный лог с `event_id`, `event_type`, `entity_id`;
- не логирует секреты.

## Process Consumer

Реализация: `backend/app/infrastructure/process_notification_consumer.py`.

Паттерн повторяет `email_delivery_consumer`:
- устойчивое соединение;
- durable exchange/queue binding;
- `prefetch_count=20`;
- `message.process(requeue=False)`;
- невалидный payload пропускается с warning;
- ошибки handler логируются без падения runtime-loop.

Запуск/остановка подключены в `backend/app/main.py` рядом с `EmailDeliveryConsumerRuntime`.

## Правила Обработки Событий

Реализация: `backend/app/services/process_notification_events.py`.

Поддерживаемые типы событий:

1. `offer.created`
- получатель: владелец заявки (`request.id_user`);
- автор события исключается;
- тип/severity уведомления: `offer.created` / `info`;
- заголовок: `Новое коммерческое предложение`.

2. `message.created`
- получатели: участники чата, кроме автора;
- если передан `payload.recipient_user_ids`, используется он (сохраняет логику suppress для открытого чата, уже рассчитанную в `OfferService`);
- тип/severity уведомления: `message.created` / `info`;
- заголовок: `Новое сообщение`;
- ссылка: `/offers/{offer_id}/workspace`.

3. `request.status_changed`
- получатель: владелец заявки (`request.id_user`);
- автор события исключается;
- тип/severity уведомления: `request.status_changed` / `info`;
- заголовок: `Статус заявки изменен`.

4. `system.warning`
- получатели должны быть явно переданы в payload (`recipient_user_id` или `recipients`/`recipient_user_ids`);
- если получатель не указан, событие пропускается с warning.

## Dedupe Без Миграции

Миграция схемы не добавлялась.

Dedupe реализован best-effort через JSON-ключи в payload:
- `payload.event_id`
- `payload.dedupe_key`

Метод репозитория:
- `exists_by_type_user_and_payload_key(user_id, notification_type, key_name, key_value)`.

Известное ограничение:
- проверки по JSON-ключам могут стать дорогими на высокой нагрузке без выделенных индексируемых колонок.
- future improvement: выделенная колонка `dedupe_key` + индекс.

## Поток Email Delivery Не Менялся

Почтовый поток остается отдельным и не объединяется с process events:
- Worker публикует `email.delivery.succeeded` / `email.delivery.failed`.
- Backend `EmailDeliveryConsumerRuntime` + `EmailDeliveryEventHandler` формируют `email.sent` / `email.failed`.

Это сохраняет текущее поведение обратной связи по доставке email.

## Frontend Поведение Центра Уведомлений

- `user_notifications` остается source of truth.
- REST `/api/v1/notifications` остается основным API для списка/прочтения/sync.
- `NotificationBell` использует `hasUnread` (red dot), а не отображение numeric unread-count.
- При `notification.created`:
  - `hasUnread` становится `true`;
  - при открытом центре новое уведомление добавляется в начало списка;
  - показывается business toast в `bottom-right`;
  - сохраняются suppress для `message.created` при уже открытом соответствующем workspace, dedupe по id и burst-aggregation для серии событий.
- Polling unread-count допускается только как sync/fallback механизм.

## System UI Toast vs Business Notification

- `system_ui`:
  - локальный результат действия пользователя на текущей странице;
  - показывается как компактный toast `top-center`;
  - не сохраняется в `user_notifications`;
  - не влияет на red dot и центр уведомлений.
- `business`:
  - процессное событие, важное вне текущей страницы;
  - сохраняется в `user_notifications`;
  - доставляется через `/api/v1/ws/realtime` событием `notification.created`;
  - показывается как push toast `bottom-right` и в центре уведомлений.

Почему разделение важно:
- центр уведомлений не захламляется локальными success/error;
- процессные сигналы не теряются среди технического UI-feedback;
- UX предсказуем: локальные действия сверху, кросс-страничные события справа снизу.

## Операционное Ограничение (Без Outbox)

Так как outbox нет:
- если commit в БД успешен и все retry публикации исчерпаны, событие может быть потеряно.
- Redis для межинстансовой координации в текущей реализации не используется.
- multi-instance/high-load улучшения (outbox/Redis) вынесены в future backlog и не входят в текущую поставку.

Этот случай логируется в `notification_publisher` с идентификаторами события.

## TODO

- Добавить выделенную колонку/индекс `dedupe_key` при росте нагрузки.
- Добавить backend-фильтры уведомлений и cursor-pagination.

## Чек-Лист Русификации

Ручная проверка (в дополнение к `python scripts/check_mojibake.py`):

- API/WS ошибки, попадающие в UI, показываются понятными русскими текстами без `Unauthorized/Forbidden/ValidationError/Internal Server Error`.
- Toast/Alert не показывают технические детали (`traceback`, `sql`, `rabbitmq`, `smtp`, `jwt`).
- Email subject/body и `notification.title/body` остаются человекочитаемыми на русском.

## Контракт доставки и настроек

This file documents the current notification delivery contract.

## Scenario: Internal, WebSocket, and Email Delivery

### 1. Scope / Trigger

- Trigger: any change to business notifications, RabbitMQ delivery, notification preferences, or worker configuration.
- The supported runtime paths are in-app persistence, WebSocket delivery, and email delivery through `notifications_worker`.

### 2. Signatures

- `NotificationService` creates in-app notification rows and schedules realtime delivery.
- Backend email publishers publish to exchange `app.events` with routing key `email.send`.
- `notifications_worker.app.consumers.handle_message(message)` consumes only email delivery messages.
- `GET|PUT /api/v1/users/me/notification-preferences` exposes email-only preferences.

### 3. Contracts

- Queue: `notify.email`.
- Routing key: `email.send`.
- Preference modes: `email_only`, `none`, and response-only `custom`.
- Per-type preference shape: `{"chat|request|offer|system": {"email": boolean}}`.
- Worker environment: `RABBITMQ_URL`, SMTP keys, `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD`, `EMAIL_FROM_NAME`, `EMAIL_DEDUP_TTL_SECONDS`, and `EMAIL_SPAM_COOLDOWN_SECONDS`.
- Existing messenger-related database values remain storage compatibility only and must not be exposed as notification channels.

### 4. Validation & Error Matrix

- Unsupported preference mode -> `409 Conflict`.
- Unsupported notification type -> `409 Conflict`.
- Unsupported channel key -> `409 Conflict`.
- Enabling email without an available email address -> `409 Conflict`.
- Unsupported RabbitMQ routing key -> acknowledge and skip without external delivery.

### 5. Good / Base / Bad Cases

- Good: a business event creates an in-app notification, reaches connected users over WebSocket, and publishes email when enabled.
- Base: email is disabled; the in-app and WebSocket paths still operate.
- Bad: backend publishes to an undeclared messenger queue or the worker imports an external messenger sender.

### 6. Tests Required

- Unit: email-only preference modes and per-type persistence.
- Integration: request, offer, chat, and user-status events preserve in-app/process events.
- Worker: application imports, binds only `notify.email`, and publishes email delivery results.
- Contract: unsupported channel keys are rejected and no messenger fields are returned by profile endpoints.

### 7. Wrong vs Correct

#### Wrong

```python
await publisher.publish("external-messenger.send", payload)
```

#### Correct

```python
await publisher.publish(RK_EMAIL, email_payload)
```

## Rules

- Do not move SMTP delivery into synchronous request handling.
- Update backend publisher, shared broker constants, worker consumer, tests, and docs together when the email payload changes.
- Preserve delayed email and email delivery-result routes.

## Scenario: Aggregated Final Email Result Notifications

### 1. Scope / Trigger
- Trigger: a user launches a multi-recipient email operation where the product needs one final in-app result notification after worker-confirmed delivery, not a burst of per-recipient system notifications.

### 2. Signatures
- Request additional emails:
  `POST /api/v1/requests/{request_id}/email-notifications`
- Contractor invitations:
  `POST /api/v1/contractors/invite`
- Outbound email payload fields:
  `operation_id`
  `operation_kind`
  `operation_expected_total`
- Delivery feedback event fields:
  `operation_id`
  `operation_kind`
  `operation_expected_total`

### 3. Contracts
- `operation_id` groups all recipient deliveries that belong to one user action.
- `operation_kind` currently supports:
  - `request.additional_email`
  - `contractor.invite`
- `operation_expected_total` is the total intended recipient count for the operation, including items that may fail before worker delivery.
- The notification center may use one hidden tracking row in `user_notifications` with `payload.tracking_only="true"` while the batch is incomplete.
- Hidden tracking rows must not appear in list/unread APIs.
- Hidden tracking rows must not be delivered to the SPA as visible `notification.created` items; otherwise the later finalized event may reuse the same notification id and lose its push/display update.
- Final visible email-result notification must carry `payload.toast_channel="system"` and trigger a dedicated realtime `system.toast` event for top-center system UI, while the normal `notification.created` event still refreshes the notification center list.
- Final user-visible notification is emitted only when:
  - all worker delivery events for the operation are processed; and
  - any pre-worker queue failures are accounted for.

### 4. Validation & Error Matrix
- batch operation with final worker feedback complete -> emit one final aggregated notification to the initiator
- per-recipient worker events for a tracked batch -> do not emit separate initiator-facing `email.sent` / `email.failed` notifications
- duplicate delivery event with same `correlation_id` inside one `operation_id` -> ignore
- queue failure before worker delivery -> count it toward the same batch summary
- hidden tracking row still incomplete -> exclude from notifications list and unread count
- hidden tracking row reaches realtime/frontend state -> ignore it and still allow the later finalized notification with the same id to appear
- final email-result notification arrives with `toast_channel=system` -> do not show business push; show only system toast plus center update

### 5. Good/Base/Bad Cases
- Good: 10 invitations started, 7 delivered, 2 worker failures, 1 queue failure -> initiator gets one final summary with `7/10`, partial success, no burst of 10 notifications.
- Base: one-off email flow without batch metadata may still use ordinary per-email `email.sent` / `email.failed`.
- Bad: create one system notification per recipient for a batch operation and flood the notification center, or emit a “success” summary before worker delivery finishes.

### 6. Tests Required
- Unit: worker feedback with one `operation_id` finalizes exactly one notification after the last delivery event.
- Unit: queue-only total failure finalizes one `email.failed` aggregated summary without waiting for worker events.
- Unit: duplicate delivery `correlation_id` inside one batch does not increment counts twice.
- Unit/Frontend: tracking-only realtime notification is ignored, and the finalized visible notification with the same id still updates state and shows push UI.
- Unit/Frontend: `toast_channel=system` email result emits `system.toast` and skips the bottom-right business notification push.
- Integration: BFF/request/invite flows pass operation metadata through the existing adapters where required.

### 7. Wrong vs Correct
#### Wrong
- Treat every recipient result as an independent initiator-facing system notification for batch operations.

#### Correct
- Use operation metadata plus one hidden tracking notification row, then publish one final aggregated initiator-facing result when the batch is fully resolved.

## Получатели модерации регистрации

`user.review_required` адресуется admin и superadmin; для contractor lifecycle также security officer.
Контрагент на проверке не получает административное уведомление. Инициирующий администратор не исключается общим фильтром автора.
Источник текущего отбора — `ProcessNotificationEventHandler._handle_user_review_required`.
