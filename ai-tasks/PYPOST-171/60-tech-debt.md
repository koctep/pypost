# PYPOST-171: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — locking in `MetricsServer` is appropriate for current callers;
risk remains low as assessed in PYPOST-23.

## Shortcuts Taken

None — verification-only task.

## Resolved Debt

| Source | Item | Resolution |
| --- | --- | --- |
| PYPOST-23 | `MetricsManager` locks during server start/stop | Reviewed in PYPOST-171; lock lives in `MetricsServer.server_lock`; main-thread-only callers |

## Known Limitations

| Item | Severity | Follow-up |
| --- | --- | --- |
| `start_server` may call `stop_server` while holding non-reentrant `Lock` | Low | Dead path in production; use `restart_server` or `RLock` if concurrent start is ever needed |
| `restart_server` not atomic across stop+start | Low | Acceptable while only Qt main thread restarts metrics |

## Follow-up Tasks

None — no new Jira tickets required.
