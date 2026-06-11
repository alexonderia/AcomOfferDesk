# MAX-бот AcomOfferDesk

MAX-бот — thin-client для мессенджера MAX. Он принимает команды пользователя, вызывает backend API `/api/v1/max/*` и показывает результат. Бизнес-логика, доступы и данные заявок живут в backend.

## Отличие от legacy Telegram-бота

- Legacy `tg_bot` использует deprecated endpoints `/api/v1/tg/*` и флаг `LEGACY_TELEGRAM_ENABLED`.
- MAX-бот работает через отдельный контур `/api/v1/max/*` и настройки `MAX_*`.
- MAX-бот не обращается к БД напрямую.

## Где хранятся MAX-связки

Отдельной таблицы `max_users` нет. Идентичность хранится в универсальных таблицах:

- `user_auth_accounts` с `provider = 'max'` и `external_subject_id = str(max_user_id)`
- `user_contact_channels` с `channel_type = 'max'` и `channel_value = str(max_user_id)`

## Переменные окружения

См. `env.example`:

- `MAX_BOT_TOKEN` — токен бота MAX (обязателен)
- `BACKEND_BASE_URL` — внутренний URL backend в docker-сети, например `http://backend:8000`
- `PUBLIC_BACKEND_BASE_URL` — публичный URL для абсолютных ссылок пользователю
- `MAX_BOT_TIMEOUT_SECONDS` — таймаут HTTP-запросов к backend
- `MAX_POLLING_ENABLED` — включить long polling (MVP)

Backend использует отдельные переменные `MAX_BOT_ENABLED`, `MAX_LINK_SECRET`, TTL токенов — см. корневые `.env*.example`.

## Запуск в составе проекта

```bash
docker compose up -d --build
```

При запуске из корня проекта сервис `max_bot` берет `MAX_BOT_TOKEN`, `MAX_BOT_ENABLED`, `MAX_LINK_SECRET`, `PUBLIC_BACKEND_BASE_URL` и `WEB_BASE_URL` из root runtime env (`${APP_RUNTIME_ENV_FILE:-./.env}` или другого root env-файла, выбранного compose-слоем).

`max_bot/.env` для root-запуска не нужен.

По умолчанию MAX должен быть выключен:

- `MAX_BOT_ENABLED=false`
- для включения задайте `MAX_BOT_ENABLED=true`, `MAX_BOT_TOKEN` и `MAX_LINK_SECRET`

Если `MAX_BOT_ENABLED=false`, контейнер `max_bot` можно не трогать или остановить отдельно:

```bash
docker compose stop max_bot
```

## Standalone-запуск для отладки

```bash
cd max_bot
cp env.example .env
docker compose up --build
```

`max_bot/.env` используется только для standalone-отладки из директории `max_bot`.

## Команды

При старте бот регистрирует команды через `PATCH /me`. В MAX нет постоянной reply-клавиатуры как в Telegram: команды доступны через ввод `/` в поле сообщения. Под заявками остаются только кнопки-ссылки «Открыть заявку».

- `/start` — регистрация, статус доступа или список открытых заявок
- `/info` — краткая инструкция

## Основной сценарий пользователя

1. Пользователь отправляет `/start`.
2. Backend определяет состояние MAX-связки и пользователя.
3. Бот показывает кнопку регистрации, сообщение о модерации, список заявок или безопасное сообщение о блокировке.
4. После активации контрагент получает открытые заявки со ссылками в web.

## Push-уведомления

Исходящие уведомления в MAX (новые заявки, смена статуса, активация доступа) публикуются backend в RabbitMQ и доставляются `notifications_worker` (`notifications_worker/app/max_sender.py`, по аналогии с `tg_sender.py`).

## Отключение MAX-бота

1. Установите `MAX_BOT_ENABLED=false` в runtime env backend.
2. При необходимости остановите контейнер: `docker compose stop max_bot`.

## Переход на webhook (будущее)

MVP использует polling (`MAX_POLLING_ENABLED=true`). Для production рекомендуется webhook:

1. Развернуть HTTP endpoint (например FastAPI + `maxapi[fastapi]`).
2. Зарегистрировать подписку через MAX Bot API `POST /subscriptions`.
3. Отключить polling и направить входящие события на webhook endpoint.
4. Пример: `maxapi` examples `09_webhook_bot.py`.

## Проверка работоспособности

```bash
docker compose ps max_bot
docker compose logs -f max_bot
```

В MAX отправьте `/info` и `/start`. При ошибках backend пользователь увидит: «Сервис временно недоступен. Попробуйте позже.»

## Тесты

```bash
cd max_bot
pip install -r requirements.txt pytest pytest-asyncio
pytest
```
