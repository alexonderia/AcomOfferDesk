# PostgreSQL (order_database) на VPS

## Граница ответственности документа

Этот документ покрывает только внешний `order_database` на VPS: Flyway, init, восстановление рассинхронов.

Смежные документы:
- [VPS troubleshooting](./vps-troubleshooting.md)
- [Окружения](./environments.md)
- [Чек-лист релиза](./release-checklist.md)

Источник схемы и init: репозиторий **[alexonderia/order_database](https://github.com/alexonderia/order_database)**, ветка **`main`**.  
Команды Flyway и профиль `tools`: **[order_database/docs/flyway.md](https://github.com/alexonderia/order_database/blob/main/docs/flyway.md)**.

## Зачем этот документ

После крупных изменений схемы БД её **пересоздают с нуля** (пустой volume), затем заводят учёт миграций Flyway. На сервере без интерактивного `git clone` в приватный репозиторий удобно использовать скрипт из этого репозитория.

## Требования

- Docker и **Compose v2** на хосте.
- Внешняя сеть **`project_net`** (как у основного `docker-compose.yml` приложения):  
  `docker network create project_net`
- Для **приватного** `order_database`: переменная **`GITHUB_TOKEN`** или **`GH_TOKEN`** (PAT с правом **`repo`**). Публичный URL `.../archive/refs/heads/main.tar.gz` без токена для приватного репо даёт **404**.

## Автоматический сценарий

Скрипт **[scripts/install-order-database-vps.sh](../scripts/install-order-database-vps.sh)**:

1. Скачивает `main` (GitHub API tarball при наличии токена).
2. Раскладывает дерево в **`/opt/order_database`** (переменная **`ORDER_DB_DIR`**).
3. Генерирует пароли Postgres и superadmin, пишет их в **`/root/.acom_order_db_postgres_password`** и **`/root/.acom_order_db_superadmin_password`** (права по `umask`).
4. Делает **`docker compose build`** / **`up`** для Postgres, **Flyway validate + migrate**.
5. Проверяет: **7** строк в **`roles`**, **`superadmin`** в **`users`**, наличие **`flyway_schema_history`**.
6. Если есть корневой **`/opt/acome-offer-desk/.env`** (`APP_DIR`), обновляет **`DATABASE_URL`** на хост **`order-database-postgres:5432`** и пересоздаёт **`backend`** и **`notifications_worker`**.

Пример с машины с `gh` CLI:

```bash
TOKEN=$(gh auth token)
scp scripts/install-order-database-vps.sh root@VPS:/root/
ssh root@VPS "export GITHUB_TOKEN='$TOKEN'; bash /root/install-order-database-vps.sh | tee /tmp/install-order-db.log"
```

В логе в конце должно быть **`INSTALL_SUCCESS`**.

После пересоздания **`backend`** вручную всегда пересоздавайте **`gateway`**, иначе возможен **502** на API (см. **[vps-troubleshooting.md](./vps-troubleshooting.md)**).

## Связь с GitHub Actions deploy

Workflow **`.github/workflows/deploy.yml`** в этом репозитории **не выполняет Flyway migrate автоматически** для `order_database`.

Он считает `order_database` отдельным prerequisite на VPS и перед app deploy проверяет:

- каталог **`/opt/order_database`** и его **`.env`**;
- healthy-статус контейнера **`order-database-postgres`**;
- наличие **`flyway_schema_history`**;
- что корневой **`.env`** уже смотрит на **`order-database-postgres:5432`**.

Если одна из этих проверок не проходит, workflow падает с меткой **`ORDER_DB_PREREQUISITE`** и просит сначала привести VPS к состоянию из этого документа, обычно через **`scripts/install-order-database-vps.sh`** до **`INSTALL_SUCCESS`**.

## Ожидания по данным (как в задаче)

| Проверка | Ожидание |
|----------|----------|
| `roles` | **7** ролей (см. `init` в order_database) |
| `users` | запись **`superadmin`** |
| Flyway | таблица **`flyway_schema_history`**; дальнейшие изменения схемы — через миграции в репозитории БД |

## Связка с приложением AcomOfferDesk

- В корневом **`.env`** сервис БД в Docker-сети обычно **`order-database-postgres:5432`** (имя контейнера из compose репозитория БД), а не обязательно `postgres`.
- Шаблоны переменных приложения: **`.env.example`**, **`.env.dev.example`**, **`.env.prod-like.example`**.

## Ручной путь (без скрипта)

Клонировать или скопировать каталог **`order_database`**, заполнить его **`.env`**, поднять Postgres, затем по **flyway.md** выполнить **`validate`** / **`migrate`** (или **`baseline`**, если так согласовано для пустой истории миграций).

## Рассинхрон: пустой `flyway/sql` на VPS (апрель 2026)

**Симптомы:** после входа через Keycloak бэкенд отвечает **500** на **`/api/v1/auth/callback`**; в логах **`backend`** — `relation "user_auth_accounts" does not exist`. При этом в **`flyway_schema_history`** может быть только строка **baseline** (**`1.0.0`**), а каталог **`/opt/order_database/flyway/sql`** на диске **пустой** или без актуальных **`V*.sql`**.

**Причина:** дерево **`order_database`** на сервере неполное (ручное копирование, обрезанный архив, старый снимок). Flyway видит только baseline из **`flyway.conf`** и считает схему «догнанной», хотя версионные миграции из репозитория не подставлялись.

**Исправление без пересоздания тома Postgres** (данные сохраняются):

1. Синхронизировать **`flyway/sql`** (и при необходимости **`flyway/conf/flyway.conf`**) с актуальным **`main`** репозитория **`alexonderia/order_database`**. Для приватного репо — **`GITHUB_TOKEN`** / **`GH_TOKEN`** и tarball через GitHub API, как в **`install-order-database-vps.sh`**.
2. В **`/opt/order_database`:**  
   `docker compose --profile tools run --rm flyway migrate`
3. Проверка: в БД есть таблица **`user_auth_accounts`**; в **`flyway_schema_history`** появляются версии после baseline (например **`1.0.1`**).

Пример одной сессии на VPS (подставить токен; **`rsync`** на сервере может отсутствовать — используйте **`cp -a`**):

```bash
cd /opt/order_database
# распаковать свежий tarball main во временный каталог, затем:
# rm -f flyway/sql/*.sql && cp -a <extracted>/flyway/sql/*.sql flyway/sql/
docker compose --profile tools run --rm flyway migrate
docker compose exec -T postgres psql -U order_admin -d order_database -c '\dt user_auth_accounts'
```

**Не использовать** полный **`install-order-database-vps.sh`**, если нужно **сохранить** существующий volume: скрипт по дизайну делает **`docker compose down -v`** и пересоздаёт данные.

**После успешной миграции:** повторный вход через Keycloak должен проходить без **500** на callback (подтверждено на production, апрель 2026).
