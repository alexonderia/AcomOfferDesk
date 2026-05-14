# Notification Service (Backend)

## Purpose

`NotificationService` is the backend entrypoint for user notification center data.  
Notifications are created in the backend service layer, then persisted into `user_notifications`.

This keeps business events and notification ownership rules in one place:
- who should receive notification;
- when self-notifications must be skipped;
- what safe text/link/payload should be produced.

## Why not DB triggers

DB triggers were intentionally not used because:
- recipient selection depends on business context from services (offer owner, chat participants, initiator);
- notification text/link needs application-level knowledge of routes and entities;
- trigger-side logic is harder to test and evolve than service-level use cases.

## Supported Notification Types (v1)

- `offer.created`
- `message.created`
- `email.sent`
- `email.failed`
- `request.status_changed`
- `system.warning`

Severity values:
- `info`
- `success`
- `warning`
- `error`

## API Endpoints

- `GET /api/v1/notifications`
  - current user notifications only
  - sorted by `created_at DESC`
  - supports `limit` and `offset`
- `GET /api/v1/notifications/unread-count`
  - returns unread count for current user
- `PATCH /api/v1/notifications/{notification_id}/read`
  - marks one notification as read for current user
  - returns 404 if not found or belongs to another user
- `PATCH /api/v1/notifications/read-all`
  - marks all unread notifications for current user

## Integrated Scenarios

Already connected:
- offer created -> notify request owner (except self-action);
- chat message created -> notify active chat participants except author;
- request status changed -> notify request owner (except self-action);
- manual request email notification API success -> notify initiator (`email.sent`).

## TODO / Clarifications

- `email.failed` and real delivery confirmation currently require status feedback from `notifications_worker`.
- At the moment backend enqueues email jobs through RabbitMQ; actual SMTP delivery happens asynchronously in worker.
- For precise `email.sent`/`email.failed` delivery notifications, add a worker -> backend status event contract (or equivalent callback path) and persist via `NotificationService`.

