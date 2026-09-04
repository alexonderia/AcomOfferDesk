# Runtime architecture

```text
browser → gateway → web/backend
                    backend → IAM (code exchange, refresh, logout, internal admin API)
                    backend → PostgreSQL / RabbitMQ / MinIO / file_guard
                    RabbitMQ → notifications_worker
```

`gateway` — единственная публичная точка входа. `/` направляется в web, `/api/*` — в backend, публичные IAM browser endpoints и JWKS доступны под `/iam`; internal IAM endpoints извне закрыты.

## Auth boundary

Backend локально проверяет IAM access token и разрешает identity только через активный IAM binding. Permissions берутся из token; unit scope и domain policies вычисляются в Acom. Frontend работает с HttpOnly cookies и session DTO, не с JWT.

## Runtime services

- `iam_migrations`, `iam`;
- `backend`, `web`, `gateway`;
- `file_guard`, `notifications_worker`;
- `rabbitmq`, `minio`.

PostgreSQL подключается через внешнюю Docker network `project_net` и не объявляется сервисом основного compose stack.
