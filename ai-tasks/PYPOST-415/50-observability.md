# PYPOST-415: Observability

## Scope

Worker cleanup refactor only. No new log events; existing `stale_worker_cleared` debug log
moved into `_clear_tab_worker` when `reason="stale"`.

## Log Paths

| Event | Level | Location | When |
|-------|-------|----------|------|
| `stale_worker_cleared` | DEBUG | `_clear_tab_worker` | Stale guard fires before new send |

Completion handlers do not log on `_clear_tab_worker` — normal path already covered by
`request_finished` / `request_error` / `request_cancelled` logs.

## Gaps

None introduced. PYPOST-416 remains open for a dedicated log-capture test of the stale path.
