# PYPOST-365: Observability

## Production Code

No changes to logging or Prometheus metrics in application code.

## Tests

- `test_metrics_tracked_on_typed_search` asserts `MetricsManager.track_gui_response_search_action`
  is invoked with `source="typed"` and `has_matches=True` when matches exist.
- Complements existing unit coverage in `tests/test_metrics_manager.py` for search metric labels.

## Logging

ResponseView search already logs at DEBUG (`response_search_typed`, `response_search_find`). Tests
do not assert log output; behavior is covered via UI labels and metrics mock.
