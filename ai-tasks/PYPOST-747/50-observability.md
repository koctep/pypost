# PYPOST-747 — Observability

## Impact

**Documentation only.** No new log lines, metrics, or alert behavior.

## Deliverable

`doc/dev/logging.md` documents:

- Preferred `event_name key=value` message shape
- Domain-grouped catalog of existing events
- Legacy migration patterns for `http_client`, composition-root injectors, server lifecycle
- CI allowlist note for ERROR prefix changes
- Sensitive field guidance (cross-ref security audit)

## Verification

`make check` — no test changes; docs do not affect runtime observability.
