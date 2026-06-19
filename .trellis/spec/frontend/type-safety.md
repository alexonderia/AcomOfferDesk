# Type Safety

Frontend types should stay aligned with backend DTOs and API contracts.

## Rules

- Treat backend response shapes as the source of truth.
- Prefer explicit API response types over loose `any`-style typing.
- Keep the wire-format shape aligned with what the backend actually returns, even if it uses snake_case field names.
- Map data at the boundary instead of inventing parallel DTOs in the UI.

## Current Patterns

- API response helpers usually live in `web/src/shared/api/<area>/`.
- Feature hooks consume those helpers and turn the raw response into view state.
- Shared domain types live in `web/src/entities/*/model`.

## Do

- Reuse shared request/response types when they already exist.
- Keep role and permission constants in one shared place.
- Keep literal unions for statuses and route values narrow and consistent.

## Don't

- Do not create a second type definition for the same backend payload in another package.
- Do not widen a known status or permission code just to make TypeScript quieter.

## Scenario: Request Details Plan Labels Use `plan_name`

### 1. Scope / Trigger
- Trigger: the request details screen needs to render the assigned plan in read-only mode before or without loading plan selector options.

### 2. Signatures
- Backend API:
  `GET /api/v1/requests/{request_id}`
- Frontend API helper:
  `getRequestDetails(requestId: string): Promise<RequestDetails>`

### 3. Contracts
- Request details response keeps both plan fields:
  `id_plan: number | null`
  `plan_name: string | null`
- `id_plan` is the stable identifier for edit flows and PATCH payloads.
- `plan_name` is the display label for read-only request details when the selected plan option is not yet present in `getPlanOptions()`.
- Frontend boundary mapping in `web/src/shared/api/requests/getRequestDetails.ts` must preserve `plan_name` instead of deriving labels inside the view.

### 4. Validation & Error Matrix
- `id_plan=null` and `plan_name=null` -> UI shows "Без плана".
- `id_plan` present and matching option exists in `getPlanOptions()` -> UI shows option label (`plan_name + user_name`).
- `id_plan` present and options are still empty/unavailable, but response includes `plan_name` -> UI shows `plan_name`, not `План #<id>`.
- `id_plan` present and backend omitted `plan_name` -> treat as contract gap and expect a targeted backend/frontend fix instead of inventing a new parallel label source.

### 5. Good/Base/Bad Cases
- Good: request details returns `id_plan=3`, `plan_name="План закупок"`, and the read-only field shows `План закупок` immediately.
- Base: once plan options load, the same request may render the richer selector label with owner context.
- Bad: rely on `id_plan` alone in the read-only UI and fall back to `План #3`, which leaks an internal identifier instead of the business name.

### 6. Tests Required
- Backend contract/integration: `/api/v1/requests/{id}` response includes `plan_name` when `id_plan` is assigned.
- Frontend unit: `RequestDetailsView` shows `plan_name` when plan options are unavailable.
- Frontend unit: role navigation config for `/requests/:id` keeps the normal sidebar tabs and still exposes `backAction`.

### 7. Wrong vs Correct
#### Wrong
- Treat `id_plan` as enough information for read-only rendering and reconstruct a fallback label like `План #<id>` in the component.

#### Correct
- Keep `id_plan` for mutations and selection state, but pass `plan_name` through the request details API contract and use it as the read-only display source until richer option metadata is available.

## Scenario: Units Hierarchy Uses Separate Recommended Tree Contract

### 1. Scope / Trigger
- Trigger: the hierarchy management page needs to show both real `units` and a recommended tree derived from the current user hierarchy without mixing those models.

### 2. Signatures
- Backend API:
  `GET /api/v1/units/tree`
  `GET /api/v1/units/recommended-tree`
- Frontend API helpers:
  `getUnitsTree(): Promise<UnitNode[]>`
  `getRecommendedUnitsTree(): Promise<RecommendedHierarchyNode[]>`

### 3. Contracts
- `GET /api/v1/units/tree` remains the source of truth for writable hierarchy nodes backed by `units` and `unit_members`.
- `GET /api/v1/units/recommended-tree` returns a read-only tree of active internal users derived from `users.id_parent`, `profiles`, and `roles`.
- Recommended tree payload keeps its own wire shape and must not be normalized into `UnitNode`.
- Each recommended node includes:
  `user_id`, `full_name`, `role_id`, `role_name`, `status`, `id_parent_user`, `children`.
- Frontend boundary mapping in `web/src/shared/api/units/types.ts` must keep two separate normalizers:
  `normalizeUnitNode(...)`
  `normalizeRecommendedHierarchyNode(...)`

### 4. Validation & Error Matrix
- `units/tree` succeeds and `recommended-tree` fails -> page still renders real units tree and shows a warning for recommendations only.
- `recommended-tree` returns an empty list -> UI shows an informational empty state, not a fake placeholder tree.
- Backend adds/removes fields in the recommended payload -> update the dedicated recommended type/normalizer instead of widening `UnitNode`.
- User lacks `units.read` -> both endpoints stay forbidden; do not add a frontend-only fallback.

### 5. Good/Base/Bad Cases
- Good: the page renders actual unit cards from `/units/tree` and a separate read-only recommendation block from `/units/recommended-tree`.
- Base: recommendation data is unavailable, but unit CRUD still works because the writable tree uses its own contract.
- Bad: map recommendation rows into `UnitNode`, invent fake `unit_id` values, or expose create/update actions on recommendation nodes.

### 6. Tests Required
- Backend integration: `/api/v1/units/recommended-tree` returns the active manager-subordinate hierarchy for a permitted user.
- Backend unit: `UnitService.get_recommended_tree()` preserves parent-child order and nesting.
- Frontend unit: `useUnitHierarchyPage` loads both trees and keeps recommendation data separate from real units.
- Frontend route/nav tests remain green so `/admin/hierarchy` stays guarded by `units.read`.

### 7. Wrong vs Correct
#### Wrong
- Reuse the `UnitNode` type for both real units and recommendations because the UI “looks similar”.

#### Correct
- Keep recommendations as a distinct DTO and render them in a separate read-only section, while unit mutations continue to target only the real `units` API.
