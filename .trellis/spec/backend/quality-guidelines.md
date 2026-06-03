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

---

## Code Review Checklist

- [ ] Layering boundaries are preserved.
- [ ] UoW owns transactions.
- [ ] Repositories are persistence-only.
- [ ] DB changes have explicit SQL/migration patch.
- [ ] Runtime/gateway/network shape is unchanged unless explicitly requested.
- [ ] Legacy Telegram paths were considered when relevant.
- [ ] No secrets or temporary stubs were introduced.
