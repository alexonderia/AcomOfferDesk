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

Все пути создания пользователя синхронизируют identity через общий
`ensure_user_iam_account`: создание сотрудника, контрагента из справочника,
нового контрагента при ручном КП и регистрация по приглашению. Успешное создание
включает IAM account и `user_auth_accounts(provider='iam')`; отсутствие почты
или начального пароля не отменяет синхронизацию. Для саморегистрации сохраняется
пара `review` / `pending`, для ручного создания — `active` / `active`.
Переиспользование компании также восстанавливает отсутствующую identity/связь.
Существующие пароль, IAM-статус, required actions и неактивная привязка сохраняются.
Конфликт логина, роли или владельца subject отклоняется.

При ошибке IAM операция не возвращает успешное создание, локальная транзакция
откатывается. IAM и MAIN не имеют общей транзакции: если сбой произошёл после
создания IAM account, повтор использует тот же стабильный subject без сброса
credentials. Точечная синхронизация исторических записей описана в
[эксплуатационном контракте](../operations/no-mail-accounts.md#синхронизация-исторического-пользователя).

При включённой почте `POST /users/register` и `POST /users/manual-contractor` создают MAIN `active`, IAM `active` без пароля и unverified email. Password setup автоматически не отправляется. Первый доступ идёт через generic recovery (логин или email): при `password_hash=NULL` — IAM `first_access` (RabbitMQ), затем `password_setup` (direct SMTP). После первой установки пароля IAM записывает `accounts.required_actions=["complete_profile"]` без TTL и без action token. Первое сохранение профиля вызывает IAM complete и убирает `complete_profile`.

При `EMAIL_ENABLED=false` создание сотрудника требует начального пароля и подтверждения; email необязателен. IAM `direct-credentials` создаёт готовую active identity без `complete_profile`, записывая источник в аудит. Повторы не меняют действующие credentials. Ручной контрагент может получить доступ при создании либо остаться справочной карточкой без пароля. Саморегистрация `review` по-прежнему требует verified email для approval.

### Смена собственного пароля

`POST /users/me/password` требует текущий пароль и совпадающие новый/повтор длиной 12–128 символов. Account/session ID берутся из авторизации; проверка и Argon2-хеширование выполняются IAM. После успеха отзываются refresh-сессии и setup/reset-токены, инвалидируется IAM browser session и очищаются cookie клиента. Access JWT других клиентов действуют до `exp`. Операция не использует почту и доступна в обоих режимах. [Эксплуатационный контракт](../operations/no-mail-accounts.md).

### Session

`business_access` истинно только при MAIN `active` и отсутствии IAM required action `complete_profile`. `review` и `first_login` направляются на `/account` или `/profile/onboarding`.

## `users.id_role`

Поле сохраняется для бизнес-классификации, UI и domain rules. Оно не является источником functional permissions. `CurrentUser.permissions` создаётся только из проверенного IAM token.

## Подробные контракты IAM

The project-owned `iam` service is the only runtime identity provider and the source
of functional roles, permissions, and individual grants. Historical non-IAM provider
values may remain in unchanged Acom database constraints, but no runtime authentication,
authorization, provisioning, synchronization, configuration, or infrastructure path may
consume them.

## Scenario: IAM BFF Authentication

### 1. Scope / Trigger

- Trigger: changes to authentication routes, protected dependencies, user provisioning,
  role/status administration, cookies, gateway routing, or IAM migrations.
- Goal: authenticate through Authorization Code + PKCE while keeping raw tokens out of browser JavaScript; password operations use dedicated authenticated BFF APIs and private IAM adapters.

### 2. Signatures

- Browser-facing Acom BFF:
  - `GET /api/v1/auth/login?next=<local-path>`
  - `GET /api/v1/auth/callback?code=<code>&state=<state>`
  - `GET /api/v1/auth/session`
  - `GET /api/v1/auth/csrf`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `POST /iam/acom/logout` (Acom BFF handler for deleting the `/iam` UI cookie)
  - `GET|POST /api/v1/auth/password/{setup|reset}`
  - `POST /api/v1/auth/password-reset/request`
- Public IAM:
  - `GET /iam/authorize`
  - `POST /iam/login`
  - `GET /iam/.well-known/jwks.json`
- Internal-only IAM APIs use `X-Acom-Service-Token` and cover code exchange, refresh,
  logout/revoke, account provisioning, role/status changes, action tokens, RBAC seed/report,
  and read-only account-ID reconciliation.
- Identity lookup is exact: active
  `user_auth_accounts(provider='iam', external_subject_id=<JWT sub>)`.

### 3. Contracts

- IAM access tokens are asymmetric RS256 JWTs with `kid`, and claims `sub`, `sid`,
  `role`, `permissions`, `iat`, `exp`, `iss`, and `aud`.
- Acom validates the JWT locally from configured IAM public keys. Normal business
  requests make no IAM network call.
- `CurrentUser.permissions` and `CurrentUser.system_role` come from the IAM token.
  Unit scope, domain status, resource actions, and Acom user activation remain local.
- Access, refresh, and auth-flow cookies are `HttpOnly`; production cookies are
  `Secure`; refresh and flow cookies use narrow paths. The readable CSRF cookie is
  double-submitted through `X-CSRF-Token`, with exact Origin/Referer validation.
- Browser JavaScript receives session metadata only. It never receives access or
  refresh token values and does not persist auth data in `localStorage`.
- Refresh tokens and authorization codes are stored only as keyed hashes in IAM.
  Refresh rotates on every use; replay revokes the session. Authorization codes are
  one-time and require PKCE S256 with exact redirect URI matching.
- Password setup/reset pages and form posts use BFF URLs. The backend proxies the form to
  IAM over its private network, never persists or logs the password/action token, and
  drops upstream headers; the gateway disables access logging for these token-bearing URLs.
  Setup/reset action links are sent directly by SMTP so raw action
  tokens do not rest in RabbitMQ. Setup delivery happens before the local binding commit,
  so a sanitized SMTP failure rolls back that binding and an idempotent retry can issue a
  replacement action token for the same IAM account.
- Acom and IAM use separate databases. The IAM schema has exactly these nine tables:
  `accounts`, `account_credentials`, `roles`, `permissions`, `role_permissions`,
  `auth_sessions`, `authorization_codes`, `auth_action_tokens`, `auth_audit_log`.
- Required Acom runtime env includes `IAM_INTERNAL_BASE_URL`, `IAM_PUBLIC_BASE_URL`,
  `IAM_ISSUER`, `IAM_AUDIENCE`, `IAM_PUBLIC_KEYS`, `IAM_SERVICE_TOKEN`, and BFF signing
  secrets. IAM runtime and IAM Flyway DB credentials live in separate env files.
- There are no legacy auth feature flags or endpoints. There is no old-JWT,
  trusted-header, role-column, retained-provider, or fake-user fallback.

### 4. Validation & Error Matrix

- Missing/invalid/expired/tampered JWT, wrong issuer/audience/kid, or missing `sid` -> `401`.
- Unknown or inactive IAM binding -> `401`; a non-IAM binding is never accepted.
- Local user inactive/blacklisted or lacking local business access -> deny locally.
- Invalid `state`, unsafe `next`, wrong redirect URI, PKCE mismatch, or code replay -> deny.
- Missing/mismatched CSRF token or foreign Origin/Referer on cookie-authenticated mutation -> `403`.
- IAM unavailable during login/refresh -> controlled unavailable response; no fallback.
- IAM unavailable during account/role/status administration -> operation fails and the
  local transaction must not be reported as successful.
- Internal IAM route requested through the public gateway -> `404`.
- Repeated user provisioning with the same deterministic identity -> reuse the IAM
  account and active binding; do not create duplicates.
- Reconciliation compares all retained IAM bindings with IAM account IDs and reports
  orphan accounts, missing accounts, and inactive bindings without copying PII or
  repairing data implicitly.

### 5. Good / Base / Bad Cases

- Good: Acom creates PKCE state, IAM authenticates, callback exchanges the code through
  the internal API, Acom resolves the active IAM binding, and only then sets BFF cookies.
- Base: an authenticated business request is authorized entirely from the verified JWT
  plus local Acom scope/status data.
- Bad: expose a bearer token to React, call a public IAM token/refresh/logout/password API
  from browser JavaScript, call IAM for every business request, auto-link by email, or
  fall back to a retained provider adapter.

### 6. Tests Required

- IAM unit/integration: Argon2id, generic login failures, brute-force lock, RS256 claims,
  PKCE S256, redirect allowlist, code one-time use, refresh rotation/replay revoke,
  setup/reset one-time use, audit, and exactly-nine-table schema.
- Acom unit/integration: state/CSRF validation, strict JWT validation, IAM-only binding,
  local status/scope enforcement, fail-closed IAM client errors, idempotent provisioning,
  role/status synchronization, session revocation, account reconciliation, and no legacy
  identity-provider imports.
- Frontend: cookie-session bootstrap/refresh/logout, no token storage, and protected-route behavior.
- Infra: compose renders with separate IAM env files; gateway exposes only the explicit
  public IAM allowlist and returns `404` for internal paths.

### 7. Wrong vs Correct

#### Wrong

```python
# Accepting another provider or the local role column recreates a second auth source.
binding = await accounts.get_any_provider_by_subject(claims.sub)
permissions = permissions_for_role(user.id_role)
```

#### Correct

```python
binding = await accounts.get_active_by_provider_subject("iam", claims.sub)
permissions = frozenset(claims.permissions)
```

Immutable deployed SQL migrations and archived migration bundles may describe historical
provider values. They must not be imported, copied into active configuration, or treated as
runtime adapters. Historical Acom binding rows are preserved as data only.

## Scenario: Browser IAM error recovery

### 1. Scope / Trigger

- Trigger: an IAM login URL is opened without its short-lived authorization cookie,
  or a browser reopens an expired/used Acom callback URL.

### 2. Signatures

- IAM browser routes: `GET|POST /iam/login`; browser credentials are submitted only as the
  authorization UI requires.
- Acom browser callback: `GET /api/v1/auth/callback?code=<code>&state=<state>`.
- SPA recovery screen: `GET /login?reset=1`.

### 3. Contracts

- Browser-facing auth failures render IAM HTML or redirect to
  `<IAM_PUBLIC_BASE_URL>/login?error=<known-code>`; they never use the JSON error
  contract intended for API clients.
- IAM browser-flow changes and Acom BFF flow-cookie/recovery changes form one deployable
  compatibility unit. Rebuild and recreate `iam`, `backend`, and `web` together; a new IAM
  image beside a stale backend image can repeatedly reject otherwise valid replacement flows.
- `GET /iam/login` without an auth-request cookie returns `303` to
  `/api/v1/auth/login`, which is the only route that creates the PKCE/state flow.
- The ordinary SPA `/login` route immediately begins that BFF flow; it is not a
  user-facing intermediate login choice. The actual IAM password form contains the
  `Забыли пароль?` link to `/login?reset=1`. Only that explicit URL renders the
  Acom password-reset form, because the reset request needs Acom's verified email
  and IAM binding. Password setup/reset pages are served through
  `/api/v1/auth/password/{setup|reset}` and proxy to IAM over the private network.
- A successful password login issues the IAM-only `HttpOnly`, `Secure` (outside local
  development), `SameSite=Lax`, path-scoped `/iam` browser-session cookie. It is a
  signed account ID plus password-version marker, never an access or refresh token.
  `/iam/authorize` validates the account remains active and its password version is
  unchanged before issuing a new authorization code without showing the password form.
- On the first expired/mismatched BFF callback, Acom sets a 60-second, `HttpOnly`
  recovery marker and redirects to `/api/v1/auth/login`. A valid IAM browser session
  then completes the replacement PKCE flow silently. The second failure consumes the
  marker and shows the ordinary recovery page, preventing an infinite redirect loop.
- `POST /api/v1/auth/logout` is CSRF-protected, revokes the IAM refresh session, and
  clears Acom access, refresh, CSRF, and flow cookies. The subsequent
  `POST /iam/acom/logout` is an Acom BFF handler (not an IAM endpoint) and clears the
  path-scoped `/iam` browser-session cookie from a path that browsers accept. The
  frontend never calls `POST /iam/logout`.
- Error codes are allowlisted by IAM and map to Russian user-facing text. Raw callback
  data, tokens, and exception details must never be reflected.

### 4. Validation & Error Matrix

- Direct `/iam/login` -> `303 /api/v1/auth/login`.
- `/login` without `reset=1` -> start BFF/IAM login immediately; `/login?reset=1`
  -> show the password-reset form.
- First expired or mismatched callback state -> clear the flow cookie, set the single
  recovery marker, and `303 /api/v1/auth/login`; an active IAM browser session is
  authorized without a second password entry.
- Repeated expired/mismatched callback while the recovery marker is present -> clear
  it and `303 .../iam/login?error=session_expired`.
- Runtime image hashes or versions differ across IAM/BFF after an auth-flow deployment ->
  recreate the stale service before diagnosing account credentials or deleting cookies.
- Invalid, expired, disabled-account, or password-version-mismatched IAM browser
  session -> clear that cookie and render the regular password form.
- Explicit logout -> the two BFF logout handlers clear all cookies even if IAM is
  unavailable. The next
  `/api/v1/auth/login` must render the
  password form rather than silently authorize.
- IAM unavailable during callback -> clear the flow cookie and `303` to
  `.../iam/login?error=service_unavailable`.
- Internal IAM/API route failure -> keep its JSON contract.

### 5. Good / Base / Bad Cases

- Good: a browser loses the BFF flow immediately after valid IAM password entry; it
  automatically starts one replacement PKCE flow and receives an active BFF session
  through the valid IAM browser session.
- Base: an invalid password stays on the current IAM form with a sanitized HTML error.
- Base: a user selects `Забыли пароль?` on the IAM form and sees the Acom reset form
  only after the explicit navigation.
- Bad: render `{"detail": ...}` in the browser, store a raw access/refresh token in the
  IAM browser cookie, retry an expired callback indefinitely, accept/reuse an old
  callback, or echo an arbitrary `error` query value.

### 6. Tests Required

- IAM test: direct login redirects to the BFF start; successful password login issues
  the browser-session cookie; a subsequent authorize response contains a new code and
  the supplied state without rendering the form.
- IAM/frontend tests: the IAM form contains `/login?reset=1`; normal `/login` calls
  `beginLogin`, while the reset query renders and submits the reset form.
- Logout smoke: establish BFF and IAM sessions, call the BFF logout endpoint, assert
  `/api/v1/auth/session` returns `401` and the following `/iam/authorize` returns
  the password form rather than an authorization-code redirect.
- Acom integration test: the first expired callback responds with `303 /api/v1/auth/login`
  and the recovery cookie; the second responds with the safe recovery page.
- Local smoke: complete password login, deliberately start an expired callback using
  only the IAM browser session, then assert the replacement flow establishes
  `/api/v1/auth/session` without a second credential POST.
- Deployment smoke: after recreating all auth participants, start with an empty cookie jar,
  assert `/api/v1/auth/login` renders the IAM password form, complete login, assert
  `/api/v1/auth/session` is `200`, then call BFF logout.

### 7. Wrong vs Correct

#### Wrong

```python
raise Unauthorized("Invalid IAM state")  # browser receives JSON from the global API handler
```

Deploy only the IAM image while leaving a backend image with an older flow-cookie protocol.

#### Correct

```python
return _retry_expired_iam_flow(request)  # one automatic replacement flow, then safe recovery
```

Deploy/recreate IAM and the Acom BFF together, then verify one complete browser flow.

## Scenario: Unified browser and API IAM unavailability

### 1. Scope / Trigger

- Trigger: an IAM route, the BFF authentication flow, or a public password-reset
  request is unavailable, rejected, or produces an expected business error.
- The browser must never expose a raw upstream gateway page or JSON document to a
  person. The presentation is selected by the type of request, not by the upstream
  implementation that failed.

### 2. Signatures

- Browser navigation: `GET /iam/authorize`, `GET|POST /iam/login`,
  `GET|POST /api/v1/auth/password/{setup|reset}`, `GET /api/v1/auth/login`, and
  `GET /api/v1/auth/callback`.
- API/XHR: `GET|POST /api/v1/auth/*`, including
  `POST /api/v1/auth/password-reset/request` with `{ "login": string }`.
- Frontend public reset request: `requestPasswordReset(login: string)`.

### 3. Contracts

- Nginx intercepts upstream `502`, `503`, and `504` for browser-navigation auth
  routes and serves the static `maintenance` HTML page. It must not forward an Nginx
  default error page.
- API/XHR authentication routes retain the controlled JSON unavailable contract so
  the React client can normalize it. They must not receive HTML from the gateway.
- React renders `TechnicalUnavailablePage` for an unavailable authentication service;
  a completed or ordinary failed user action is shown through `useSystemToasts`.
  Credential validation stays adjacent to the field only when it helps correct input.
- Password reset is public. Its request uses `credentials: 'omit'` even when an IAM
  session cookie exists, because cookie-authenticated unsafe requests require the
  CSRF header. The request has no `withAuth` token/cookie semantics.

### 4. Validation & Error Matrix

- Browser IAM/BFF route upstream `502|503|504` -> maintenance HTML page.
- API auth route upstream `502|503|504` -> controlled JSON unavailable response ->
  frontend technical page or error toast according to the active screen.
- Password-reset request with a stale auth cookie but no CSRF header -> prevented by
  `credentials: 'omit'`; the public request can reach the endpoint.
- Password-reset accepted -> success toast; do not disclose whether a login exists.
- Password-reset rejected for an ordinary safe reason -> error toast with sanitized
  message.

### 5. Good / Base / Bad Cases

- Good: IAM is stopped, `/iam/authorize` shows the project technical page; restarting
  IAM and retrying starts login normally.
- Base: an authenticated browser asks to reset a password and the POST is accepted
  without sending its session cookies.
- Bad: show a raw `502 Bad Gateway`, render `{"detail": ...}` as a document, attach
  cookies to the public reset request, or duplicate a component-local alert instead
  of using the shared toast system.

### 6. Tests Required

- Gateway smoke: make IAM unavailable and assert the browser auth route contains the
  maintenance-page marker and does not contain `502 Bad Gateway`.
- Frontend unit: password-reset POST has `credentials: 'omit'`, `withAuth: false`,
  and the login body only.
- Frontend component: reset success calls the shared success toast; unavailable auth
  renders `TechnicalUnavailablePage`.
- Backend integration: a public reset request returns its generic accepted response
  without session cookies; full BFF login still establishes an active session.

### 7. Wrong vs Correct

#### Wrong

```typescript
await fetchJson('/api/v1/auth/password-reset/request', {
  method: 'POST',
  body: JSON.stringify({ login }),
  withAuth: false,
}); // apiFetch still includes existing cookies, so CSRF can reject this request
```

#### Correct

```typescript
await fetchJson('/api/v1/auth/password-reset/request', {
  method: 'POST',
  body: JSON.stringify({ login }),
  withAuth: false,
  credentials: 'omit',
});
```

## Scenario: Seamless BFF access-session refresh

### 1. Scope / Trigger

- Trigger: a protected REST request returns `401`, the access cookie is expired on
  browser bootstrap, or the realtime transport reports authentication failure while
  the narrow-path HttpOnly refresh cookie may still be valid.
- Refresh-token rotation is replay-sensitive: concurrent use of the previous token
  revokes the IAM session. The browser runtime therefore coordinates refresh before
  it reaches the BFF/IAM boundary.

### 2. Signatures

- BFF endpoints: `GET /api/v1/auth/session`, `GET /api/v1/auth/csrf`,
  `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`.
- Frontend runtime: `AuthProvider.refresh('bootstrap' | 'http_401' | 'ws_4401')`
  resolves to `{ kind: 'success' | 'terminal' | 'unavailable' }`.
- BFF error contract: terminal refresh failure is HTTP `401`; IAM/network failure is
  HTTP `503` with `reason_code='AUTH_SERVICE_UNAVAILABLE'`.

### 3. Contracts

- `AuthProvider` owns one in-flight refresh promise. REST, bootstrap, and realtime
  consumers await that promise instead of creating independent refresh requests.
- The coordinator first obtains/rotates the readable CSRF cookie, then calls
  `POST /auth/refresh` through the shared authenticated API client so the request
  includes `X-CSRF-Token`; do not disable CSRF or mark this cookie-authenticated POST
  as unauthenticated merely to avoid the header.
- Success returns the new session DTO and BFF rotates the HttpOnly access and refresh
  cookies. The provider maps the new DTO, including current role and permissions,
  before permitting UI access. A REST request retries exactly once.
- `401` means terminal: BFF clears auth cookies, frontend reaches `unauthenticated`,
  and idempotent cleanup redirects to login at most once. A refresh endpoint response
  never triggers another refresh.
- `502|503|504`, a typed unavailable response, or network failure means
  `unavailable`: retain the possible refresh cookie, do not log out or redirect, and
  render the controlled technical-unavailable state while protected actions stay
  blocked.

### 4. Validation & Error Matrix

- Protected `401` + valid refresh -> one refresh -> `200` + rotated cookies -> one
  retry of the original request.
- Three concurrent REST `401`s or REST `401` plus WS auth failure -> one IAM refresh
  operation; every REST caller retries once after success and WS reconnects normally.
- Missing, expired, revoked, malformed, or identity-rejected refresh -> `401`, clear
  BFF auth cookies, no retry of the original protected request.
- IAM timeout/network/`502|503|504` -> unavailable result, no `Set-Cookie` deletion
  for the refresh cookie and no `/login` navigation.
- Reload with expired access and valid refresh -> session bootstrap refreshes and keeps
  the original route; it must not show an intermediate login redirect.

### 5. Good / Base / Bad Cases

- Good: an expired access cookie during a page action produces one invisible refresh,
  current permissions are refreshed from the DTO, and the original action completes.
- Base: an unavailable IAM service shows the technical-unavailable UI at the current
  URL; refreshing the page later can restore the cookie-backed session.
- Bad: allow every `401` handler or WebSocket provider to post `/auth/refresh`, inspect
  translated error text to decide logout, or clear cookies after a `503`.

### 6. Tests Required

- Frontend API tests: ordinary `401 → success → retry`, three parallel callers sharing
  one operation, bounded retry, and self-exclusion for `/auth/refresh`.
- Provider/realtime tests: one promise serves REST and `ws_4401`; terminal failures
  clear session once; unavailable preserves session metadata and does not call logout.
- Frontend auth-helper test: refresh POST carries the CSRF header and classifies
  `401`, `503`, and network failure without user-facing text matching.
- BFF integration: success returns the session DTO plus rotated HttpOnly cookies;
  terminal refresh clears them; unavailable returns typed `503` and preserves them.

### 7. Wrong vs Correct

#### Wrong

```typescript
const restored = await refreshWebSession();
if (!restored) logout();
```

This loses the terminal/unavailable distinction and turns an IAM outage into session
destruction. Calling the refresh helper with `withAuth: false` is also wrong because
the CSRF header is omitted for a cookie-authenticated POST.

#### Correct

```typescript
const result = await refresh('http_401');
if (result.kind === 'success') return retryOnce();
if (result.kind === 'terminal') forceLogoutOnce();
return originalUnauthorizedResponse;
```

All callers use the same provider-owned operation, and only the terminal branch
performs cleanup.

## Парольные операции и отключённая почта

Этот раздел дополняет BFF-контракт актуальным режимом `EMAIL_ENABLED=false`.
Сотрудник создаётся с начальным паролем и подтверждением через `POST /api/v1/users/register`; ручной контрагент — через `POST /api/v1/users/manual-contractor`.
Backend передаёт credentials в IAM через private API `direct-credentials`, не хранит и не логирует пароль. IAM остаётся владельцем Argon2-хеша.
Самостоятельная смена пароля — `POST /api/v1/users/me/password`; сброс суперадминистратором и ограничения целевых аккаунтов описаны в [эксплуатационном контракте](../operations/no-mail-accounts.md).
Проверяйте текущий пароль, совпадение нового и подтверждения, отзыв refresh/browser sessions и отсутствие почтовых обращений в отключённом режиме.
Локальная миграция тестовых аккаунтов — [отдельная процедура](../iam/local-account-migration.md), не production fallback.
