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

## Регистрация и онбординг

MAIN хранит только бизнес-факты. Технические auth/onboarding actions живут в IAM либо в stateless signed token.

Независимые оси:

- MAIN `users.status` (`review` / `active` / `inactive` / `blacklist`);
- IAM `accounts.auth_status` (`pending` / `active` / `blocked` / `disabled`);
- подтверждение email только в `user_contact_channels.is_verified`;
- наличие пароля в IAM `account_credentials.password_hash`;
- временные действия в IAM `auth_action_tokens` (`verify_email`, `first_access`, `profile_change`, `password_setup`, `password_reset`);
- постоянные required actions в IAM `accounts.required_actions` (`complete_profile`, без TTL).

Отдельного `users.onboarding_state` и таблиц invitations/verification actions в MAIN нет. Session DTO `onboarding_state=first_login` вычисляется, если в IAM required actions есть `complete_profile`.

### Саморегистрация по приглашению

1. Authorized Admin/Security (`users.registration.invite`) или роли с `contractors.manual.create` выпускают HMAC-подписанный stateless token. MAIN ничего про invitation не пишет.
2. Claims: `purpose=registration_invite`, email, role_id, unit_id, inviter_id, nonce, exp. Ссылка `/register?token=...`.
3. Дополнительная рассылка по заявке (`additional_emails`) выпускает тот же token без `users.registration.invite`: неизвестный email → `/register?token=...`; email уже привязан к пользователю (`user_login`) → портал входа (`INVITATION_PORTAL_URL` / `/login`).
4. До успешной регистрации тот же valid token технически можно открыть повторно. После создания пользователя повтор блокируется uniqueness (email/login/IAM binding).
5. Submit берёт role/unit из claims; email можно исправить на форме. MAIN `review`, IAM `pending`, unverified primary email. Повторный submit той же ссылки обновляет незавершённую заявку, а не создаёт второго пользователя. UI открывает `/verify-email?next=check_email&invite=...` со статусом «подтвердите почту» и кнопкой вернуться к форме.
6. Подтверждение email идёт через IAM `verify_email` и меняет только `user_contact_channels.is_verified`. После клика по письму страница показывает, что email подтверждён и заявка на проверке.
7. Approval (`users.registration.approve`) требует verified email и переводит MAIN+IAM в `active`.
8. Password setup/reset и email verification никогда не активируют MAIN или IAM.

### Ручное создание

`POST /users/register` и `POST /users/manual-contractor` создают MAIN `active`, IAM `active` без пароля и unverified email. Password setup автоматически не отправляется. Первый доступ идёт через generic recovery (логин или email): при `password_hash=NULL` — IAM `first_access` (RabbitMQ), затем `password_setup` (direct SMTP). После первой установки пароля IAM записывает `accounts.required_actions=["complete_profile"]` без TTL и без action token. Первое сохранение профиля вызывает IAM complete и убирает `complete_profile`.

### Session

`business_access` истинно только при MAIN `active` и отсутствии IAM required action `complete_profile`. `review` и `first_login` направляются на `/account` или `/profile/onboarding`.

## `users.id_role`

Поле сохраняется для бизнес-классификации, UI и domain rules. Оно не является источником functional permissions. `CurrentUser.permissions` создаётся только из проверенного IAM token.
