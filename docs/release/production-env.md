# Production environment contract

Обязательные IAM параметры backend: `IAM_INTERNAL_BASE_URL`, `IAM_PUBLIC_BASE_URL`, `IAM_ISSUER`, `IAM_AUDIENCE`, `IAM_SIGNING_PUBLIC_KEY`, `IAM_SIGNING_KID`, `IAM_INTERNAL_SERVICE_TOKEN`. Private IAM signing key хранится только в IAM runtime env и не передаётся backend.

Также обязательны application DB, RabbitMQ, S3/MinIO, SMTP и cookie/security settings. Секреты не хранятся в репозитории.

Production требования:

- HTTPS public URLs и secure cookies;
- gateway — единственная публичная точка входа;
- internal IAM API недоступен извне;
- service/database/admin ports не публикуются;
- PostgreSQL подключён через external `project_net`;
- compose config, backend/IAM/frontend tests, IAM check и infrastructure smoke зелёные.
