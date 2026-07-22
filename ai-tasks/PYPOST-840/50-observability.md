# PYPOST-840: Observability

## Assessment

No new metrics or structured log fields are required. The canonical helper
already emits `ui_wait_settled` / timeout diagnostics from PYPOST-837.

## Actions

- [x] Reuse existing `pypost.agent.ui_wait` debug logs — no new events
- [x] Lock tests are silent on success (assert-only)
- [x] Document that observability remains owned by `ui_wait.md`
