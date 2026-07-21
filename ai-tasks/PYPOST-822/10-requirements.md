# PYPOST-822: Tab switch hotkeys keep focus on request tabs

## Goals

Users who switch between request tabs with keyboard shortcuts must land only on real
request workspaces. The trailing `+` (new tab) control is not a request and must never
become the focused tab when cycling with next/previous tab hotkeys. This task adds a
regression test so that behavior cannot silently break, extending the close-focus coverage
from PYPOST-818/819/820 to keyboard tab switching.

## User Stories

- As a **user**, when I press next/previous tab shortcuts with two or more request tabs
  open, I want focus to move only among request tabs so I can keep editing or sending.
- As a **user**, I do not want the `+` control to become active while cycling tabs, because
  that is not a request and interrupts my workflow.
- As a **maintainer**, I want an automated test under `make test` that exercises the product
  next/previous tab hotkey mapping (not only an isolated slot call) and locks the focus rule.

## Definition of Done

- A test opens at least two request tabs (plus the `+` control).
- The test exercises previous and next tab actions via the product hotkey map path (or the
  closest reliable product path if synthetic key delivery is flaky offscreen).
- The test asserts focus stays on a request tab and is never the `+` control while switching.
- The test runs under `make test` and passes.
- Prefer test-only change; production code only if the test reveals a real bug.

## Task Description

**Problem:** Next/previous tab shortcuts must cycle request tabs and skip the trailing new-tab
control. Existing presenter tests call `handle_next_tab` / `handle_previous_tab` directly and
check index cycling, but do not lock the hotkey-map wiring together with the “never focus `+`”
rule that PYPOST-818/819/820 cover for close flows.

**Scope**

- In scope: regression test for next/previous tab hotkey switching focus; production fix only
  if behavior is wrong today.
- Out of scope: redesign of tab chrome, new shortcut bindings, MainWindow full e2e unless
  required to exercise the hotkey map reliably.

**Constraints and assumptions**

- Programming language: Python.
- Product hotkeys for this story: next tab and previous tab bindings from the application
  hotkey map (Help → Hotkeys / Tabs section).
- Existing helpers and patterns in `tests/test_tabs_presenter.py` are the preferred surface
  unless a small focused hotkey test fits better beside existing hotkey tests.
- Module-level timeout markers already used by sibling presenter tests must be respected.

## Main entities (business)

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Next / previous tab hotkeys | Keyboard actions that move focus among request tabs |
| Active tab | The currently focused tab after a switch |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this a test story? | To lock UX: tab-switch hotkeys never focus `+`. |
| Why not only call slots directly? | Acceptance wants the product hotkey map path validated. |
| How does this relate to PYPOST-818/820? | Same focus rule; those cover close, this covers switch hotkeys. |
| Production changes? | Only if the new test fails against current behavior. |
