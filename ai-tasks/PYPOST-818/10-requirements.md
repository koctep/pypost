# PYPOST-818: Focus stays on remaining request tab after closing first of two

## Goals

Users who work with multiple request tabs must keep working on a real request after closing
another tab. Focus must never land on the trailing `+` (new tab) control, which is not a
request workspace. This task adds a regression test so that behavior cannot silently break.

## User Stories

- As a **user**, when I close the first of two open request tabs, I want the remaining request
  tab to stay active so I can continue editing or sending without clicking again.
- As a **user**, I do not want the `+` control to become the active tab after a close, because
  that is not a request and interrupts my workflow.
- As a **maintainer**, I want an automated presenter test under `make test` that locks this
  focus rule in place.

## Definition of Done

- A test opens two request tabs (plus the `+` control).
- The test closes the first request tab.
- The test asserts the active/focused tab is the remaining request tab.
- The test asserts the focused tab is not the `+` (new tab) control.
- The test runs under `make test` and passes.
- Prefer test-only change; production code only if the test reveals a real bug.

## Task Description

**Problem:** After closing one of several request tabs, focus must remain on a request tab, not
the trailing new-tab control. Without a regression test, Qt tab-bar index shifts or close-path
changes could leave the `+` selected.

**Scope**

- In scope: presenter-level regression test for close-then-focus behavior; production fix only
  if behavior is wrong today.
- Out of scope: keyboard shortcut UX changes, MainWindow e2e tests, redesign of the plus tab.

**Constraints and assumptions**

- Programming language: Python.
- Existing helpers in `tests/test_tabs_presenter.py` (`_make_presenter`, `_plus_tab_index`,
  `close_tab`) are the preferred test surface.
- Module already declares `pytestmark = pytest.mark.timeout(60)`.

## Main entities (business)

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Active tab | The currently focused tab after close |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this a test story? | To lock expected UX: after close, focus stays on a request tab, not `+`. |
| Why not only manual QA? | Regression must run in CI via `make test`. |
| Production changes? | Only if the new test fails against current behavior. |
