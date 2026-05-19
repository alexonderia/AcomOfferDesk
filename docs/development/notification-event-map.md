# Карта Событий Уведомлений

## Назначение

Документ фиксирует карту уведомлений в backend/frontend и классифицирует каждое событие как:

- `system_ui` — локальная реакция интерфейса на текущей странице, не сохраняется в `user_notifications`.
- `business` — бизнес-событие, важное независимо от открытой страницы; сохраняется в `user_notifications`, показывается в центре уведомлений и предназначено для доставки через realtime.

## Правила Классификации

- `system_ui`
  - Пользователь сам инициировал действие и сразу видит результат в текущем сценарии.
  - Не сохраняется в `user_notifications`.
  - Целевое размещение: toast `top-center` (сейчас во многих местах используется inline `Alert`, см. статус и комментарии).

- `business`
  - Событие важно пользователю независимо от текущей страницы.
  - Сохраняется в `user_notifications`.
  - Целевое размещение: бизнес-toast `bottom-right` + центр уведомлений.
  - Основной push-механизм: realtime доставка через `/api/v1/ws/realtime` (`notification.created`), polling остается только как sync/fallback.

## Таблица Событий

| event_type | категория | фиксировать в user_notifications | размещение toast | источник события | получатели | link_url | payload | текущий статус | комментарий |
|---|---|---|---|---|---|---|---|---|---|
| request.created | business | yes | bottom-right | `backend/app/services/requests.py:create_request` -> process event -> `process_notification_events.py` | `responsible_user_id`/`recipient_user_ids` из payload (матрица получателей требует уточнения) | `/requests/{request_id}` | `request_id`, `actor_user_id`, dedupe-ключи | partial | Producer/handler подключены; при отсутствии получателей кроме автора событие пропускается (TODO по матрице получателей). |
| request.status_changed | business | yes | bottom-right | `backend/app/services/requests.py` -> process event -> `process_notification_events.py` | Владелец заявки (без автора события) | `/requests/{request_id}` | `old_status`, `new_status`, `actor_user_id`, dedupe-ключи | implemented | Реализовано: сохраняется и показывается в центре/пуш-слое. |
| request.assigned | business | yes | bottom-right | Отдельный producer не найден | Назначенный пользователь и/или менеджер (требует уточнения) | `/requests/{request_id}` | `request_id`, `assignee_user_id`, `actor_user_id` | todo | Требуется формализация бизнес-правила назначения. |
| request.responsible_changed | business | yes | bottom-right | `backend/app/services/requests.py:update_request` -> process event -> `process_notification_events.py` | Старый и новый ответственный (без автора события) | `/requests/{request_id}` | `old_responsible_user_id`, `new_responsible_user_id`, `actor_user_id`, dedupe-ключи | implemented | Реализовано через publish-after-commit и dedupe. |
| request.deadline_changed | business | yes | bottom-right | `backend/app/services/requests.py:update_request` -> process event -> `process_notification_events.py` | Ответственный по заявке (без автора события) | `/requests/{request_id}` | `old_deadline`, `new_deadline`, `actor_user_id`, dedupe-ключи | implemented | Реализовано через publish-after-commit и dedupe. |
| request.closed | business | yes | bottom-right | Покрыто через `request.status_changed` при `new_status=closed` | Владелец заявки | `/requests/{request_id}` | `old_status`, `new_status=closed` | partial | Работает как частный случай общего события смены статуса. |
| request.cancelled | business | yes | bottom-right | Покрыто через `request.status_changed` при `new_status=cancelled` | Владелец заявки | `/requests/{request_id}` | `old_status`, `new_status=cancelled` | partial | Работает как частный случай общего события смены статуса. |
| request.reopened | business | yes | bottom-right | Покрыто через `request.status_changed` при `new_status=open` | Владелец заявки | `/requests/{request_id}` | `old_status`, `new_status=open` | partial | Работает как частный случай общего события смены статуса. |
| offer.created | business | yes | bottom-right | `backend/app/services/offers.py:create_offer` -> process event -> `process_notification_events.py` | Владелец заявки (без автора события) | `/requests/{request_id}` или `/offers/{offer_id}/workspace` | `request_id`, `offer_id`, `actor_user_id`, dedupe-ключи | implemented | Реализовано: сохраняется и показывается в центре/пуш-слое. |
| offer.accepted | business | yes | bottom-right | `backend/app/services/offers.py:update_status` -> process event -> `process_notification_events.py` | Владелец КП и владелец заявки (без автора события) | `/offers/{offer_id}/workspace` | `offer_id`, `request_id`, `actor_user_id`, `old_status`, `new_status`, dedupe-ключи | implemented | Реализовано через publish-after-commit и dedupe. |
| offer.rejected | business | yes | bottom-right | `backend/app/services/offers.py:update_status` -> process event -> `process_notification_events.py` | Владелец КП и владелец заявки (без автора события) | `/offers/{offer_id}/workspace` | `offer_id`, `request_id`, `actor_user_id`, `old_status`, `new_status`, dedupe-ключи | implemented | Реализовано через publish-after-commit и dedupe. |
| offer.deleted | business | yes | bottom-right | `backend/app/services/offers.py:update_status` -> process event -> `process_notification_events.py` | Владелец КП и владелец заявки (без автора события) | `/offers/{offer_id}/workspace` | `offer_id`, `request_id`, `actor_user_id`, `old_status`, `new_status`, dedupe-ключи | implemented | Реализовано через publish-after-commit и dedupe. |
| offer.updated | business | yes | bottom-right | Изменения суммы/файлов/статуса есть, единого `offer.updated` нет | Участники КП (требует уточнения) | `/offers/{offer_id}/workspace` | набор измененных полей (требует уточнения) | todo | Нужна явная область применения события. |
| message.created | business | yes | bottom-right | `backend/app/services/offers.py:create_message` -> process event -> `process_notification_events.py` | Участники чата кроме автора (с учетом подавления в открытом чате) | `/offers/{offer_id}/workspace` | `request_id`, `offer_id`, `chat_id`, `message_id`, `actor_user_id` | implemented | Реализовано: сохраняется и показывается в центре/пуш-слое. |
| message.read | system_ui | no | none | WebSocket-событие чата (`/api/v1/ws/chat`, `message.read`) | Активные участники чата | none | `chat_id`, `user_id`, `message_ids`, `last_read_message_id` | implemented | Сигнал чата в реальном времени, не центр уведомлений. |
| chat.participant_joined | business | yes | bottom-right | В контрактах ws/notification pipeline не найдено | Участники чата (требует уточнения) | `/offers/{offer_id}/workspace` | `chat_id`, `user_id` | todo | Не реализовано, применимость нужно уточнить. |
| chat.participant_left | business | yes | bottom-right | В контрактах ws/notification pipeline не найдено | Участники чата (требует уточнения) | `/offers/{offer_id}/workspace` | `chat_id`, `user_id` | todo | Не реализовано, применимость нужно уточнить. |
| request.file_attached | business | yes | bottom-right | `RequestService.attach_file` есть, события уведомления нет | Владелец заявки и участники (требует уточнения) | `/requests/{request_id}` | `request_id`, `file_id`, `actor_user_id` | todo | Прикрепление файла есть, уведомление нет. |
| offer.file_attached | business | yes | bottom-right | `OfferService.attach_file` есть, события уведомления нет | Участники КП (требует уточнения) | `/offers/{offer_id}/workspace` | `offer_id`, `file_id`, `actor_user_id` | todo | Прикрепление файла есть, уведомление нет. |
| message.file_attached | business | yes | bottom-right | Вложения идут через `message.created`, отдельного типа нет | Участники чата кроме автора | `/offers/{offer_id}/workspace` | `message_id`, `chat_id`, метаданные вложений | partial | Покрыто неявно через `message.created` с вложениями. |
| email.sent | business | yes | bottom-right | `EmailDeliveryEventHandler` из `email.delivery.succeeded` | `recipient_user_id` из payload доставки | `/requests/{request_id}` или `/offers/{offer_id}/workspace` | `correlation_id`, `request_id/offer_id`, `to_email` | implemented | Реализовано: сохраняется и показывается в центре/пуш-слое. |
| email.failed | business | yes | bottom-right | `EmailDeliveryEventHandler` из `email.delivery.failed` | `recipient_user_id` из payload доставки | `/requests/{request_id}` или `/offers/{offer_id}/workspace` | `correlation_id`, `safe_error_code`, безопасный текст ошибки | implemented | Реализовано: сохраняется и показывается в центре/пуш-слое. |
| user.review_required | business | yes | bottom-right | Producer в текущем user-flow не найден | Пользователь на проверке, менеджеры/админы (требует уточнения) | `/auth/account-state` или admin route (требует уточнения) | `user_id`, `status`, `actor_user_id` | todo | Нужна фиксация триггера и матрицы получателей. |
| user.approved | business | yes | bottom-right | Producer в moderation flow не найден | Подтвержденный пользователь | профиль/домашняя страница (требует уточнения) | `user_id`, `old_status`, `new_status` | todo | Бизнес-смысл есть, события в коде нет. |
| user.rejected | business | yes | bottom-right | Producer в moderation flow не найден | Отклоненный пользователь | профиль/домашняя страница (требует уточнения) | `user_id`, `old_status`, `new_status`, причина (требует уточнения) | todo | Нужны правила по видимости причины. |
| user.blocked | business | yes | bottom-right | Producer в moderation flow не найден | Заблокированный пользователь + админы (требует уточнения) | профиль/домашняя страница (требует уточнения) | `user_id`, `old_status`, `new_status` | todo | В текущих контрактах отсутствует. |
| plan.assigned | business | yes | bottom-right | API делегирования плана есть (`delegatePlan`), события уведомления нет | Назначенный пользователь | маршрут dashboard плана (требует уточнения) | `plan_id`, `assignee_user_id`, `actor_user_id` | todo | Сейчас есть только локальные сообщения об успехе/ошибке. |
| plan.updated | business | yes | bottom-right | API обновления плана есть, события уведомления нет | Владелец/участники плана (требует уточнения) | маршрут dashboard плана (требует уточнения) | `plan_id`, измененные поля | todo | Контракта backend-уведомления нет. |
| plan.completed | business | yes | bottom-right | API закрытия плана есть, события уведомления нет | Владелец/менеджер плана (требует уточнения) | маршрут dashboard плана (требует уточнения) | `plan_id`, метаданные завершения | todo | Может трактоваться через close, но явного события нет. |
| plan.overdue | business | yes | bottom-right | Планировщик/producer просрочки не найден | Владелец/менеджер плана (требует уточнения) | маршрут dashboard плана (требует уточнения) | `plan_id`, дата срока, величина просрочки | todo | Нужен источник обнаружения просрочки и правила отправки. |
| system.warning | business | yes | bottom-right | Обработчик есть в `process_notification_events.py`, producer в сервисах не найден | Явно переданные получатели из payload | payload `link_url` или none | произвольный payload + `event_id`/`dedupe_key` | partial | Consumer-путь готов, публикация в бизнес-сервисах не подключена. |
| system.worker_failed | business | yes | bottom-right | Мост из ошибок воркера в notification pipeline не найден | Ops/admin получатели (требует уточнения) | worker/admin route (требует уточнения) | `worker_name`, `error_code`, корреляционные поля | todo | В текущем process/email flow не реализовано. |
| ui.request.save.success | system_ui | no | top-center | local API result (`RequestDetailsView`) | Текущий пользователь страницы | none | локальный текст | implemented | Показывается через единый system toast facade. |
| ui.request.save.error | system_ui | no | top-center | local API result (`RequestDetailsView`) | Текущий пользователь страницы | none | локальный текст ошибки | implemented | Показывается через единый system toast facade. |
| ui.request.create.error | system_ui | no | top-center | local API result (`CreateRequestPage`) | Текущий пользователь страницы | none | локальный текст ошибки | implemented | Ошибка создания заявки показывается как system toast. |
| ui.plan.mutation.success | system_ui | no | top-center | `web/src/features/dashboard/model/usePlanDashboard.ts` | Текущий пользователь страницы | none | локальный текст успеха | partial | Локальные сообщения для create/update/delegate/close/remove. |
| ui.plan.mutation.error | system_ui | no | top-center | `web/src/features/dashboard/model/usePlanDashboard.ts` | Текущий пользователь страницы | none | локальный текст ошибки | partial | Только локальная ошибка в UI. |
| ui.user.create.success | system_ui | no | top-center | local API result (`useAdminPage`) | Текущий пользователь страницы | none | локальный текст успеха | implemented | Показывается через единый system toast facade. |
| ui.user.create.error | system_ui | no | top-center | local API result (`useAdminPage`) | Текущий пользователь страницы | none | локальный текст ошибки | implemented | Показывается через единый system toast facade. |
| ui.profile.review.submit.success | system_ui | no | top-center | local API result (`AccountStatePage`) | Текущий пользователь страницы | none | локальный текст успеха | implemented | Отправка на проверку подтверждается system toast. |
| ui.file.upload.normative.success | system_ui | no | top-center | local API result (`NormativeFileButton`) | Текущий пользователь страницы | none | локальный текст успеха | implemented | Компонент использует system toast facade для success/error. |
| ui.feedback.submit.success | system_ui | no | top-center | local API result (`FeedbackButton`) | Текущий пользователь страницы | none | локальный текст успеха | implemented | Компонент использует system toast facade для success/error. |

## Примечания

- Бизнес-пуши реализованы через `NotificationsPushLayer` и приходят по realtime-событию `notification.created` (`/api/v1/ws/realtime`), без запуска push от роста unread-count polling.
- Визуальные иконки в центре уведомлений сейчас явно сопоставлены с типами: `offer.created`, `offer.accepted`, `offer.rejected`, `offer.deleted`, `message.created`, `request.created`, `request.responsible_changed`, `request.deadline_changed`, `request.status_changed`, `email.sent`, `email.failed`, `system.warning`.
- `message.read` — это событие чата в realtime-канале и его следует оставлять вне `user_notifications`, пока бизнес-требования не изменятся.
