# PYPOST-941: Observability

## Logging

No new log lines. Existing `ui_action_applied` DEBUG on successful `ui_select`
unchanged.

## Metrics

None — refactor only; no new Prometheus series.

## Tests as signal

- `tests/test_tree_index_walk.py` locks shared walk + error-type boundaries.
- Existing `test_ui_action_applied_caplog` unchanged.
