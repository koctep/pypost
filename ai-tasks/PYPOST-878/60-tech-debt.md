# PYPOST-878: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

`gateway_timeout_detail` now forwards env worker `_operation` as
`worker_operation` when it is a string; collection-style workers without the
attribute omit the field. DoD met with focused diagnostics coverage. Items
below are non-blocking. **Do not create Jira tickets in this step** — list
unticketed follow-ups for the orchestrator.

## Shortcuts Taken

- **Private `_operation` via `getattr`.** Same duck-typed private-read pattern
  as `_worker` / `isRunning()` from PYPOST-828; avoided a public env-worker
  accessor for a harness-only field.
- **`isinstance(..., str)` guard.** Non-string `_operation` values are omitted
  rather than coerced; env workers already use Literal["load","save"] strings.
- **No real-gateway forced-timeout CI assert.** Fake-worker unit coverage is
  sufficient for this wiring; forcing a live hung gateway solely to assert
  message text would be flaky and out of scope.
- **Full `make check` not re-run.** Validated with focused diagnostics tests +
  `make lint` (same scoped gate pattern as sibling harness tickets). Full check
  remains tracked under [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880).

## Code Quality Issues

- None that block close. Optional future: public `operation` property on env
  worker if other consumers need it (Lowest; not required for DoD).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Env-style `_operation` appears in `gateway_timeout_detail` | Covered |
| Collection-style omit `worker_operation=` | Covered |
| Formatter omit-None / include when set | Covered (PYPOST-828) |
| Forced real-gateway timeout with `worker_operation` in CI text | Not covered — optional; NON-BLOCKER |
| Full `make check` after this story | Not re-run — see PYPOST-880 |

Timeout markers: module `pytestmark` on diagnostics file. **No timeout-marker
blockers.**

## Performance Concerns

None. Field is read only inside the lazy timeout detail callable.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Lowest | Optional public `operation` on env worker | Only if a second consumer needs it beyond harness `getattr` | — (do not ticket unless demand appears) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Optional shared `worker_timeout_detail` helper | [PYPOST-879](https://pypost.atlassian.net/browse/PYPOST-879) |
| Full `make check` when sibling noise is clear | [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880) |

## User documentation

N/A — harness-only change; no `doc/user/` updates.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: env load/save appears in gateway timeout detail when present;
  collection omits; busy/pending/worker_running unchanged.
- No missing pytest timeout markers.
- No BLOCKER debt. TD-1 is Lowest and intentionally not ticketed until needed.
- Unticketed follow-ups needing Jira: **none**.
