# PYPOST-171: Dev Docs

## Updated

- `doc/dev/mcp_integration.md` — metrics server lifecycle threading and `server_lock` constraints

## Notes

Closes PYPOST-23 item "Locking." Complements PYPOST-49/75 (registry/server split) and
PYPOST-153 (startup signaling). Locks guard uvicorn thread lifecycle only; metric counters
remain lock-free via `MetricsRegistry`.
