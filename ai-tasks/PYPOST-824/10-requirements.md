# PYPOST-824: Closing the rightmost request tab must not focus the + control

## Goals

Users who close the active request tab next to the trailing `+` (new tab) control must
land on another request workspace, never on `+`. Today that close path leaves focus on
`+`, which is not a request and breaks the multi-tab editing workflow. Automated checks
already encode this product rule and fail; this task restores correct focus after close so
those checks pass and the quality gate stays trustworthy.

Sibling tickets PYPOST-825 and PYPOST-826 cover the same product defect from related
test entry points; fixing focus after close addresses the shared root cause.

## Programming Language

Python 3.10+

## User Stories

- As a **desktop user**, when I close the rightmost of several request tabs (the one next
  to `+`), I want a remaining request tab to become active so I can keep editing or
  sending without clicking away from `+`.
- As a **desktop user**, when I close the current request tab via the usual close action
  (including when that tab is the rightmost request), I want focus to stay on a request
  tab, never on the `+` control.
- As a **maintainer**, I want the existing presenter regression tests for this focus rule
  to pass under `make test` so CI detects regressions of the Qt close/focus trap.

## Definition of Done

- Closing the rightmost of three request tabs leaves the active tab on a remaining
  request tab, not on `+`.
- Closing the rightmost of two request tabs leaves the active tab on the remaining
  request tab, not on `+`.
- Closing the current request tab via the close-current action leaves the active tab on a
  remaining request tab, not on `+`.
- The following tests pass under `make test`:
  - `test_close_rightmost_of_three_tabs_does_not_land_on_plus`
  - `test_close_rightmost_of_two_tabs_does_not_land_on_plus`
  - `test_handle_close_tab_closes_current`
- Related close-focus tests that already passed (e.g. close first of two, close middle of
  three, close last request tab) continue to pass.
- No intentional change to plus-tab semantics (still not closable; still not a request
  workspace) or to keyboard next/previous navigation rules beyond what close-focus needs.

## Task Description

**Problem:** After closing a request tab that sits immediately before the trailing `+`,
the active tab becomes `+`. Observed failure: `AssertionError` on
`assertNotEqual(current, plus_idx)` after closing index 2 with three request tabs
(and the same class of failure for the two-tab and close-current cases). Source:
PYPOST-824; deferred hardening from PYPOST-818 / PYPOST-820.

**Business need:** Closing a tab must leave the user in a real request workspace. Landing
on `+` interrupts work and confuses the tab chrome. Maintainers need the existing
regression tests green so this UX rule stays locked in CI.

### In Scope

- Correct post-close focus so the active tab is always a request tab when any remain
  (including after closing the rightmost request tab and via close-current).
- Making the three named failing tests pass; keeping related close-focus coverage green.
- Minimal production change on the close path; prefer reuse of existing navigable-tab
  concepts already used for next/previous tab.

### Out of Scope

- Redesign of the plus-tab chrome or new-tab UX.
- New MainWindow e2e / GUI automation beyond existing presenter tests.
- Changing collection-delete bulk close behavior except if the same focus rule must be
  applied for consistency (only if required for acceptance; otherwise follow-up).
- Broader tab-bar refactors unrelated to post-close focus.

## Functional Requirements

- After closing any request tab while at least one request tab remains, the active tab
  must be a request tab (not `+`).
- Close-current must obey the same rule (it closes the active request tab).
- Closing `+` remains a no-op.
- Closing the last remaining request tab still leaves the user on a blank replacement
  request tab (existing product rule), not on `+`.

## Non-functional Requirements

- **Regression protection:** Existing presenter tests for close-focus continue to run under
  the default quality gate.
- **Minimal change:** Prefer the smallest fix that restores correct focus; avoid unrelated
  tab-bar changes.
- **Consistency:** Post-close focus rules should align with next/previous navigation, which
  already skip `+`.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Tests already exist in `tests/test_tabs_presenter.py` with module
  `pytestmark = pytest.mark.timeout(60)`.
- Prior work: PYPOST-818 / PYPOST-820 documented optional explicit reselect after
  `removeTab` as deferred hardening; this task implements that product fix.
- Siblings PYPOST-825 / PYPOST-826 share the same root cause; one correct close-path fix
  is expected to clear all three.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Active tab | Currently focused tab after close |
| Close action | User closes a specific tab or the current tab |
| Navigable tabs | Request tabs the user may focus (excludes `+`) |

Interaction overview:

1. User has two or more request tabs plus trailing `+`.
2. User closes the rightmost request tab (or closes current while that tab is active).
3. System removes that tab and selects a remaining request tab.
4. User continues work on a request workspace; `+` is never the active tab.

## Q&A

- Q: Why is this a bug rather than a new test story?
  A: The product rule and tests already exist; production close leaves focus on `+`, so
  the tests fail and users hit broken focus.
- Q: Why not only fix one of the three tests?
  A: All three encode the same UX rule from different entry points; one close-path fix
  should satisfy all.
- Q: How does this relate to PYPOST-818 / PYPOST-820?
  A: Those tasks added regression tests and deferred explicit post-close reselect; this
  task implements that reselect because Qt `removeTab` lands on `+` for rightmost close.
- Q: May next/previous tab behavior change?
  A: Only if required for shared navigable-tab consistency; those paths already skip `+`.
- Q: What about PYPOST-825 / PYPOST-826?
  A: Same defect, different ticket entry points; fixing close focus here addresses the
  shared root cause (no separate product design expected).
