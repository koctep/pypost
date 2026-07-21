# PYPOST-820: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

None. Single presenter regression test; production behavior already matched acceptance.

## Code Quality Issues

None introduced. `close_tab` still relies on Qt `removeTab` current-index selection rather
than an explicit "select first navigable request tab" step. That is acceptable today and
covered by PYPOST-818 and this middle-close test; an explicit reselect would be a hardening
option, not a blocker.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Close first of two → focus remaining request, not `+` | Covered (PYPOST-818) |
| Close middle of three → focus remaining request, not `+` | Covered (this task) |
| Close last remaining request tab → blank tab ensured | Covered (PYPOST-819) |
| Close plus tab ignored | Already covered |
| Close last of many while focused elsewhere | Optional edge case; not required by acceptance |

## Performance Concerns

None.

## Follow-up Tasks

None. Optional hardening (explicit post-close `setCurrentIndex` to a navigable request tab)
deferred unless a future Qt/platform change breaks the regression tests.

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; test passes under `make test`; no production
regressions.
