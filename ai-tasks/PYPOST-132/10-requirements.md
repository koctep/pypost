# PYPOST-132: Table hover performance during mouse movement

## Context

- **Jira:** PYPOST-132
- **Origin:** Follow-up from [PYPOST-15](https://pypost.atlassian.net/browse/PYPOST-15)
  (`40-tech-debt.md`): variable resolution in `mouseMoveEvent` may add load when users move
  the mouse across large header/param tables.
- **Related:** [PYPOST-122](https://pypost.atlassian.net/browse/PYPOST-122) optimized multiline
  body-editor hover with line-scoped expression scans.
- **Type:** Debt (Sprint 500)

## Problem statement

Key/value tables show variable tooltips while the pointer moves across many cells. Each move
can trigger placeholder detection and value resolution. Users expect tooltips to stay
responsive without perceptible lag when scanning long tables.

## Goals

- Confirm whether the PYPOST-122 hover optimization already addresses this concern.
- If not, reduce redundant work during rapid pointer movement over table cells.
- Preserve existing tooltip content and behaviour for header/param tables.

## Scope

### In scope

- Analysis of table hover path vs. PYPOST-122 line-scoped scan.
- Performance guard for `VariableAwareTableWidget` when appropriate.
- Unit test covering repeated moves over the same cell.
- Developer documentation of the table hover strategy.

### Out of scope

- Line-scoped scan for multiline editors (already delivered in PYPOST-122).
- Recursive tooltip resolution (PYPOST-123).
- UI automation for tooltip appearance (PYPOST-131).
- Caching across application sessions or global document indexes.

## User stories

- As a **user**, I want variable tooltips in header/param tables to remain smooth when I move
  the mouse across many rows so I can inspect templates without UI stutter.
- As a **user**, I want the same resolved tooltip values as before when hovering placeholder
  cells.

## Functional requirements

1. **FR-1:** Hover over a table cell containing `{{...}}` still shows the resolved tooltip.
2. **FR-2:** Hover over plain cells still hides the tooltip.
3. **FR-3:** Function expressions in table cells still resolve via the hover path.
4. **FR-4:** Multiline body and URL field hover behaviour is unchanged.

## Non-functional requirements

1. **NFR-1:** Repeated pointer moves over the same cell must not repeat full resolution work.
2. **NFR-2:** No new user-visible settings or configuration.
3. **NFR-3:** Cache must invalidate when environment variables or hidden keys change.

## Definition of Done

- [ ] Documented whether PYPOST-122 covers the table hover path.
- [ ] Table hover path optimized when line-scoped scan does not apply.
- [ ] Existing `tests/test_variable_hover.py` cases pass.
- [ ] New test covers cache behaviour on repeated mouse moves.
- [ ] `doc/dev/ui_mixins.md` documents the table hover strategy.

## Q&A

- **Q:** Does PYPOST-122 line-scoped scan fix table hover?
  **A:** No — it applies only to `VariableHoverMixin` multiline editors; tables use a separate
  per-cell path with bounded cell text.
- **Q:** Why not debounce with a timer?
  **A:** Per-cell caching avoids redundant resolution on intra-cell moves without delaying the
  first tooltip on cell entry.
