# Ручная проверка уведомлений

Поднять backend, notifications worker, RabbitMQ, PostgreSQL и SMTP test account. Войти через IAM подготовленными пользователями основных ролей.

Проверить:

- создание/изменение заявки и предложения;
- email активным и дополнительным контрагентам;
- приглашение ведёт на действующий portal/login URL и не содержит legacy auth token;
- unit visibility исключает скрытых или недоступных контрагентов;
- notification preferences отключают соответствующий канал;
- worker retry/deduplication не создают дубликаты;
- ссылки ведут на разрешённые backend/frontend routes;
- пользователь без IAM session не получает доступ по одной ссылке из письма.
