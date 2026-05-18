# Сервис Уведомлений (Backend)

## Назначение

`user_notifications` — источник истины для данных центра уведомлений.

Подробная классификация событий находится в документе:

- `docs/development/notification-event-map.md`

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
- Доставка сейчас выполняется через polling/push-слой frontend; в будущем — через `/ws/realtime` (на этом этапе не реализовано).

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

- `/api/v1/ws/chat?ticket=...` остается текущим рабочим каналом чата.
- Добавлен общий endpoint `/api/v1/ws/realtime?ticket=...` для будущей унифицированной доставки событий чата и центра уведомлений.
- Для `/ws/realtime` используется ws-ticket с `purpose = realtime_ws`.
- Polling центра уведомлений пока не меняется и остается основным механизмом доставки уведомлений в UI.
- Следующий этап: фактическая доставка `notification.created` и связанных событий через `/ws/realtime`.

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

## Поток Email Delivery Не Менялся

Почтовый поток остается отдельным и не объединяется с process events:
- Worker публикует `email.delivery.succeeded` / `email.delivery.failed`.
- Backend `EmailDeliveryConsumerRuntime` + `EmailDeliveryEventHandler` формируют `email.sent` / `email.failed`.

Это сохраняет текущее поведение обратной связи по доставке email.

## Операционное Ограничение (Без Outbox)

Так как outbox нет:
- если commit в БД успешен и все retry публикации исчерпаны, событие может быть потеряно.

Этот случай логируется в `notification_publisher` с идентификаторами события.

## TODO

- Добавить выделенную колонку/индекс `dedupe_key` при росте нагрузки.
- Оценить bulk insert для очень больших наборов получателей.
- Добавить backend-фильтры уведомлений и cursor-pagination.
- Реализовать будущий endpoint `/ws/realtime` (пока не реализован).
