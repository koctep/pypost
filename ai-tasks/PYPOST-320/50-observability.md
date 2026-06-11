# PYPOST-320: Observability

## Scope

Test-only task. No production logging or metrics changes.

## Existing Coverage (unchanged)

- `save_action_triggered` / `save_as_action_triggered` INFO logs in `RequestWidget`.
- `save_as_flow_*` and `save_request_*` logs in `RequestSaveOrchestrator`.
- `gui_save_actions_total` and `gui_save_as_actions_total` metrics via `MetricsManager`.

## Test Notes

Integration tests use `MagicMock()` for metrics; they do not assert log or metric output.
Orchestrator and presenter unit tests remain the place for metric-behavior checks if added later.

## Checklist

- [x] No new log or metric surface required for this task
- [x] Existing save observability docs in `doc/dev/request_actions.md` remain accurate
