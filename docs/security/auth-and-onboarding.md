# Аутентификация и авторизация

## Source of truth

| Область | Источник |
|---|---|
| Authentication | IAM access token |
| Account identity | JWT `sub` → активный `user_auth_accounts(provider='iam')` → `users.id` |
| System role | IAM token claim `role` |
| Functional permissions | IAM effective permissions |
| Individual permissions | IAM `account_permission_grants` |
| Unit/data scope | Acom units и memberships |
| Business authorization | Acom domain policies |

Исторические записи `user_auth_accounts(provider='keycloak')` могут оставаться в БД, но не участвуют во входе, связывании identity или авторизации.

## Browser flow

1. Frontend открывает `/api/v1/auth/login`.
2. BFF создаёт PKCE/state flow и перенаправляет browser в IAM.
3. IAM возвращает одноразовый code на `/api/v1/auth/callback`.
4. Backend обменивает code, локально валидирует access token и проверяет IAM binding.
5. Access/refresh tokens записываются в HttpOnly cookies; frontend получает только session DTO.

## Проверка access token

Backend принимает только RS256 token с ожидаемыми `kid`, issuer и audience. Обязательны `sub`, `sid`, `role`, `permissions`, `iat` и `exp`. Неизвестные role/permission, неверная подпись, issuer/audience/kid и истёкший token отклоняются fail-closed.

## Refresh, logout и CSRF

- refresh token отправляется только cookie на auth path;
- state и PKCE защищают callback;
- изменяющие запросы требуют корректную пару CSRF header/cookie;
- revoked/expired refresh token завершает сессию;
- при недоступности IAM выдача нового auth context запрещена.

## Individual grants

Department и contractor delegation UI управляют IAM grants через internal IAM API. Effective permissions вычисляются как union role permissions и `account_permission_grants`; отдельная копия grants в Acom не хранится.

## `users.id_role`

Поле сохраняется для бизнес-классификации, UI и domain rules. Оно не является источником functional permissions. `CurrentUser.permissions` создаётся только из проверенного IAM token.
