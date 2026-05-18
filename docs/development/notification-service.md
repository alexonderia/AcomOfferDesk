# Notification Service (Backend)

## Purpose

`user_notifications` is the source of truth for Notification Center data.

Backend now supports two independent RabbitMQ-driven flows:

1. Email delivery feedback flow (already existing):
- `email.delivery.succeeded`
- `email.delivery.failed`

2. Process notification flow (new centralized path):
- `offer.created`
- `message.created`
- `request.status_changed`
- `system.warning`

## Process Notification Pipeline

Pipeline (publish-after-commit, no outbox):

`Business Service` -> `DB commit succeeded` -> `notification_publisher.publish_process_notification_event()` -> `RabbitMQ` -> `ProcessNotificationConsumerRuntime` -> `ProcessNotificationEventHandler` -> `NotificationService` -> `user_notifications`.

Important:
- No `notification_outbox`.
- No Redis.
- No DB migrations for dedupe.

## RabbitMQ Contracts

Exchange / queue / routing keys:

- exchange: `app.events`
- process queue: `notify.process`
- process routing key: `notification.process`
- email queue: `notify.email`
- email delivery queue: `notify.email.delivery`
- email delivery routing keys:
  - `email.delivery.succeeded`
  - `email.delivery.failed`

## Process Event Envelope

Shared contract: `shared/process_notifications.py`.

Payload shape:

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

Rules:
- `event_id`, `event_type`, `occurred_at` are required.
- `actor_user_id`, `entity_type/entity_id`, `request_id/offer_id/chat_id/message_id`, `dedupe_key` are optional.
- `payload` defaults to `{}`.

## Publish-After-Commit

`UnitOfWork` now supports after-commit hooks (`add_after_commit_hook`).

Business services schedule process events into this hook:
- `OfferService.create_offer` -> `offer.created`
- `OfferService.create_message` -> `message.created`
- `RequestService.update_request` (status change) -> `request.status_changed`

Behavior:
- If DB commit fails -> event is not published.
- If DB commit succeeds but RabbitMQ publish finally fails -> business result remains successful; failure is only logged.

## Publisher Behavior

Implementation: `backend/app/infrastructure/notification_publisher.py`.

For process events:
- uses existing RabbitMQ connection/config style;
- publishes via `notification.process`;
- retries with backoff (100ms / 300ms / 1000ms);
- logs structured error with `event_id`, `event_type`, `entity_id` on final failure;
- does not log secrets.

## Process Consumer

Implementation: `backend/app/infrastructure/process_notification_consumer.py`.

Pattern mirrors `email_delivery_consumer`:
- robust connection;
- durable exchange/queue binding;
- `prefetch_count=20`;
- `message.process(requeue=False)`;
- invalid payload is skipped with warning;
- handler exceptions are logged without crashing runtime loop.

Startup/shutdown is wired in `backend/app/main.py` alongside `EmailDeliveryConsumerRuntime`.

## Event Handling Rules

Implementation: `backend/app/services/process_notification_events.py`.

Supported event types:

1. `offer.created`
- recipient: request owner (`request.id_user`);
- actor is excluded;
- notification type/severity: `offer.created` / `info`;
- title: `Новое коммерческое предложение`.

2. `message.created`
- recipients: chat participants excluding actor;
- if `payload.recipient_user_ids` is provided, it is used (preserves realtime/chat-open suppression logic already computed in `OfferService`);
- notification type/severity: `message.created` / `info`;
- title: `Новое сообщение`;
- link: `/offers/{offer_id}/workspace`.

3. `request.status_changed`
- recipient: request owner (`request.id_user`);
- actor is excluded;
- notification type/severity: `request.status_changed` / `info`;
- title: `Статус заявки изменен`.

4. `system.warning`
- recipients must be explicit in payload (`recipient_user_id` or `recipients`/`recipient_user_ids`);
- if recipient is missing, event is skipped with warning.

## Dedupe Without Migration

No schema migration was added.

Dedupe is best-effort via JSON payload keys in repository:
- `payload.event_id`
- `payload.dedupe_key`

Repository method:
- `exists_by_type_user_and_payload_key(user_id, notification_type, key_name, key_value)`.

Known limitation:
- JSON-key checks may become expensive at high load without dedicated indexed columns.

## Email Delivery Flow Is Unchanged

Email flow stays separate and is not merged into process events:
- Worker publishes `email.delivery.succeeded` / `email.delivery.failed`.
- Backend `EmailDeliveryConsumerRuntime` + `EmailDeliveryEventHandler` produce `email.sent` / `email.failed`.

This preserves current email delivery feedback behavior.

## Operational Limitation (No Outbox)

Because there is no outbox:
- if DB commit succeeded and all publish retries failed, event can be lost.

This is logged by `notification_publisher` with event identifiers.

## TODO

- Add dedicated `dedupe_key` column/index when load grows.
- Evaluate bulk insert path for very large recipient sets.
- Backend notification filters + cursor pagination.
- Future `/ws/realtime` endpoint (not implemented now).
