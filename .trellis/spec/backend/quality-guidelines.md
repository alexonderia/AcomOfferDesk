# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

Backend changes must preserve the current FastAPI + async SQLAlchemy + Clean Architecture / DDD-oriented structure. Code should be production-ready on the first pass: no temporary stubs, no fake behavior, no hardcoded secrets.

---

## Required Patterns

- Inspect affected files before proposing edits.
- Keep API routes thin: validate input, collect dependencies, call services, serialize output.
- Keep business rules in `backend/app/domain/*` or `backend/app/services/*`.
- Keep repositories limited to CRUD/query persistence work.
- Use `UnitOfWork` for transaction boundaries.
- When a service receives runtime URLs or adapters through its constructor, keep helper branches aligned with those injected values instead of re-reading equivalent global settings only. This preserves direct service tests and non-HTTP entrypoints.
- Use backend permissions/action flags as the source of truth for allowed actions.
- Keep Keycloak-backed E2E provisioning aligned with the realm user-profile schema. If Keycloak makes a profile attribute required (for example `middleName`), populate it during smoke-user creation so tests do not stall on required-action forms before the SPA loads.
- Review-stage contractor onboarding must use dedicated registration-only self-profile endpoints. Do not weaken the normal `/users/me*` permission gates for already-authenticated pages.
- Keep in-memory integration fixtures aligned with current dataclass constructors and service factory signatures; when request/offer schemas gain or lose fields, update the test factories in the same change.
- Preserve legacy Telegram functionality unless removal is explicitly requested.
- For DB changes, include SQL/migration patch and rollout notes.
- For infra changes, preserve `gateway`, `project_net`, and tunnel routing.

---

## Forbidden Patterns

- Business logic in API routes.
- Permission enforcement only on the frontend.
- Repository methods that decide business policy.
- Direct public exposure of backend, Keycloak, RabbitMQ, MinIO, PostgreSQL, or admin ports in `test`/`prod`.
- Hardcoded secrets, tokens, passwords, or production hostnames.
- Temporary placeholder implementations, mock-only production paths, or TODO-dependent behavior.
- Removing Telegram compatibility code or compose rollback comments without an explicit task.
- Changing DB schema because it is convenient rather than required by the task.

---

## Permissions Checklist

When a backend change affects permissions/actions:

- [ ] Permission codes are defined/updated centrally in `backend/app/domain/permissions.py`.
- [ ] Domain policies or service rules enforce the behavior.
- [ ] Internal staff visibility uses the shared scope services consistently:
  `StaffAccessScopeService` for module scope and `DepartmentScopeService` for subdivision/department scope.
- [ ] User/staff list endpoints do not fall back to ad hoc direct-subordinate-only filtering when module/department scope already exists elsewhere in requests/plans.
- [ ] Internal staff list scope remains aligned with the current contract:
  project manager -> department/subdivision scope;
  lead economist / economist -> module scope by default;
  department delegation permissions -> broaden to department/subdivision scope.
- [ ] `department.requests.status_update` is enforced independently for foreign department requests; `department.requests.update` must not implicitly grant status transitions.
- [ ] Department offer status actions remain independent: `department.requests.update` must not implicitly grant `department.offers.accept` or `department.offers.reject`.
- [ ] Department offer content actions remain independent: `department.requests.update` must not implicitly grant amount/file edits; use `department.offers.update`.
- [ ] Contractor-specific request view checks `requests.contractor_view.read` explicitly at backend service/policy level.
- [ ] Offer acceptance flow rejects `accepted` transition when parent request is already `closed` or `cancelled`.
- [ ] API responses expose backend-owned permissions/actions/links for frontend UX.
- [ ] Frontend does not become the final decision maker.
- [ ] Tests or targeted validation cover denied and allowed paths when feasible.

---

## Testing Requirements

Run the narrowest meaningful checks for the task and report them. Typical commands:

```powershell
python -m pytest
```

If checks cannot be run, state why and list the residual risk.

## Scenario: Review Contractor Registration-Only Self-Profile Access

### 1. Scope / Trigger
- Trigger: contractor onboarding uses `/api/v1/users/me`, `/api/v1/users/me/profile`, and `/api/v1/users/me/company-contacts` before the user has full system access.

### 2. Signatures
- Read registration onboarding state: `GET /api/v1/users/me/registration-profile`
- Update registration onboarding profile: `PATCH /api/v1/users/me/registration-profile`
- Update registration onboarding company contacts: `PATCH /api/v1/users/me/registration-company-contacts`
- Regular authenticated self-profile endpoints stay permission-gated:
  `GET /api/v1/users/me`
  `PATCH /api/v1/users/me/profile`
  `PATCH /api/v1/users/me/company-contacts`

### 3. Contracts
- Request fields:
  standard self-profile and self-company payloads from the SPA registration form.
- Response fields:
  same `MeResponse` contract as regular self-profile endpoints, including `actions`.

### 4. Validation & Error Matrix
- `role=contractor` and `status=review` -> allow access only through the dedicated registration endpoints even if atomic profile/company permissions are absent.
- same user on regular `/users/me*` endpoints -> keep standard permission enforcement.
- `status=inactive|blacklist` -> keep blocking protected actions.
- non-contractor `review` users -> do not inherit the contractor onboarding bypass.

### 5. Good/Base/Bad Cases
- Good: new review contractor opens the registration form, reads/saves through dedicated onboarding endpoints, and other pages stay on normal rights checks.
- Base: active users and ordinary profile pages still rely on normal permission-based self-profile behavior.
- Bad: weakening `/users/me*` globally so any post-login self-profile screen bypasses rights just because the user is in review.

### 6. Tests Required
- Integration: review contractor without `profile.manage_own` gets `403` on regular `GET /api/v1/users/me`.
- Integration: same user can `GET /api/v1/users/me/registration-profile`.
- Integration: same user can `PATCH /api/v1/users/me/registration-profile`.
- Integration: same user can `PATCH /api/v1/users/me/registration-company-contacts`.
- Contract: returned `actions` should reflect onboarding editability for that review contractor.

### 7. Wrong vs Correct
#### Wrong
- Reuse the regular `/users/me*` endpoints for registration onboarding and weaken their permission checks for all self-profile traffic.

#### Correct
- Keep registration onboarding on dedicated endpoints and leave the regular authenticated self-profile endpoints permission-gated.

## Scenario: Keycloak Name Sync For Linked Local Profiles

### 1. Scope / Trigger
- Trigger: any change that creates, updates, or synchronizes a Keycloak-linked user whose local profile stores one combined `full_name` while Keycloak stores separate profile fields.

### 2. Signatures
- Backend self-profile writes:
  `PATCH /api/v1/users/me/profile`
  `PATCH /api/v1/users/me/registration-profile`
- Backend admin/manual writes:
  user creation/update flows in `backend/app/services/users.py`
- Keycloak admin sync entrypoint:
  `KeycloakAdminService.ensure_user(...)`

### 3. Contracts
- Local source of truth:
  `profiles.full_name` stores one combined FIO string.
- Keycloak target fields:
  `lastName`
  `firstName`
  `attributes.middleName[]`
- Mapping contract from local `full_name` to Keycloak fields:
  - token order is `Фамилия Имя Отчество`
  - first token -> `lastName`
  - last token -> `middleName` when there are 3+ tokens
  - middle token span -> `firstName`, so first name may contain multiple words
  - hyphenated surname stays inside the first token
- Reverse mapping from Keycloak claims to local profile:
  combine `family_name`, `given_name`, and `middle_name` back into one `full_name`.

### 4. Validation & Error Matrix
- local profile updated and linked Keycloak account exists -> push latest FIO/email to Keycloak in the same service flow
- Keycloak callback returns edited profile claims -> overwrite local `profiles.full_name` / `profiles.mail` with those latest submitted values
- local `full_name` missing/placeholder -> do not invent synthetic Keycloak names
- local profile not linked to Keycloak yet -> update only the local profile; sync resumes after binding

### 5. Good/Base/Bad Cases
- Good: local DB already has `Иванов-Сидоров Анна Мария Петровна`; Keycloak gets `lastName=Иванов-Сидоров`, `firstName=Анна Мария`, `middleName=Петровна`, and the user does not re-enter FIO.
- Base: user enters FIO in Keycloak first; callback stores the submitted values into the local profile.
- Bad: only copying Keycloak names into blank local profiles while never pushing local onboarding/admin edits back to Keycloak; this leaves required-action forms empty on first login.

### 6. Tests Required
- Unit: tokenized full-name mapping preserves hyphenated surname and multi-word first name.
- Unit: linked self-profile update calls `ensure_user()` with parsed Keycloak name fields.
- Unit/Integration: Keycloak callback sync overwrites stale local `full_name` with the latest claims.
- Integration: admin/manual user flows that mock `ensure_user()` must accept the name-sync kwargs.

### 7. Wrong vs Correct
#### Wrong
- Treat local `full_name` as opaque text everywhere and sync only username/email into Keycloak.

#### Correct
- Keep one `full_name` in the local DB, but always map it explicitly into Keycloak `lastName` / `firstName` / `middleName` when a linked account is created or updated.

## Scenario: Self-Registered Contractor Keycloak Access On Activation

### 1. Scope / Trigger
- Trigger: a contractor creates a Keycloak-linked account through self-registration, stays in local `users.status=review`, and later an internal user approves the account by changing status to `active`.

### 2. Signatures
- Status transition entrypoints:
  `PATCH /api/v1/users/{user_id}/status`
  `PATCH /api/v1/contractors/{contractor_id}/status`
- Backend service hook:
  `UserStatusService.update_statuses(...)`

### 3. Contracts
- Local source of truth for approval remains `users.status`.
- Self-registered contractor may already have:
  - local `user_auth_accounts(provider='keycloak')`
  - Keycloak account without `acom-api` `app.contractor`
- On contractor transition to `active`, backend must:
  - resolve the active Keycloak binding from `user_auth_accounts`
  - assign the app role matching local `id_role` through `sync_keycloak_app_role_for_user(...)`
  - best-effort terminate Keycloak sessions so the next login/refresh picks up new claims

### 4. Validation & Error Matrix
- contractor status changes to `active` and active Keycloak binding exists -> sync `acom-api` app role for the linked Keycloak subject
- contractor status changes to `active` and no Keycloak binding exists -> keep local activation; skip Keycloak role sync
- non-contractor status changes to `active` -> do not run contractor Keycloak access sync
- contractor status changes away from `active` -> this activation hook does not assign app roles
- Keycloak role sync succeeds but session logout fails -> keep status change and role assignment; do not roll back local approval

### 5. Good/Base/Bad Cases
- Good: self-registered contractor is approved from `review` to `active`, receives `app.contractor` in `acom-api`, and next session refresh/login has business-access claims.
- Base: admin-created/manual contractor flows may still assign the same role earlier during explicit provisioning.
- Bad: rely on first successful login after approval to assign app roles lazily; this leaves approved contractors with linked Keycloak accounts but empty `api_roles`.

### 6. Tests Required
- Unit: contractor `review -> active` with Keycloak binding calls `sync_keycloak_app_role_for_user(...)`.
- Unit: same transition best-effort calls `logout_user_sessions(...)` after role sync.
- Unit: contractor activation without Keycloak binding skips sync.
- Integration: existing `/users/{id}/status` and `/contractors/{id}/status` enforcement fixtures stay aligned with the expanded `UserStatusService(...)` constructor.

### 7. Wrong vs Correct
#### Wrong
- Assume self-registration plus local approval is enough and wait for some later auth path to backfill missing Keycloak app roles.

#### Correct
- Treat local activation as the authoritative moment to grant Keycloak application access for self-registered contractors, using the stored Keycloak binding immediately in the status-change service.

## Scenario: Contractor Review Notifications Go To Admin Staff Only

### 1. Scope / Trigger
- Trigger: a contractor appears in `users.status=review` through self-registration, invite completion, or a manual/internal status transition that requires admin moderation.

### 2. Signatures
- Process event:
  `user.review_required`
- Backend handler:
  `ProcessNotificationEventHandler._handle_user_review_required(...)`

### 3. Contracts
- Recipient set for `user.review_required` is role-based:
  - `admin`
  - `superadmin`
- The contractor under review must never become a recipient of this moderation notification.
- Do not apply generic “exclude actor” behavior to this event; if an `admin` triggered the status transition, that admin still receives the moderation notification.

### 4. Validation & Error Matrix
- contractor self-registers into `review` -> notify `admin` + `superadmin`
- admin manually moves contractor into `review` -> notify `admin` + `superadmin`
- contractor is the event actor -> contractor still receives no `user.review_required` notification

### 5. Good/Base/Bad Cases
- Good: contractor finishes registration, and both admin roles see one moderation notification in the notification center.
- Base: ordinary process notifications may still exclude the actor when that is part of the product contract.
- Bad: reuse a generic “all recipients except actor” rule and accidentally suppress the initiating admin, or send the moderation notification to the contractor being reviewed.

### 6. Tests Required
- Unit: `user.review_required` with admin actor still creates notifications for both admin-role recipients.
- Unit: `user.review_required` with contractor actor creates notifications only for admin-role recipients.

### 7. Wrong vs Correct
#### Wrong
- Filter `user.review_required` recipients with `user.id != actor_user_id`.

#### Correct
- Build recipients strictly from `admin` / `superadmin` role membership and let the role filter, not the actor filter, decide visibility.

## Scenario: Aggregated Final Email Result Notifications

### 1. Scope / Trigger
- Trigger: a user launches a multi-recipient email operation where the product needs one final in-app result notification after worker-confirmed delivery, not a burst of per-recipient system notifications.

### 2. Signatures
- Request additional emails:
  `POST /api/v1/requests/{request_id}/email-notifications`
- Contractor invitations:
  `POST /api/v1/contractors/invite`
- Outbound email payload fields:
  `operation_id`
  `operation_kind`
  `operation_expected_total`
- Delivery feedback event fields:
  `operation_id`
  `operation_kind`
  `operation_expected_total`

### 3. Contracts
- `operation_id` groups all recipient deliveries that belong to one user action.
- `operation_kind` currently supports:
  - `request.additional_email`
  - `contractor.invite`
- `operation_expected_total` is the total intended recipient count for the operation, including items that may fail before worker delivery.
- The notification center may use one hidden tracking row in `user_notifications` with `payload.tracking_only="true"` while the batch is incomplete.
- Hidden tracking rows must not appear in list/unread APIs.
- Hidden tracking rows must not be delivered to the SPA as visible `notification.created` items; otherwise the later finalized event may reuse the same notification id and lose its push/display update.
- Final visible email-result notification must carry `payload.toast_channel="system"` and trigger a dedicated realtime `system.toast` event for top-center system UI, while the normal `notification.created` event still refreshes the notification center list.
- Final user-visible notification is emitted only when:
  - all worker delivery events for the operation are processed; and
  - any pre-worker queue failures are accounted for.

### 4. Validation & Error Matrix
- batch operation with final worker feedback complete -> emit one final aggregated notification to the initiator
- per-recipient worker events for a tracked batch -> do not emit separate initiator-facing `email.sent` / `email.failed` notifications
- duplicate delivery event with same `correlation_id` inside one `operation_id` -> ignore
- queue failure before worker delivery -> count it toward the same batch summary
- hidden tracking row still incomplete -> exclude from notifications list and unread count
- hidden tracking row reaches realtime/frontend state -> ignore it and still allow the later finalized notification with the same id to appear
- final email-result notification arrives with `toast_channel=system` -> do not show business push; show only system toast plus center update

### 5. Good/Base/Bad Cases
- Good: 10 invitations started, 7 delivered, 2 worker failures, 1 queue failure -> initiator gets one final summary with `7/10`, partial success, no burst of 10 notifications.
- Base: one-off email flow without batch metadata may still use ordinary per-email `email.sent` / `email.failed`.
- Bad: create one system notification per recipient for a batch operation and flood the notification center, or emit a “success” summary before worker delivery finishes.

### 6. Tests Required
- Unit: worker feedback with one `operation_id` finalizes exactly one notification after the last delivery event.
- Unit: queue-only total failure finalizes one `email.failed` aggregated summary without waiting for worker events.
- Unit: duplicate delivery `correlation_id` inside one batch does not increment counts twice.
- Unit/Frontend: tracking-only realtime notification is ignored, and the finalized visible notification with the same id still updates state and shows push UI.
- Unit/Frontend: `toast_channel=system` email result emits `system.toast` and skips the bottom-right business notification push.
- Integration: OIDC/request/invite flows pass operation metadata through the existing adapters where required.

### 7. Wrong vs Correct
#### Wrong
- Treat every recipient result as an independent initiator-facing system notification for batch operations.

#### Correct
- Use operation metadata plus one hidden tracking notification row, then publish one final aggregated initiator-facing result when the batch is fully resolved.

---

## Code Review Checklist

- [ ] Layering boundaries are preserved.
- [ ] UoW owns transactions.
- [ ] Repositories are persistence-only.
- [ ] DB changes have explicit SQL/migration patch.
- [ ] Runtime/gateway/network shape is unchanged unless explicitly requested.
- [ ] Legacy Telegram paths were considered when relevant.
- [ ] No secrets or temporary stubs were introduced.
