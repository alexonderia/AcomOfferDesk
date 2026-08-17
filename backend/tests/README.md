# Backend tests

- `unit/` проверяет domain/services/auth без live infrastructure.
- `integration/` проверяет FastAPI и cross-layer contracts через fakes/overrides.
- корневые `test_*.py` содержат migration/permission/response guards.

Запуск:

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Auth coverage включает IAM JWT validation, IAM-only binding, BFF callback/refresh/logout, cookies/CSRF, effective permissions и запрет provider-specific fields в `CurrentUser`/session DTO. Live PostgreSQL, IAM, RabbitMQ и MinIO для unit/integration suite не требуются.
