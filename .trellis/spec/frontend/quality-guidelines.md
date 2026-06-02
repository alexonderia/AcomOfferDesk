# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

Frontend work must preserve the thin-client architecture. The React app is responsible for presenting data and ergonomics, not for final business authorization.

---

## Required Patterns

- Inspect affected files before proposing edits.
- Prefer existing feature/shared structure over new ad hoc folders.
- Consume backend `permissions`, backend `actions`, and HATEOAS/action metadata for UX gating.
- Treat `role_id` as UX-only.
- Default missing action flags to disabled/hidden.
- Keep API calls in `web/src/shared/api/*` and feature hooks/models, not scattered through presentational components.
- Keep secrets out of frontend code and env examples.
- For background polling + push UX flows, guard against burst loops: single-flight fetches, throttled refresh triggers, and ID-based dedupe for already-shown toasts.

### Convention: Subtle Hover Emphasis

- When highlighting an info card or details panel on hover/focus, prefer a single 1px border color change and a subtle shadow.
- Avoid stacking a second outline ring on top of the border unless the interaction needs a strong selection state.
- Keep hover emphasis visually lighter for read-only helper content, especially in dense detail layouts.

### Convention: Viewport-Clamped Floating Panels

- Floating panels that remember size across sessions must clamp their saved and rendered dimensions to the current viewport.
- Let the outer popover/drawer container own the responsive width and height, and keep the inner panel flexible with `width: 100%`, `height: 100%`, `minWidth: 0`, and `minHeight: 0`.
- Re-clamp on window resize so the stored size never renders outside the available screen area.

---

## Forbidden Patterns

- Final permission decisions in frontend.
- Copying backend policy rules into React components.
- New role-only checks for protected business actions.
- Hardcoded production URLs, tokens, credentials, or environment-specific secrets.
- Temporary stubs, fake production data, or TODO-gated behavior.
- UI changes that assume DB/schema changes without an explicit backend/DB patch.

---

## Permissions Review Checklist

- [ ] Does the UI use backend-provided permissions/actions for protected controls?
- [ ] Is any `roleId` usage limited to UX routing/menu/visibility?
- [ ] Does a backend endpoint enforce the same action?
- [ ] Are disabled/hidden states safe when action metadata is missing?
- [ ] If the contract changed, were backend schemas/mappers/UI consumers reviewed together?

---

## Testing Requirements

Run the narrowest meaningful checks and report them. Typical frontend checks:

```powershell
npm --prefix web run build
```

If checks cannot be run, state why and list the residual risk.

---

## Code Review Checklist

- [ ] Thin-client boundary is preserved.
- [ ] No frontend-only authorization was introduced.
- [ ] Backend action metadata is consumed consistently.
- [ ] Components remain reusable and scoped to existing feature/shared structure.
- [ ] No secrets or temporary stubs were introduced.
