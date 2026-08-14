# IAM — эксплуатация этапа 2

## Границы ответственности

- IAM владеет учётными записями, Argon2id-хешами, ролями, разрешениями,
  authorization code, action-token и auth-сессиями.
- AcomOfferDesk хранит профиль, подразделения и предметные связи. Связь с IAM
  выполняется только через активную запись `user_auth_accounts` с
  `provider='iam'` и `external_subject_id = JWT sub`.
- Backend AcomOfferDesk получает только публичный RSA-ключ IAM. Приватный ключ
  находится только в `.env.iam`, который подключается к контейнеру `iam`.
- Flyway получает только `.env.iam-db`; ключи подписи в миграционный контейнер
  не передаются.

## Подготовка конфигурации

1. Создать отдельную базу PostgreSQL и отдельного владельца IAM.
2. Скопировать `.env.iam.example` в `.env.iam` и заполнить runtime-настройки.
3. Скопировать `.env.iam-db.example` в `.env.iam-db` и заполнить настройки
   Flyway.
4. Добавить публичный ключ и тот же internal service token в runtime env
   AcomOfferDesk. Приватный ключ туда не копировать.
5. Для production использовать HTTPS. В production cookie автоматически
   получают флаг `Secure`, даже если его забыли указать явно.

RSA-ключи генерируются вне репозитория. Реальные env-файлы и ключи не должны
попадать в git, логи или артефакты сборки.

## Порядок развёртывания

```bash
docker compose config
docker compose run --rm iam_migrations
docker compose up -d --build iam
docker compose exec backend python -m app.scripts.seed_iam_rbac
docker compose exec backend python -m app.scripts.seed_iam_rbac --report
docker compose exec backend python -m app.scripts.reconcile_iam_accounts
docker compose exec backend python -m app.scripts.migrate_users_to_iam --dry-run
docker compose exec backend python -m app.scripts.migrate_users_to_iam --apply
docker compose up -d --build backend web gateway
```

Перед `--apply` необходимо проверить адреса доставки. Команда не печатает
пароли, action-token или адреса электронной почты. Повторный запуск безопасен:
существующие IAM-привязки пропускаются, account id детерминирован и непрозрачен,
а выпуск нового action-token инвалидирует предыдущий неиспользованный токен
того же назначения.

Пользователи без валидного email помечаются как
`blocked-missing-valid-email` и не изменяются. Сначала необходимо исправить
контакт в AcomOfferDesk, затем повторить dry-run и apply; секретная ссылка не
выводится для ручной передачи через stdout.

`reconcile_iam_accounts` выполняет только чтение и показывает IAM accounts без
Acom-привязки и Acom IAM-привязки без соответствующего account. Для CI/ручного
quality gate можно добавить `--strict`: при найденном drift команда завершится
с кодом `2`, но ничего автоматически не удалит и не исправит.

## Проверка после запуска

- `GET /health` backend и внутренний `GET /health` IAM возвращают `200`.
- `/iam/authorize`, `/iam/login`, `/iam/password/setup`,
  `/iam/password/reset` и `/iam/.well-known/jwks.json` доступны через gateway.
- `/iam/internal/*`, `/internal/*` и остальные IAM URL через gateway не
  доступны.
- Вход завершается callback AcomOfferDesk, после которого браузер получает
  только HttpOnly access/refresh cookie и читаемую double-submit CSRF cookie.
- Бизнес-endpoint не вызывает IAM: access JWT проверяется локально публичным
  ключом.

## Ошибки и откат

При недоступности IAM операции входа, refresh, logout и управления учётной
записью завершаются контролируемой ошибкой; локальная бизнес-транзакция не
подтверждается. Если IAM-операция уже прошла, повтор использует тот же account id
и приводит обе стороны к одному состоянию.

Миграции этапа 2 аддитивны. Для отката приложения остановить новые контейнеры и
вернуть предыдущие образы/config. Таблицы IAM, `iam`-привязки и legacy-данные не
удалять: destructive rollback в этом этапе не предусмотрен. Возврат старого
runtime-аутентификатора является отдельным осознанным решением, а не fallback
текущего кода.
