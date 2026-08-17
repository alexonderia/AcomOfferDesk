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

## Ручная overlap-ротация signing key

IAM подписывает новые access JWT только парой
`IAM_SIGNING_PRIVATE_KEY` / `IAM_SIGNING_PUBLIC_KEY` с активным
`IAM_SIGNING_KID`. `IAM_SIGNING_VERIFICATION_KEYS` — JSON-объект
`kid -> public PEM` для RETIRING-ключей. Backend использует локальный key ring
из активной пары `IAM_SIGNING_PUBLIC_KEY` / `IAM_SIGNING_KID` и того же JSON;
запрос к IAM при проверке business request не выполняется.

1. Сгенерировать новую RSA-пару вне репозитория. Старый private key для
   verification не нужен.
2. Сначала добавить новый public key в
   `IAM_SIGNING_VERIFICATION_KEYS` backend и развернуть backend. Старый ключ
   пока остаётся активным.
3. В IAM заменить активные private/public/kid на новую пару, а старый public
   key добавить в `IAM_SIGNING_VERIFICATION_KEYS`. Перезапустить IAM.
4. Проверить, что JWKS содержит old + new, новые JWT имеют new `kid`, а backend
   принимает токены с обоими `kid`.
5. В backend сделать новую пару основной в
   `IAM_SIGNING_PUBLIC_KEY` / `IAM_SIGNING_KID`, оставив old public key в JSON.
6. Выждать не меньше максимального `IAM_ACCESS_TOKEN_TTL_SECONDS` плюс время
   распространения deploy/config. Текущая конфигурация ограничивает TTL
   диапазоном 60–900 секунд.
7. Удалить old public key из JSON IAM и backend, перезапустить сервисы и
   проверить, что старый `kid` отклоняется.

Не переключать IAM на новый active key до того, как backend получил его public
key. Не удалять RETIRING public key до истечения всех выпущенных им access JWT.

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

- `GET /health/live` IAM проверяет только процесс и не обращается к DB.
- `GET /health/ready` IAM проверяет `SELECT 1` в IAM DB и активную signing
  configuration. Docker healthcheck использует readiness.
- `GET /health` IAM сохранён как совместимый alias readiness; `GET /health`
  backend возвращает `200`.
- `/iam/authorize`, `/iam/login`, `/iam/password/setup`,
  `/iam/password/reset` и `/iam/.well-known/jwks.json` доступны через gateway.
- `/iam/internal/*`, `/internal/*` и остальные IAM URL через gateway не
  доступны.
- Вход завершается callback AcomOfferDesk, после которого браузер получает
  только HttpOnly access/refresh cookie и читаемую double-submit CSRF cookie.
- Бизнес-endpoint не вызывает IAM: access JWT проверяется локально публичным
  ключом.

## Cleanup transient IAM data

Команда удаляет expired authorization codes/action tokens/sessions и
consumed/revoked записи старше retention. Удаление идёт пакетами, активно
действующие sessions не затрагиваются, `auth_audit_log` не удаляется. При
удалении audited session её исторические audit events сохраняются, а
`auth_audit_log.session_id` становится `NULL` через FK `ON DELETE SET NULL`.

```bash
docker compose exec iam \
  python -m iam_app.maintenance.cleanup --dry-run --retention-hours 24 --batch-size 500

docker compose exec iam \
  python -m iam_app.maintenance.cleanup --retention-hours 24 --batch-size 500
```

Результат — JSON с количеством записей по каждой таблице и общим `total`.
Команду можно вызывать из cron/systemd/container schedule; отдельный scheduler
в IAM не требуется.

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
