# Permissions And Roles

This file captures the current permission model in the backend.

## Source Of Truth

- `backend/app/domain/permissions.py` defines the canonical permission codes.
- `backend/app/services/keycloak_app_roles.py` maps local role IDs to Keycloak app roles.
- `backend/app/domain/auth_context.py` combines local role ceilings, token roles, and delegation scopes.
- `backend/app/api/action_flags.py` turns backend permission decisions into response `actions`.

## Roles

Current local role IDs:

- `1` - `superadmin`
- `2` - `admin`
- `3` - `contractor`
- `4` - `project_manager`
- `5` - `lead_economist`
- `6` - `economist`
- `7` - `operator`
- `8` - `security_officer`

Keycloak app roles:

- `app.superadmin`
- `app.admin`
- `app.project_manager`
- `app.lead_economist`
- `app.economist`
- `app.operator`
- `app.security_officer`
- `app.contractor`

## Permission Families

The backend permission codes are grouped by domain:

- users and user management
- profile and company contacts
- requests
- offers
- chat and message receipts
- feedback
- dashboards and plans
- normative files
- file downloads
- unavailability
- contractors
- units hierarchy
- department-scoped request/offer/chat/dashboard actions

## Contract Rules

- Backend permissions are authoritative.
- Frontend `role_id` checks are UX hints only.
- Backend `actions` arrays/objects are the real per-resource control surface.
- If a permission changes, update:
  - the backend permission map
  - the Keycloak role mapping/bootstrap
  - the backend access checks
  - the frontend guards and menus

## Practical Rules

- Prefer `has_permission(...)` or the existing policy helpers instead of string-comparing roles directly.
- Use role ceilings for access control, not just for display decisions.
- `department.*` and `delegation.*` scopes are extensions, not replacements, for the normal permission matrix.
- Do not add a parallel permission system in the frontend.

## Units Hierarchy Contract

- `units.read` gates both the actual units tree and the recommended hierarchy tree derived from `users.id_parent`.
- `units.create`, `units.update`, and `units.members.manage` apply only to real `units` / `unit_members` mutations.
- The recommended hierarchy is a read-only helper source built from the current user management chain and must not be treated as a second writable unit model.
