# PYPOST-841: Observability

## Assessment

Existing events remain sufficient:

- `agent_session_started` / `agent_session_ready` / `agent_session_ready_timeout`
- `agent_session_shutdown_started` / `agent_session_shutdown_completed`
- Per-step `*_failed` logs inside `shutdown()`

Mid-start cleanup now always reaches the shutdown log pair on failure; no new
metric series required.

## Actions

- [x] Rely on existing lifecycle logs
- [x] Document transactional start cleanup in `agent_lifecycle.md`
