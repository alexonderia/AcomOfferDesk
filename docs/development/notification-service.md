# Сервис уведомлений (Backend)

## Назначение

`NotificationService` — backend-точка входа для данных центра уведомлений пользователя.  
Уведомления формируются в сервисном слое backend и сохраняются в таблицу `user_notifications`.

Это позволяет держать в одном месте:
- правила выбора получателей;
- правила исключения self-уведомлений;
- безопасное формирование текста, ссылки и `payload`.

## Почему не триггеры БД

Триггеры БД намеренно не используются, потому что:
- выбор получателей зависит от бизнес-контекста сервисов (владелец КП, участники чата, инициатор);
- текст и ссылка уведомления требуют знания прикладных маршрутов и сущностей;
- логику в сервисах проще тестировать и развивать, чем trigger-side реализацию.

## Поддерживаемые типы уведомлений (v1)

- `offer.created`
- `message.created`
- `email.sent`
- `email.failed`
- `request.status_changed`
- `system.warning`

Поддерживаемые уровни важности (`severity`):
- `info`
- `success`
- `warning`
- `error`

## API-эндпоинты

- `GET /api/v1/notifications`
  - возвращает только уведомления текущего пользователя;
  - сортировка: `created_at DESC`;
  - поддерживает `limit` и `offset`.
- `GET /api/v1/notifications/unread-count`
  - возвращает количество непрочитанных уведомлений текущего пользователя.
- `PATCH /api/v1/notifications/{notification_id}/read`
  - помечает одно уведомление как прочитанное для текущего пользователя;
  - возвращает `404`, если уведомление не найдено или принадлежит другому пользователю.
- `PATCH /api/v1/notifications/read-all`
  - помечает все непрочитанные уведомления текущего пользователя.

## Интегрированные сценарии

Уже подключены:
- создание КП -> уведомление владельца заявки (кроме self-action);
- создание сообщения в чате -> уведомление активных участников чата, кроме автора;
- изменение статуса заявки -> уведомление владельца заявки (кроме self-action);
- постановка email-рассылки в очередь через API без отдельного queued-уведомления в центре.

## Центр уведомлений на фронтенде (v1)

- Источник истины: backend-таблица `user_notifications`.
- UI колокольчика:
  - desktop: `popover` по кнопке колокольчика;
  - mobile: `drawer` по кнопке колокольчика.
- Загрузка данных:
  - `unread-count` опрашивается через `GET /api/v1/notifications/unread-count` примерно раз в 45 секунд, пока пользователь аутентифицирован;
  - список загружается через `GET /api/v1/notifications` при открытии центра, после `mark read`/`mark all`, и поддерживает `limit/offset` для кнопки «Показать еще».
- Действия:
  - `PATCH /api/v1/notifications/{notification_id}/read`;
  - `PATCH /api/v1/notifications/read-all`.
- Слой toast/snackbar — только UX-слой и не заменяет персистентные записи в `user_notifications`.
- Push dedupe выполняется по `notification.id`, чтобы одно и то же непрочитанное уведомление не показывалось повторно.
- При приходе 3+ новых уведомлений вместо пачки toast показывается один агрегированный push.
- В UI центра однотипные непрочитанные уведомления агрегируются по типу (например: «Новые сообщения (N)»), чтобы не показывать длинную однообразную ленту.
- Для `message.created` push suppress включается, если пользователь уже открыт в соответствующем `/offers/{offer_id}/workspace`.

## Поведение realtime для чата

- Chat realtime использует один WebSocket-клиент через `ChatRealtimeProvider/chatSocketClient` на пользователя.
- Отдельный WebSocket для центра уведомлений не используется: центр остается polling-based.
- Если пользователь уже подписан на чат по websocket (то есть читает сообщения в реальном времени), запись `message.created` в центр уведомлений для него не создается.
- Если чат не открыт и пользователь не подписан, уведомление сохраняется в центр как обычно.

## Email Delivery Flow (worker feedback)

### Типы и семантика

- `email.sent` — письмо реально отправлено SMTP и это подтверждено `notifications_worker`.
- `email.failed` — SMTP-отправка реально завершилась ошибкой в `notifications_worker`.

Важно: `email.sent` больше не должен означать "поставлено в очередь".

### Контракт delivery-result события

Worker публикует в `app.events`:
- `email.delivery.succeeded`
- `email.delivery.failed`

Payload:

```json
{
  "event_type": "email.delivery.failed",
  "correlation_id": "uuid",
  "recipient_user_id": "user-id",
  "request_id": 42,
  "offer_id": 100,
  "to_email": "contractor@example.com",
  "safe_error_code": "SMTP_AUTH_FAILED",
  "safe_error_message": "Не удалось отправить письмо. Проверьте настройки почты.",
  "occurred_at": "2026-05-15T12:00:00Z"
}
```

Правила:
- `correlation_id` обязателен (если старый payload без него — worker генерирует fallback и логирует warning).
- `recipient_user_id` обязателен для пользовательского уведомления.
- `request_id/offer_id` опциональны.
- Никаких stack trace, SMTP password, token и внутренних exception details в event payload.

### RabbitMQ routing

- queue отправки писем: `notify.email` (`email.send`)
- queue результатов доставки: `notify.email.delivery`
- routing keys результатов: `email.delivery.succeeded`, `email.delivery.failed`

### Как backend формирует user_notifications

Backend consumer читает `notify.email.delivery` и через `NotificationService` создает:
- `email.sent` (severity `success`) при `email.delivery.succeeded`
- `email.failed` (severity `error`) при `email.delivery.failed`

Если есть `request_id/offer_id`, добавляются `entity_type/entity_id/link_url`.

### Dedupe (best effort, без миграции)

Перед созданием уведомления backend проверяет наличие записи с тем же:
- `type` (`email.sent` или `email.failed`)
- `user_id`
- `payload.correlation_id`

При совпадении дубль не создается.

## TODO / Уточнения

- Полноценный retry policy (с четкой финализацией delivery result).
- Dead-letter queue для невалидных/необрабатываемых событий.
- Явный dedupe_key в БД (отдельное поле + индекс).
- Админский email delivery audit/log.
- UI-фильтры уведомлений через backend query params.
- Realtime push для самого центра уведомлений (сейчас polling-based).
- ws-ticket/cookie-based WS auth вместо `access token` в query-string.
- user notification preferences.
