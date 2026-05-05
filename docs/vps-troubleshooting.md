# VPS: типовые сбои (кратко)

## Граница ответственности документа

Этот документ — быстрый troubleshooting по типовым сбоям на VPS.

Смежные документы:
- [order_database на VPS](./order-database-vps.md)
- [Окружения](./environments.md)
- [Чек-лист релиза](./release-checklist.md)

Полный журнал с контекстом: **`vvv-web/devops_manual`** — [docs/acom-offer-desk-archive/vps-troubleshooting-2026-03.md](https://github.com/vvv-web/devops_manual/blob/acom-offer-postgres-vps-2026-03-31/docs/acom-offer-desk-archive/vps-troubleshooting-2026-03.md).

---

## Keycloak / OAuth: **500** на `/api/v1/auth/callback`, в логах `user_auth_accounts` does not exist

**Причина:** схема **`order_database`** на VPS не доведена миграциями Flyway (частый случай — **пустой** каталог **`/opt/order_database/flyway/sql`** при живом Postgres и только **baseline** в **`flyway_schema_history`**).

**Куда смотреть:** пошагово — **[order-database-vps.md](./order-database-vps.md)** (раздел **«Рассинхрон: пустой flyway/sql на VPS»**). Полный пересоздающий том сценарий — только **`scripts/install-order-database-vps.sh`**, если осознанно готовы к новому volume.

---

## 502 / «сервер недоступен» после `docker compose up --force-recreate backend`

**Причина:** контейнер **`gateway`** (nginx) продолжает проксировать на **старый IP** `backend` в Docker-сети.

**Исправление:**

```bash
cd /opt/acome-offer-desk
docker compose up -d --force-recreate --no-deps gateway
```

Скрипт **`scripts/install-order-database-vps.sh`** после обновления **`DATABASE_URL`** пересоздаёт **`backend`**, **`notifications_worker`** и **`gateway`**.

**На будущее:** в `nginx.conf` шлюза — **`resolver 127.0.0.11`** и **`proxy_pass` через переменную**, чтобы имя **`backend`** резолвилось заново.

---

## Чат (WebSocket): с домена не работает, с IP:8080 — работает

Внутренний nginx в **`gateway`** уже пробрасывает **`Upgrade`** для **`/api/`**. Если **`wss://домен/api/v1/ws/chat`** не подключается (часто **404** на handshake), а **`ws://IP:8080/...?token=…`** даёт **`connection.ready`** — чинить **хостовый** nginx/TLS **перед** Docker.

**Проверенный патч на хосте (Debian/Ubuntu):**

1. Файл **`/etc/nginx/conf.d/ws-upgrade-map.conf`:**

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
```

2. В **`server { … }`** для домена, в **`location /api/`** (рядом с **`proxy_pass`**):

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_read_timeout 86400;
```

Затем **`nginx -t && systemctl reload nginx`**.

---

## Почта не уходит

**Не задавать** **`SMTP_HOST=127.0.0.1`** в корневом **`.env`** для контейнеров — это не хост VPS. Для Яндекса: **`smtp.yandex.com`**, порт **465**, затем **`docker compose up -d --force-recreate backend notifications_worker`** (при необходимости и **`gateway`**).

Если в логах **`notifications_worker`** — **`SMTPAuthenticationError: 535`** — проверьте **`EMAIL_ADDRESS`**: реальный ящик (например **`@yandex.ru`**), не **`noreply@localhost`**, и **`EMAIL_APP_PASSWORD`** — пароль приложения для этого ящика.

Если в логах **`backend`** сообщение про отключённый IMAP — задать **`IMAP_HOST`**, **`IMAP_PORT`** по шаблону в **`.env.example`**.

---

## Ответ по почте (IMAP): `Reply token decoded`, затем `AttachmentFileInput` / `content_sha256`

**Симптом (до исправления):** в логах после **`Created new offer from email`** — **`AttributeError: 'AttachmentFileInput' object has no attribute 'content_sha256'`** при **`attachments=1`**.

**Причина:** вложения из письма передавались в **`FileService._store`** как **`AttachmentFileInput`**, тогда как слой хранения ожидает **`PreparedUpload`** (с полем **`content_sha256`** и проверками типа/размера через **`prepare_bytes`**).

**Исправление в коде:** в **`process_request_reply_use_case`** перед **`create_offer_file`** / **`create_chat_message_file`** вызывается **`file_service.prepare_bytes(...)`**, как в **`offers.py`** для загрузок из API.

После выката: **`docker compose build --no-cache backend`** и **`docker compose up -d --force-recreate --no-deps backend gateway`**.

---

## Superadmin после пересоздания БД

Пароль задаётся при инициализации **`order_database`**. На VPS (root): **`/root/.acom_order_db_superadmin_password`**. Пароли из старых заметок после нового тома могут не совпадать.

---

## `.env`

- Не дублировать **`WEB_BASE_URL`** / **`PUBLIC_BACKEND_BASE_URL`**.
- **`DATABASE_URL`:** хост Postgres = имя сервиса в вашей Docker-сети (часто **`order-database-postgres`**).
- Публичные URL — **ваш** домен/туннель.
