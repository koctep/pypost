# PYPOST-825: Closing the rightmost of two request tabs must not focus the + control

## Goals

Users who close the rightmost of two request tabs (the tab next to trailing `+`) must land
on the remaining request workspace, never on `+`. The product rule and automated check
already exist; this ticket tracks the failure of
`test_close_rightmost_of_two_tabs_does_not_land_on_plus` so maintainers can close the gap
and keep CI trustworthy. Sibling tickets PYPOST-824 and PYPOST-826 cover the same defect
from related close entry points; one correct close-path fix addresses the shared root
cause.

## Programming Language

Python 3.10+

## User Stories

- As a **desktop user**, when I have two request tabs and close the one next to `+`, I
  want the remaining request tab to become active so I can keep editing without clicking
  away from `+`.
- As a **maintainer**, I want
  `test_close_rightmost_of_two_tabs_does_not_land_on_plus` (and related land-on-plus /
  close-current checks) to pass under `make test` so CI detects regressions of this focus
  rule.

## Definition of Done

- Closing the rightmost of two request tabs leaves the active tab on the remaining
  request tab, not on `+`.
- The named test `test_close_rightmost_of_two_tabs_does_not_land_on_plus` passes under
  `make test`.
- Related land-on-plus / close-focus tests continue to pass (including three-tab
  rightmost close and close-current).
- No duplicate production change is required if the shared close-path fix from PYPOST-824
  already satisfies this acceptance (verification-only close is acceptable).
- No intentional change to plus-tab semantics beyond what post-close focus needs.

## Task Description

**Problem:** After closing the rightmost of two request tabs, the active tab becomes `+`.
Observed failure class: `AssertionError` on `assertNotEqual(current, plus_idx)` after
`close_tab(1)` with two request tabs. Source: PYPOST-825; same root cause as PYPOST-824
(three-tab rightmost) and PYPOST-826 (close-current).

**Business need:** Closing a tab must leave the user in a real request workspace. Landing
on `+` interrupts work. Maintainers need the existing two-tab regression test green so
this UX rule stays locked in CI.

### In Scope

- Confirm post-close focus leaves a request tab active after closing the rightmost of
  two request tabs.
- Verify the named test and related land-on-plus / close-focus coverage under `make test`.
- Document verification against the shared close-path fix; avoid a second production
  change unless tests still fail.

### Out of Scope

- Redesign of the plus-tab chrome or new-tab UX.
- New MainWindow e2e / GUI automation beyond existing presenter tests.
- Separate bulk `close_tabs_for_request_ids` focus work (tracked elsewhere if needed).
- Broader tab-bar refactors unrelated to post-close focus.

## Functional Requirements

- After closing the rightmost of two request tabs while one request tab remains, the
  active tab must be that remaining request tab (not `+`).
- Closing `+` remains a no-op.
- Closing the last remaining request tab still leaves the user on a blank replacement
  request tab (existing product rule), not on `+`.

## Non-functional Requirements

- **Regression protection:** Existing presenter tests for close-focus continue to run
  under the default quality gate.
- **No duplicate fix:** Prefer verification against the shared PYPOST-824 close-path
  correction over a second production edit of the same behavior.
- **Consistency:** Post-close focus rules align with next/previous navigation, which
  already skip `+`.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Test already exists in `tests/test_tabs_presenter.py` with module
  `pytestmark = pytest.mark.timeout(60)`.
- Production fix is already in `TabsPresenter.close_tab` from PYPOST-824 (navigable
  reselect after `removeTab`).
- Siblings PYPOST-824 / PYPOST-826 share the same root cause.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Active tab | Currently focused tab after close |
| Close action | User closes a specific tab (here: rightmost of two) |
| Navigable tabs | Request tabs the user may focus (excludes `+`) |

Interaction overview:

1. User has two request tabs plus trailing `+`.
2. User closes the rightmost request tab (index adjacent to `+`).
3. System removes that tab and selects the remaining request tab.
4. User continues work on a request workspace; `+` is never the active tab.

## Q&A

- Q: Why is this a bug rather than a new test story?
  A: The product rule and test already exist; production close left focus on `+`, so
  the test failed and users hit broken focus.
- Q: Why a separate ticket from PYPOST-824?
  A: Same defect, different failing test entry point (two-tab rightmost vs three-tab /
  close-current). One close-path fix clears all siblings.
- Q: Is a new production change required here?
  A: Only if verification shows the named test still fails after PYPOST-824. Otherwise
  this task documents verified-fixed and closes without duplicate code.
