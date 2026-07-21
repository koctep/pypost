# PYPOST-826: Close-current must not leave focus on the + control

## Goals

Users who close the **current** request tab (close-current action) must land on another
request workspace, never on the trailing `+` control. Automated checks already encode
this rule via `test_handle_close_tab_closes_current`; this ticket confirms that failure is
resolved so the quality gate stays trustworthy for the close-current entry point.

Sibling tickets PYPOST-824 and PYPOST-825 cover the same product defect from related
close entry points. The shared root cause is post-close focus after removing a request
tab next to `+`.

## Programming Language

Python 3.10+

## User Stories

- As a **desktop user**, when I close the current request tab (including when it is the
  rightmost request tab next to `+`), I want a remaining request tab to become active so
  I can keep editing without clicking away from `+`.
- As a **maintainer**, I want `test_handle_close_tab_closes_current` to pass under the
  default test suite so CI detects regressions of close-current focus.

## Definition of Done

- Closing the current request tab via the close-current action leaves the active tab on a
  remaining request tab, not on `+`, when at least one request tab remains.
- `test_handle_close_tab_closes_current` passes.
- No duplicate production change is required if the shared close-path fix from PYPOST-824
  already satisfies this entry point (verified by running the named test).
- Plus-tab semantics remain unchanged (still not closable; still not a request workspace).

## Task Description

**Problem:** After closing the current request tab when that tab is the rightmost request
tab (adjacent to trailing `+`), focus can land on `+`. Observed failure class:
`AssertionError` on `assertNotEqual(current, plus_idx)` after `handle_close_tab`. Source:
PYPOST-826; same defect class as PYPOST-824 / PYPOST-825.

**Business need:** Close-current must leave the user in a real request workspace. Landing
on `+` interrupts work. Maintainers need the existing regression test green so this UX
rule stays locked in CI for the close-current path.

### In Scope

- Verify close-current focus rule for `test_handle_close_tab_closes_current`.
- Document that the shared root-cause fix (post-close focus on a request tab) addresses
  this entry point.
- Apply a production change only if verification still fails after the PYPOST-824 fix.

### Out of Scope

- Redesign of plus-tab chrome or new-tab UX.
- New MainWindow e2e / GUI automation beyond existing presenter tests.
- Duplicate reimplementation of the close-path fix already delivered by PYPOST-824 when
  tests already pass.
- Broader tab-bar refactors unrelated to post-close focus.

## Functional Requirements

- After close-current while at least one request tab remains, the active tab must be a
  request tab (not `+`).
- Closing `+` remains a no-op if that path is invoked.
- Closing the last remaining request tab still leaves the user on a blank replacement
  request tab (existing product rule), not on `+`.

## Non-functional Requirements

- **Regression protection:** `test_handle_close_tab_closes_current` continues to run under
  the default quality gate.
- **Minimal change:** Prefer verification and documentation when the shared fix already
  lands; avoid a second production patch for the same root cause.
- **Consistency:** Close-current must obey the same post-close focus rule as closing a
  specific rightmost request tab.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Test exists in `tests/test_tabs_presenter.py` with module
  `pytestmark = pytest.mark.timeout(60)`.
- Production fix for the shared root cause is expected from PYPOST-824
  (`TabsPresenter.close_tab` navigable reselect after `removeTab`).
- `handle_close_tab` calls `close_tab(currentIndex)`; fixing `close_tab` covers this
  ticket’s entry point.
- Approval for step artifacts is treated as granted under sprint-task-runner autonomy.
- Do not call Jira or commit from this autonomous run (orchestrator / parent constraints).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Active tab | Currently focused tab after close-current |
| Close-current action | User closes the active request tab |
| Navigable tabs | Request tabs the user may focus (excludes `+`) |

Interaction overview:

1. User has two or more request tabs plus trailing `+`.
2. User activates a request tab (often the rightmost) and invokes close-current.
3. System removes that tab and selects a remaining request tab.
4. User continues work on a request workspace; `+` is never the active tab.

## Q&A

- Q: Why is this a separate ticket from PYPOST-824?
  A: Same defect, different Jira entry point keyed to
  `test_handle_close_tab_closes_current`. One close-path fix should clear all siblings.
- Q: Why not only re-run the test without documentation?
  A: Top-down workflow requires Steps 1–7 artifacts so the ticket’s verification and
  sibling relationship are recorded for audit and debt coordination.
- Q: May production code change under this ticket?
  A: Only if verification still fails after PYPOST-824’s fix; otherwise document
  “verified fixed by PYPOST-824” and avoid duplicate patches.
- Q: How does this relate to PYPOST-825?
  A: Sibling covering another land-on-plus assertion; same root cause; no duplicate debt
  for the same fix.
