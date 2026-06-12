# PYPOST-72 — Observability

## Impact

No observability changes. Existing save orchestrator logs unchanged:

| Event | Level | When |
|-------|-------|------|
| `save_request_new_succeeded` | INFO | New save via dialog |
| `save_as_flow_completed` | INFO | Save-as success |

## Verification

- [x] No log message text changed
- [x] No new metrics required for this bug fix
