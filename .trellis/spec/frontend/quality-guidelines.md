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

### Convention: Mobile Notification Center Sheet

- On mobile, the notification center opens as a centered full-width fullscreen sheet instead of a corner-anchored popover.
- Hide desktop resize affordances on the mobile sheet; let the viewport define the panel width and height.
- Keep the overlay/modal container responsible for centering and backdrop behavior, not the inner panel.

### Convention: HTML Email Source Preview

- When showing a generated email preview for users, render the HTML as an actual visual preview rather than a code block.
- Keep the preview aligned with the backend template structure so the rendered content mirrors the sent email body.
- Use placeholder tokens for environment-specific values that the frontend cannot know, instead of inventing fake runtime data.

### Convention: Mobile Breadcrumb Actions

- Breadcrumb actions may collapse to icon-only controls on narrow viewports when text would waste space.
- Keep the action accessible with an `aria-label` that matches the removed text.
- Preserve the desktop text label on larger viewports when there is room for it.

### Convention: Mobile Bottom Navigation Slot Budget

- Keep the bottom navigation within its intended slot budget so the `more` entry remains visible on mobile.
- When a new primary destination is needed, prefer placing it inside `more` rather than pushing `more` off-screen.
- If a new item must become top-level, update the slot budget and responsive layout together with tests so the change is intentional.

### Convention: Scoped Admin Create Dialog Roles

- When one admin create dialog is reused across employee and contractor tabs, scope the available create-role options to the active tab instead of exposing cross-tab creation paths.
- On employee tabs, contractor creation must stay out of the employee role dropdown when there is a dedicated contractor entry point elsewhere in the UI.
- If the active tab has no available create roles after scoping, hide the add action instead of opening a dialog with unrelated options.
- Superadmin is the exception to tab scoping: keep the full role list available, but move the current tab's role to the first position when it is present.

### Convention: Recommended Hierarchy Uses Org Chart Layout

- When a read-only recommendation tree is derived from current user hierarchy, render it as an org chart with explicit parent-child connectors instead of a plain indented card list.
- Keep the recommendation chart visually separate from the editable units tree so users do not confuse guidance with the source-of-truth structure.
- Prefer a horizontally scrollable chart container over wrapping children to the next line, because wrapped branches break connector readability on dense hierarchies.
- Keep editing actions out of the recommendation chart cards; CRUD stays attached only to the real units tree.
- When the chart follows a visual reference similar to a corporate org diagram, prefer a neutral light canvas, white node cards, and thin blue connectors over saturated gradients or oversized chips.
- Prefer a restrained system-style surface: flat light canvas, white cards, standard-radius corners, and low-contrast borders over decorative gradients or showcase-style depth.
- When recommendation data has multiple roots, render each root as its own centered subtree instead of merging all roots into one shared top row with a single connector band.
- Do not show unlabeled numeric legends inside recommendation cards; if hierarchy metadata is useful, present it with explicit captions such as `Подчинённые` or `Логин`.
- For MUI connector boxes, never use numeric `width: 1` or `height: 1` when you mean a 1px line: sizing props treat `1` as percentage-based sizing, so use string pixel values such as `width: '1px'` and `height: '1px'`.

### Convention: Combined Hierarchy Shows Per-Assignment Cards

- In the combined hierarchy, show unit affiliation directly on each duplicated employee mini-card instead of wrapping several cards into one shared unit container.
- Within one role level, place duplicated cards in module-oriented clusters so each copy stays visually near the relevant unit area.
- Highlight module-oriented clusters with subtle dashed module frames behind the cards so cross-department duplicates still read as hanging from the target module area.
- If one employee belongs to multiple units, duplicate the employee mini-card for each assignment while keeping the employee at the same role level in the reporting tree.
- If a recommended-hierarchy member has no unit assignment but still belongs to a reporting chain, keep that card inside the nearest department chain inferred from the hierarchy instead of moving it into a separate fallback column.
- Cards without a real unit assignment should stay outside module frames and show an explicit no-unit badge such as `Не определено`; placeholder vacancies may keep the empty-slot label.
- Keep visual hierarchy subtle: department containers may be slightly heavier than employee cards, but all surfaces should still feel like standard application cards rather than custom marketing panels.
- Empty combined-hierarchy slots should stay interactive: use a visible placeholder card that opens the existing assignment flow instead of introducing a new ad hoc edit path.

### Convention: Unit Hierarchy Uses Expandable Block Cards

- In the units hierarchy, render each unit as a block card with summary metadata, not as a thin label floating above member cards.
- Keep a single units-hierarchy representation sourced directly from the backend `units tree`; do not maintain a second frontend-only participant layout that can diverge from DB membership.
- Keep helper copy on the hierarchy page terse: prefer short labels and empty states over explanatory paragraphs in side panels, cards, and dialogs.
- Open the participant list in a dedicated details panel on the same page when the user clicks the unit card, and keep add/remove member actions inside that side panel instead of a modal dialog.
- Empty member lists and leaf-unit child areas should use interactive placeholders that lead into the existing "add employee" and "create child unit" flows.

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
