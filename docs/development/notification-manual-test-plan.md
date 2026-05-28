# План Ручного Тестирования Уведомлений

## Цель

Проверить актуальную реализацию центра уведомлений после унификации событий:

- `offer.updated` вместо `offer.files_changed`;
- `offer.status_changed` вместо отдельных `offer.accepted/rejected/deleted`;
- явный `user.review_required`;
- подключенные потоки `system.warning` и `ui.plan.mutation.*`.

## Подготовка

1. Развернуть окружение `dev`/`test` с рабочими:
   - backend;
   - worker/consumer process notifications;
   - RabbitMQ;
   - frontend;
   - Keycloak.
2. Подготовить пользователей:
   - `admin`/`superadmin`;
   - `project_manager` (владелец заявки);
   - `contractor` с активной привязкой Keycloak;
   - `contractor_manual` без завершенной привязки Keycloak (для негативного сценария).
3. Открыть минимум 2 браузерные сессии (например, PM и Contractor) для проверки realtime.

## Сценарии

### 1. `offer.updated` при изменении файлов

1. Контрагент добавляет файл в свое КП.
2. Контрагент удаляет файл из КП.
3. Проверить, что создаются уведомления типа `offer.updated`:
   - у ответственного по заявке;
   - у автора КП;
   - без уведомления автора действия.
4. Проверить payload (`file_ids`, `changed_file_count`, `offer_author_user_id`).

Ожидание: единый тип `offer.updated`, дубля `offer.files_changed` нет.

### 2. `offer.updated` при изменении суммы

1. Изменить сумму КП.
2. Проверить уведомление `offer.updated` у тех же получателей.
3. Проверить payload (`old_offer_amount`, `new_offer_amount`).

Ожидание: событие суммы идет тем же типом `offer.updated`.

### 3. `offer.status_changed` для accepted/rejected/deleted

1. Сменить статус КП на `accepted`, затем `rejected`, затем `deleted` (на отдельных КП).
2. Проверить, что в `user_notifications.type` всегда `offer.status_changed`.
3. Проверить заголовок уведомления по `new_status`.

Ожидание: отдельные типы `offer.accepted/rejected/deleted` не создаются.

### 4. `user.review_required` при TG-регистрации

1. Зарегистрировать нового контрагента через TG registration flow.
2. Проверить уведомления у `admin/superadmin`.

Ожидание: появляется `user.review_required`, автор события не уведомляется сам.

### 5. `user.review_required` при переводе пользователя в review

1. Админ меняет статус пользователя на `review`.
2. Проверить:
   - `user.status_changed` создан;
   - `user.review_required` создан;
   - оба дошли realtime.

Ожидание: moderation-событие создается явно.

### 6. Фильтр Keycloak для контрагентов

1. Сгенерировать business-событие с контрагентом-получателем (`request.created`/`request.reopened`/`offer.status_changed`).
2. Проверить:
   - контрагент с активным Keycloak получает уведомление;
   - `contractor_manual` без привязки не получает.

Ожидание: фильтр получателей работает стабильно.

### 7. `system.warning`

1. Опубликовать process event `system.warning` с явными `recipient_user_ids`.
2. Проверить доставку:
   - запись в `user_notifications`;
   - realtime `notification.created`;
   - отображение в push-слое и центре.

Ожидание: consumer-path и UI отображение работают.

### 8. `ui.plan.mutation.success/error`

1. В UI выполнить успешные операции в плане: create/update/delegate/close/remove.
2. Вызвать ошибку в одной из операций (например, некорректные данные/конфликт).
3. Проверить:
   - toast `top-center`;
   - отсутствуют записи в `user_notifications`.

Ожидание: это system-ui путь, не бизнес-уведомления центра.

## Регрессии

1. Убедиться, что `message.created`, `request.files_changed`, `request.status_changed`, `plan.assigned`, `plan.updated` продолжают работать.
2. Проверить, что `/ws/realtime` продолжает отправлять `notification.created`.
3. Проверить отсутствие дублей по `event_id`/`dedupe_key`.

## Критерии приемки

- Новые типы (`offer.updated`, `offer.status_changed`, `user.review_required`) создаются и отображаются корректно.
- Устаревшие типы (`offer.files_changed`, `offer.accepted/rejected/deleted`) не создаются новым кодом.
- `system.warning` и `ui.plan.mutation.*` работают в своих каналах (business vs system_ui).
- Получатели соответствуют матрице ролей и фильтру Keycloak.
