# IAM PostgreSQL: backup и restore

IAM использует отдельную PostgreSQL DB. Скрипты опираются на штатные
`pg_dump`, `pg_restore` и `psql`; параметры подключения передаются через
стандартные PostgreSQL env (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` и
`PGPASSWORD` либо `PGPASSFILE`). Пароль не попадает в argv процесса.

## Backup

```bash
export PGHOST='DB_HOST'
export PGPORT='5432'
export PGDATABASE='acom_iam'
export PGUSER='IAM_USER'
export PGPASSWORD='IAM_PASSWORD'
export IAM_BACKUP_DIR='/secure/backups/iam'
bash ./scripts/backup-iam-db.sh
```

Скрипт создаёт custom-format файл `iam-YYYYmmddTHHMMSSZ.dump`, устанавливает
закрывающий `umask` и завершается non-zero при любой ошибке. DSN и содержимое
БД не печатаются.

## Restore в новую пустую DB

Restore не предназначен для перезаписи рабочей IAM DB. Создайте новую пустую
БД и отдельного владельца, затем измените стандартные PostgreSQL env:

```bash
export PGHOST='DB_HOST'
export PGPORT='5432'
export PGDATABASE='acom_iam_restore'
export IAM_RESTORE_CONFIRM_DATABASE='acom_iam_restore'
export PGUSER='NEW_IAM_USER'
export PGPASSWORD='NEW_PASSWORD'
bash ./scripts/restore-iam-db.sh /secure/backups/iam/iam-20260817T080000Z.dump
```

Скрипт требует точного совпадения `IAM_RESTORE_CONFIRM_DATABASE` и
`PGDATABASE`, а также прекращает работу, если в `public` target DB уже есть
пользовательские таблицы. Он не удаляет существующие объекты. Для custom-format
backup используется `pg_restore --exit-on-error --single-transaction`; для
переданного `.sql` — `psql` с `ON_ERROR_STOP=1` и `--single-transaction`.

## Проверенный операционный сценарий

1. Остановить запись в исходную IAM DB на согласованное окно либо выполнять
   backup в режиме, допускающем согласованный snapshot PostgreSQL.
2. Снять backup существующей IAM DB и сохранить файл вне репозитория.
3. Создать новую пустую IAM DB с нужными owner/permissions.
4. Восстановить backup командой выше.
5. Направить временный `.env.iam-db` на новую DB и выполнить:

   ```bash
   docker compose run --rm iam_migrations validate
   docker compose run --rm iam_migrations migrate
   ```

   `migrate` нужен только если образ приложения содержит более новые
   аддитивные миграции, чем backup.
6. Направить временный `.env.iam` на восстановленную DB и запустить IAM.
7. Проверить `GET /health/live` и `GET /health/ready`; readiness должен вернуть
   `200`.
8. Через штатный gateway проверить login, затем refresh. Не выводить cookie,
   access token или refresh token в консоль и логи.
9. Только после проверки согласованно переключить runtime на восстановленную
   DB. Исходную DB не удалять до завершения rollback window.

Ключи подписи не хранятся в IAM DB. Для восстановленного сервиса необходимо
предоставить тот же актуальный local key ring отдельно через runtime env.
