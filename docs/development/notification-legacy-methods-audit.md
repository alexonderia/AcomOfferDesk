# NotificationService Legacy `notify_*` Methods Audit

## Purpose

This document audits `notify_*` methods in `backend/app/services/notifications.py` and records current usage, compatibility role, and next-step recommendations.

## Scope

- Source class: `NotificationService` (`backend/app/services/notifications.py`)
- Search targets:
  - `notify_offer_created`
  - `notify_message_created`
  - `notify_email_sent`
  - `notify_email_failed`
  - `notify_request_status_changed`
  - `notify_system_warning`
  - `NotificationService(`
  - `.create_for_user(`
  - `.create_many_for_users(`

## Findings Table

| Метод | Назначение | Тип уведомления | Пишет в `user_notifications` | Realtime через общий `create_for_user` | Используется сейчас | Где используется | Новый основной путь | Рекомендация |
|---|---|---|---|---|---|---|---|---|
| `notify_offer_created` | Создать уведомление о новом КП для получателя, кроме инициатора | `offer.created` | yes | yes (`create_for_user`) | yes | `backend/app/services/offers.py` (fallback when process event is not scheduled); unit tests in `backend/tests/unit/test_notification_service_unit.py` | Process pipeline: `offer.created` -> `ProcessNotificationEventHandler` -> `create_for_user` | Оставить как compatibility fallback; пометить legacy-кандидатом, удалять только после подтверждения, что fallback-ветка больше не нужна. |
| `notify_message_created` | Создать уведомления о новом сообщении участникам чата, кроме автора | `message.created` | yes | yes (`create_many_for_users` -> `create_for_user`) | yes | `backend/app/services/offers.py` (fallback when process event is not scheduled); unit tests in `backend/tests/unit/test_notification_service_unit.py` | Process pipeline: `message.created` -> `ProcessNotificationEventHandler` -> `create_many_for_users` | Оставить как compatibility fallback; пометить legacy-кандидатом, удалять только после проверки fallback-пути и тестов. |
| `notify_email_sent` | Создать уведомление об успешной доставке email | `email.sent` | yes | yes (`create_for_user`) | yes | `backend/app/services/email_delivery_events.py` | Email delivery flow (`email.delivery.succeeded`) -> `EmailDeliveryEventHandler` -> `NotificationService.notify_email_sent` | Оставить; не удалять, метод используется в текущем email delivery flow. |
| `notify_email_failed` | Создать уведомление об ошибке доставки email с безопасным текстом ошибки | `email.failed` | yes | yes (`create_for_user`) | yes | `backend/app/services/email_delivery_events.py` | Email delivery flow (`email.delivery.failed`) -> `EmailDeliveryEventHandler` -> `NotificationService.notify_email_failed` | Оставить; не удалять, метод используется в текущем email delivery flow. |
| `notify_request_status_changed` | Создать уведомление о смене статуса заявки для владельца, кроме инициатора | `request.status_changed` | yes | yes (`create_for_user`) | yes | `backend/app/services/requests.py` (fallback when process event is not scheduled); unit tests in `backend/tests/unit/test_notification_service_unit.py` | Process pipeline: `request.status_changed` -> `ProcessNotificationEventHandler` -> `create_for_user` | Оставить как compatibility fallback; пометить legacy-кандидатом и удалить только после подтверждения, что fallback-ветка не используется. |
| `notify_system_warning` | Создать системное предупреждение для явного получателя | `system.warning` | yes | yes (`create_for_user`) | no direct calls found | Прямых вызовов в backend/tests не найдено (кроме определения в `notifications.py`) | Process pipeline currently uses `system.warning` handler with `create_many_for_users` in `process_notification_events.py` | Пометить как legacy/standby: оставить до появления явного producer- или API-use-case; перед удалением требуется подтверждение. |

## Notes

- All `notify_*` methods above ultimately use `create_for_user` / `create_many_for_users`, therefore they write to `user_notifications` and emit realtime `notification.created` via common path.
- For `notify_system_warning`, direct call sites were not found in production code or tests during this audit.
- For methods marked legacy-candidate, repository search alone does not prove runtime impossibility. Confirmation is required before removal.

## Current Decision (2026-05-22)

| Метод | Решение | Почему | Условие пересмотра |
|---|---|---|---|
| `notify_email_sent` | Оставить как рабочий (non-legacy) | Метод является частью активного `email delivery flow` через `EmailDeliveryEventHandler` | Пересматривать только при явной замене email-flow на другой подтвержденный путь |
| `notify_email_failed` | Оставить как рабочий (non-legacy) | Метод является частью активного `email delivery flow` и формирует безопасный текст ошибки | Пересматривать только при явной замене email-flow на другой подтвержденный путь |
| `notify_offer_created` | Оставить как fallback/compatibility | Вызывается в `OfferService` только когда process-event не удалось запланировать (`is_scheduled == False`) | Удалять только после подтверждения, что fallback-ветка недостижима и не нужна в проде |
| `notify_message_created` | Оставить как fallback/compatibility | Вызывается в `OfferService` только когда process-event не удалось запланировать (`is_scheduled == False`) | Удалять только после подтверждения, что fallback-ветка недостижима и не нужна в проде |
| `notify_request_status_changed` | Оставить как fallback/compatibility | Вызывается в `RequestService` только когда process-event не удалось запланировать (`is_scheduled == False`) | Удалять только после подтверждения, что fallback-ветка недостижима и не нужна в проде |
| `notify_system_warning` | Оставить в standby до отдельного решения | Прямых вызовов не найдено, но метод остается запасным прямым API для точечного предупреждения | Первый кандидат на удаление после подтверждения отсутствия реальных producer/use-case |

## Fallback Layer Definition

`Fallback layer` в текущем проекте означает совместимый резервный путь доставки уведомления напрямую через `NotificationService.notify_*`, который используется только если основной process pipeline не удалось запланировать в текущем use-case.

Сейчас это выражено явной конструкцией в сервисах:

- `event` публикуется в process pipeline;
- если `is_scheduled == False`, вызывается соответствующий `notify_*` метод;
- результат все равно идет через общий `create_for_user`/`create_many_for_users` (запись в `user_notifications` + realtime `notification.created`).
