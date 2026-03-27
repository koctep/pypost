# PYPOST-424: Expose request timeout in application settings

## Programming language

**Python** — This task applies to the PyPost desktop/UI codebase where settings are
implemented. Downstream steps must follow `.cursor/lsr/do-python.md` for style and
quality expectations.

## Problem statement

Work under **[PYPOST-402]** introduced configuration for **request timeout** so
operators can limit how long the application waits for network responses. A numeric
control for this value was created in code, but it was **not added to the visible
settings form layout**. As a result, users cannot see or change this value through
the settings screen even though the underlying setting exists and is wired in logic.

The business impact is reduced **control and transparency**: administrators cannot
adjust timeout behavior from the UI, which can force workarounds or leave
misconfigured timeouts undetected.

## Goals

- Ensure **request timeout** is **discoverable and editable** wherever other
  connection-related settings are presented.
- Align user-visible behavior with the intent of PYPOST-402: timeout is a
  first-class setting, not a hidden constant.

## Scope

### In scope

- **Visibility and placement** of the request timeout control on the relevant
  settings form so it appears with comparable settings.
- **End-to-end usability** from the user perspective: view current value, change
  it, and persist it with the rest of settings (consistent with existing settings
  behavior).
- **Regression check** that saving and loading settings still behave correctly
  when the control is on the form.

### Out of scope

- Changing the **default** timeout value or the **meaning** of the field (unless
  required to fix a defect uncovered while testing).
- New **backend services**, protocols, or **API** contracts beyond what the
  application already uses for settings.
- **Unrelated** settings fields, themes, or dialogs.
- **Documentation** deliverables tracked under STEP 7 (may reference this work
  later, but not part of requirements completion).

## User stories

- As an **operator**, I want to **see** the current request timeout in settings so
  I know what value the application will use.
- As an **operator**, I want to **change** the request timeout and **save** my
  settings so I can tune behavior for slow or unreliable networks without
  editing files or using unsupported paths.

## Functional requirements

1. **FR-1 (Discoverability)** — The settings UI that lists connection-related
   options must **include** request timeout so it is visible without hidden
   dialogs or developer-only paths.

2. **FR-2 (Editability)** — The user must be able to **adjust** the timeout using
   the same interaction patterns as other numeric limits in that form, consistent
   with product conventions for comparable fields.

3. **FR-3 (Persistence)** — Changing the value and applying or saving settings
   must **update stored configuration** together with other settings, consistent
   with existing save semantics.

4. **FR-4 (Load)** — On opening settings, the control must **reflect** the
   currently stored timeout value.

5. **FR-5 (Consistency)** — Labels and grouping should **match** the rest of the
   settings form so users understand the field in context (e.g. near related
   connection or HTTP options if those exist).

## Non-functional requirements

1. **NFR-1 (Consistency)** — Interaction patterns, validation bounds, and visual
   hierarchy should match adjacent settings controls unless a documented product
   reason dictates otherwise.

2. **NFR-2 (Reliability)** — No new crashes or broken save/load flows for
   settings; existing tests or checks for settings should remain passing or be
   updated as needed.

3. **NFR-3 (Maintainability)** — The change should not duplicate conflicting
   definitions of the same setting; a single clear path from UI to stored value.

## Acceptance criteria

1. Opening the **same settings dialog** that already manages connection-related
   options shows **request timeout** alongside those options.

2. The displayed value **matches** the persisted configuration when settings are
   opened.

3. After the user **changes** the timeout and confirms save/apply per product
   conventions, the new value **persists** across application restart (or is
   verifiable through the same mechanism used for other settings).

4. Verification for the settings area (including automated tests where they
   exist) **passes**, or minimal follow-up is agreed for development steps.

5. No duplicate or orphaned controls: the timeout is managed **once** through the
   visible form.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| Risk | Layout changes might affect dialog sizing or tab order; verify on target |
| | platforms used by the team. |
| Risk | If two code paths set the same value, merging the control into the layout |
| | could expose inconsistent behavior; confirm a single source of truth. |
| Assumption | Stored request timeout semantics and valid range are already defined |
| | and only visible placement in settings was missing. |
| Assumption | Product copy (label/tooltip) can follow existing patterns for similar |
| | fields without a separate content ticket. |

## Definition of done (STEP 1)

- Requirements above are **approved** by the stakeholder after review.
- **Product Owner review:** Business logic reviewed; requirements approved for
  STEP 2 (architecture). (2025-03-27)
- Roadmap **STEP 1** marked complete and **STEP 2** not started until approval.
