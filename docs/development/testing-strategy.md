# Стратегия тестирования

## Локальный обязательный контур

1. Backend unit/integration tests.
2. IAM tests.
3. Frontend lint, unit tests and build.
4. Global legacy-auth search.
5. `docker compose ... config` for supported overlays.

## Security focus

Проверяются local RS256 validation, issuer/audience/kid, expiry, required claims, IAM binding, blocked user/account, refresh rotation/revoke, logout, CSRF и недоступность IAM. Любая ошибка должна завершаться fail-closed.

## Authorization focus

Проверяются effective permissions из IAM, individual grants, role-inherited permissions после удаления grant, неизвестные permissions, Acom unit hierarchy, request/offer visibility и domain policies. `users.id_role` не должен создавать permissions.

## Live smoke

`scripts/smoke-infra.*` работает с поднятым stack. `scripts/check-iam.*` сверяет и при явном repair синхронизирует RBAC. E2E требует заранее подготовленные IAM credentials; автоматического identity-provider provisioning нет.
