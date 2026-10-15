# Миграции базы IAM

IAM использует отдельную базу PostgreSQL. Схему применяет Flyway; приложение
не создаёт таблицы при запуске.

Миграции запускаются сервисом `iam_migrations`. После готовности IAM матрица
RBAC загружается явно из контракта разрешений AcomOfferDesk:

```bash
docker compose run --rm iam_migrations
docker compose up -d iam backend
docker compose exec backend python -m app.scripts.seed_iam_rbac
docker compose exec backend python -m app.scripts.seed_iam_rbac --report
```

Схема намеренно содержит ровно десять прикладных таблиц. Поле
`role_permissions.permission_id` имеет тип `BIGINT`, соответствующий
`permissions.id BIGSERIAL` из утверждённой схемы.

`account_permission_grants` хранит только дополнительные permissions account:
они объединяются с `role_permissions`, не содержат DENY и не заменяют
ролевую матрицу.
