# Telegram Bot (`/tg_bot`)

## Граница ответственности документа

Этот README описывает legacy Telegram-модуль.
Единый источник правды по основным окружениям и запуску проекта:
- `docs/environments.md`

Статус модуля:
- `tg_bot` — legacy и в основном root compose выключен по умолчанию.
- `tg_bot/docker-compose.yml` — standalone-сценарий для отдельных задач/rollback, не основной путь запуска продукта.

## Назначение

Бот на `aiogram` обрабатывает команды `/start` и `/info`, обращается в backend API и:
- выдаёт ссылку на регистрацию,
- показывает статус модерации,
- показывает список открытых заявок с кнопкой перехода в веб.

## Основной сценарий работы

1. Пользователь пишет `/start`.
2. Бот отправляет `POST /api/v1/tg/start` в backend.
3. По полю `action` в ответе backend бот делает одно из действий:
   - `register` — показывает кнопку регистрации;
   - `pending` — сообщает, что заявка на проверке;
   - `open_requests` — показывает список открытых заявок и ссылки.

Команда `/info` выводит справку о процессе.

---

## Конфигурация (ENV)

Бот читает `.env` через `pydantic-settings`.

Обязательные переменные:

- `BOT_TOKEN` — токен Telegram-бота.
- `BACKEND_BASE_URL` — базовый URL backend (куда бот ходит сервер-сервер).

Опциональные:

- `PUBLIC_BACKEND_BASE_URL` — публичный базовый URL для ссылок, которые бот отправляет пользователю.
  - Если не задан, используется `BACKEND_BASE_URL`.
- `REQUEST_TIMEOUT_SECONDS` — timeout HTTP запросов к backend (по умолчанию `5.0`).

Пример `.env`:

```env
BOT_TOKEN=123456:ABCDEF...
BACKEND_BASE_URL=http://gateway
PUBLIC_BACKEND_BASE_URL=https://<your-ngrok-domain>
REQUEST_TIMEOUT_SECONDS=5
```

> Если бот работает в docker-сети с backend/gateway, обычно удобно ставить `BACKEND_BASE_URL=http://gateway`.

---

## Docker и сеть

`tg_bot/docker-compose.yml` запускает сервис `tg_bot` в внешней сети `project_net`.

Это значит, что bot-контейнер может обращаться к `gateway`/`backend` по именам сервисов внутри этой сети.

### Запуск

1. Убедиться, что сеть существует:

```bash
docker network create project_net
```

2. Поднять основной root-стек проекта (или минимум gateway+backend в совместимой сети).

3. Поднять бота:

```bash
docker compose -f tg_bot/docker-compose.yml up -d --build
```

Логи:

```bash
docker compose -f tg_bot/docker-compose.yml logs -f tg_bot
```

---

## Как формируются ссылки для пользователя

Бот получает от backend относительные ссылки и преобразует их в абсолютные:
- если ссылка уже абсолютная (`http://` / `https://`) — оставляет как есть;
- если относительная — добавляет базу из `PUBLIC_BACKEND_BASE_URL` (или `BACKEND_BASE_URL`).

Поэтому для прод/демо обычно важно задать публичную базу (например, ngrok URL), чтобы ссылки открывались у пользователя извне.

---

## Обработка ошибок

Если backend недоступен или вернул HTTP-ошибку, бот отвечает пользователю:
- «Сервис временно недоступен. Попробуйте позже.»

Это защищает UX от падений при временных проблемах backend.

## Связанные документы

- `docs/runtime-architecture.md`
- `docs/auth-and-onboarding.md`
- `docs/environments.md`
