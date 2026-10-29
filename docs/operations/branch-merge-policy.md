# Политика продвижения веток

Перед продвижением dev → test → production просматривайте diff, особенно:

- `docker-compose*.yml` и env examples;
- `iam/`, backend auth/config и gateway;
- deploy workflows и database migrations;
- permission matrix, policies, frontend guards;
- notification/file contracts.

Обязательные gates:

1. backend tests;
2. IAM tests;
3. frontend lint, unit tests and build;
4. compose config для target overlay;
5. IAM RBAC/account reconciliation report;
6. infrastructure smoke на поднятом стенде;
7. ручная проверка login/refresh/logout и ключевых role scopes.

Нельзя автоматически включать неизвестные dirty files, секреты или локальные env. Изменения auth должны сохранять fail-closed поведение, IAM-only binding и Acom unit scope.
