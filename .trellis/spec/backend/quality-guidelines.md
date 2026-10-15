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
- Keep E2E IAM users and credentials explicit in environment secrets; smoke tests must use the same BFF login entrypoint as a browser.
- Review-stage contractor onboarding must use dedicated registration-only self-profile endpoints. Do not weaken the normal `/users/me*` permission gates for already-authenticated pages.
- Keep in-memory integration fixtures aligned with current dataclass constructors and service factory signatures; when request/offer schemas gain or lose fields, update the test factories in the same change.
- Keep removed external messenger integrations out of runtime, API, frontend, compose, and worker delivery paths.
- For DB changes, include SQL/migration patch and rollout notes.
- For infra changes, preserve `gateway`, `project_net`, and tunnel routing.

---

## Forbidden Patterns

- Business logic in API routes.
- Permission enforcement only on the frontend.
- Repository methods that decide business policy.
- Direct public exposure of backend, IAM internal APIs, RabbitMQ, MinIO, PostgreSQL, or admin ports in `test`/`prod`.
- Hardcoded secrets, tokens, passwords, or production hostnames.
- Temporary placeholder implementations, mock-only production paths, or TODO-dependent behavior.
- Reintroducing external messenger runtime or UI through legacy database compatibility values.
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

## Scenario: Gateway Maintenance Fallback And Manual Maintenance Mode

### 1. Scope / Trigger
- Trigger: any change to gateway/nginx runtime routing, compose service dependencies, or maintenance-mode behavior.

### 2. Signatures
- Compose files:
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `docker-compose.prod-like.yml`
  - `docker-compose.prod.yml`
  - `docker-compose.test.yml`
  - `docker-compose.maintenance.yml`
- Gateway configs:
  - `backend/nginx.conf`
  - `infra/maintenance/gateway.maintenance.conf`
  - `infra/maintenance/default.conf`
- Public routes:
  - `/`
  - `/api/*`
  - `/iam/*`
  - `/health`

### 3. Contracts
- Runtime service contract:
  - `maintenance` is a dedicated internal nginx service on `project_net`.
  - `maintenance` is never published directly with public `ports`.
  - `gateway` remains the single public entrypoint.
- Automatic fallback contract:
  - `/` falls back to the maintenance page when `web` is unavailable.
  - Browser-facing auth endpoints under `/api/v1/auth/` (`login` and `callback`) also fall back to the maintenance page when `backend` is unavailable.
  - `/api/*` returns controlled JSON `503` when `backend` is unavailable:
    `{"detail":"Система временно недоступна. Ведутся технические работы."}`
  - `/iam/*` keeps routing to the project IAM service while IAM itself is available.
  - `/health` may return `503` when backend health is unavailable in normal mode.
- Manual maintenance contract:
  - enable by adding `docker-compose.maintenance.yml`;
  - `/` and `/iam/*` return the maintenance page;
  - `/api/*` returns maintenance JSON `503`;
  - `/health` returns from the maintenance contour so gateway stays reachable.

### 4. Validation & Error Matrix
- `web` unavailable in normal mode -> `/` returns maintenance HTML, not default nginx `502`
- `backend` unavailable in normal mode -> `/api/*` returns controlled JSON `503`
- `iam` unavailable in normal mode -> `/iam/*` remains unavailable; do not silently reroute IAM to backend/web
- manual maintenance override enabled -> all user-facing web/IAM paths return maintenance HTML, API remains controlled `503`
- adding a new public service port for maintenance -> forbidden

### 5. Good/Base/Bad Cases
- Good: `gateway` starts with `maintenance`; `web` is down; `GET /` still shows the maintenance page.
- Good: `backend` is down; `GET /api/v1/auth/login?next=%2F` still shows the maintenance page instead of raw JSON.
- Base: all upstreams are healthy; routing stays `/ -> web`, `/api/* -> backend`, `/iam/* -> iam`.
- Bad: `gateway` depends on healthy `web`/`backend`, so the entrypoint never starts and users only see edge-level failure.

### 6. Tests Required
- Config: `docker compose ... config` passes for normal and maintenance override stacks.
- Syntax: nginx config test passes for `backend/nginx.conf`, `infra/maintenance/default.conf`, and `infra/maintenance/gateway.maintenance.conf`.
- Smoke:
  - stop `web` -> assert `/` returns maintenance HTML instead of raw `502`
  - stop `backend` -> assert `/api/v1/auth/login?next=%2F` returns maintenance HTML
  - stop `backend` -> assert `/api/health` returns JSON `503`
  - enable `docker-compose.maintenance.yml` -> assert `/` returns maintenance HTML and `/api/health` returns JSON `503`

### 7. Wrong vs Correct
#### Wrong
- Implement maintenance as part of `backend` or `web`, or publish a separate external maintenance port.

#### Correct
- Keep maintenance as a dedicated internal service behind `gateway`, with automatic frontend/API fallback and an explicit compose override for manual full-maintenance mode.

## Scenario: Isolated File Upload Guard

### 1. Scope / Trigger
- Trigger: any change that accepts user-uploaded files from HTTP endpoints or adds a new storage-bound file ingestion path.

### 2. Signatures
- Backend shared seam:
  `FileService.prepare_upload(upload: UploadFile) -> PreparedUpload`
  `FileService.prepare_bytes(original_name, content_bytes, mime_type) -> PreparedUpload`
- Backend guard orchestration:
  `FileUploadGuardService.scan_bytes(...) -> GuardedUpload`
- Internal scanner API:
  `POST http://file_guard:8080/scan`
- File guard health:
  `GET http://file_guard:8080/health`

### 3. Contracts
- HTTP upload routes should pass already prepared `PreparedUpload` objects into request/offer/chat/normative services instead of re-validating the same file bytes again.
- `file_guard` stays internal-only on `project_net`; it is not exposed through `gateway` or public `ports`.
- `file_guard` must not receive backend DB, IAM, or MinIO secrets through the shared runtime env file. Give it only the minimum env keys it needs.
- Backend env keys:
  `FILE_GUARD_ENABLED`
  `FILE_GUARD_URL`
  `FILE_GUARD_TIMEOUT_SECONDS`
- File guard env keys:
  `FILE_GUARD_MAX_FILE_SIZE_BYTES`
  optional `FILE_GUARD_ALLOW_LIBMAGIC_FALLBACK`
- Allowed MVP types:
  `.pdf`
  `.docx`
  `.xlsx`
  `.jpg`
  `.jpeg`
  `.png`

### 4. Validation & Error Matrix
- file size exceeds backend limit before scanner call -> `422 file_too_large`
- scanner verdict `allowed=false` -> backend returns `422` with `reason_code`
- scanner unavailable / timeout / invalid response -> backend returns fail-closed `503 file_scan_unavailable`
- blocked or unavailable scan -> do not write file to MinIO and do not attach DB records
- allowed scan -> continue with the existing storage + DB flow

### 5. Good/Base/Bad Cases
- Good: request/offer/chat/normative uploads all pass through the same guard seam before persistence.
- Base: non-HTTP byte sources (for example email ingestion) may still use `prepare_bytes(...)`, but they should still hit the same guard service once.
- Bad: each route hand-rolls its own upload checks, or `file_guard` inherits the full backend env contract with unrelated secrets.

### 6. Tests Required
- Unit: `FileUploadGuardService` allowed verdict, blocked verdict, and unavailable-scanner fail-closed behavior.
- Integration: at least one upload endpoint returns `reason_code` when the scanner blocks a file.
- Service/API regression: request/offer/normative upload contract tests still pass after switching route -> service payloads to `PreparedUpload`.
- Runtime: `docker compose ... config` shows `backend -> file_guard` dependency and no public `ports` for `file_guard`.

### 7. Wrong vs Correct
#### Wrong
- Validate/sanitize/scan the same HTTP file multiple times across route and service layers, or let `file_guard` read the shared backend env file with DB/identity/storage secrets.

#### Correct
- Read/prepare the HTTP upload once, pass `PreparedUpload` through the service flow, and keep `file_guard` isolated with a minimal env contract and fail-closed backend integration.

---

## Code Review Checklist

- [ ] Layering boundaries are preserved.
- [ ] UoW owns transactions.
- [ ] Repositories are persistence-only.
- [ ] DB changes have explicit SQL/migration patch.
- [ ] Runtime/gateway/network shape is unchanged unless explicitly requested.
- [ ] Legacy database compatibility fields were not exposed as active integration paths.
- [ ] No secrets or temporary stubs were introduced.
