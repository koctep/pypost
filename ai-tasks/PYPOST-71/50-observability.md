# PYPOST-71 — Observability

## Impact

No observability changes. Existing logs in `_handle_send_request` unchanged:

| Event | Level | When |
|-------|-------|------|
| `request_send_initiated` | INFO | New worker dispatch |
| `request_stop_requested` | INFO | Stop while worker running |
| `stale_worker_cleared` | DEBUG | Stale guard via `_clear_tab_worker` |

## Verification

- [x] No log message text changed
- [x] `test_stale_worker_cleared_emits_debug_log` still passes via signal path
