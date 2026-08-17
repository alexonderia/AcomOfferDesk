# Матрица permissions

Канонический список permission codes находится в `backend/app/domain/permissions.py`. IAM RBAC seed строится из этого контракта и системных role names из `backend/app/domain/iam_roles.py`.

## Правила

- IAM хранит role permissions и `account_permission_grants`.
- Effective permissions равны union permissions роли и индивидуальных grants.
- Access token содержит только известные application permission codes; неизвестное значение отклоняет token целиком.
- `users.id_role` не создаёт permissions и не является fallback.
- `CurrentUser.role_id` приходит из проверенного IAM system role и может использоваться domain policies как тип участника процесса.
- Unit hierarchy и memberships ограничивают data scope независимо от functional permission.
- Frontend permissions/actions служат для UX; enforcement остаётся на backend.

## Individual access

Department и contractor delegation UI сохраняют изменения только в IAM grants. UI access codes могут оставаться стабильными identifiers, но runtime authorization проверяет соответствующие atomic permission codes. Удаление индивидуального grant не снимает permission, если он наследуется от system role.

## Изменение матрицы

При добавлении или удалении permission необходимо синхронно обновить:

1. `PermissionCodes` и role matrix в backend;
2. IAM seed/report tests;
3. backend policies/actions;
4. frontend guards и tests;
5. этот документ и coverage map.
