# PYPOST-416 — Observability

## Log Under Test

| Event | Level | Emitter | Trigger |
|-------|-------|---------|---------|
| `stale_worker_cleared` | DEBUG | `_clear_tab_worker` | Stale guard in `_handle_send_request` |

## Verification

- [x] `test_stale_worker_cleared_emits_debug_log` captures DEBUG logs via `assertLogs`
- [x] Asserts single `stale_worker_cleared` record with method and URL
- [x] No PII beyond request URL already used in sibling tests
