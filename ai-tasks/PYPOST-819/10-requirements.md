# PYPOST-819: Focus stays valid after closing the last request tab

## Goals

Users who close their only open request tab must land on a real request workspace, not on
the trailing `+` (new tab) control. This task adds a regression test so that replacement-tab
behavior and focus cannot silently break.

## User Stories

- As a **user**, when I close the last open request tab, I want a usable request tab to remain
  focused so I can keep working without clicking the `+` control.
- As a **user**, I do not want the `+` control to become the only "active" tab with no request
  workspace selected.
- As a **maintainer**, I want an automated presenter test under `make test` that locks this
  last-tab close focus rule in place (sibling of PYPOST-818).

## Definition of Done

- A test covers closing the last request tab.
- The test asserts focus is not incorrectly on the `+` control as the only active tab without
  a request.
- The test documents the product expectation: closing the last request tab creates a
  replacement blank request tab and focuses it (not other undefined empty states).
- The test runs under `make test` and passes.
- Prefer test-only change; production code only if the test reveals a real bug.

## Task Description

**Problem:** After closing the last request tab, focus must remain on a request tab created as
a replacement, not the trailing new-tab control. Without a regression test, changes to the
close path could leave the `+` selected with no request workspace.

**Scope**

- In scope: presenter-level regression test for last-tab close-then-focus behavior; production
  fix only if behavior is wrong today.
- Out of scope: keyboard shortcut UX changes, MainWindow e2e tests, redesign of the plus tab,
  changes to multi-tab close focus (covered by PYPOST-818).

**Constraints and assumptions**

- Programming language: Python.
- Existing helpers in `tests/test_tabs_presenter.py` (`_make_presenter`, `_plus_tab_index`,
  `close_tab`) are the preferred test surface.
- Module already declares `pytestmark = pytest.mark.timeout(60)`.
- Product already replaces the last closed tab in many cases; verify and assert that path.

## Main entities (business)

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Replacement tab | Blank request tab created when the last request tab is closed |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Active tab | The currently focused tab after close |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this a test story? | To lock expected UX: after closing the last tab, focus is on a replacement request tab, not `+`. |
| Why not only manual QA? | Regression must run in CI via `make test`. |
| Production changes? | Only if the new test fails against current behavior. |
| Relation to PYPOST-818? | Sibling: 818 covers closing first of two; 819 covers closing the last remaining request tab. |
