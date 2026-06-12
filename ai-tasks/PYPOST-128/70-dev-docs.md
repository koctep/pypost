# PYPOST-128: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/variable_propagation.md` | Composite fan-out via `_variable_snapshot_targets` and `push_snapshot_to_widgets` |

## Summary

Documented how `RequestWidget` registers variable-aware children and reuses one helper
for both variable and hidden-key snapshots. Presenter boundary unchanged from
PYPOST-116.

## Cross-links

- `doc/dev/ui_mixins.md` — `VariableHoverMixin.set_variables`
- `tests/test_request_editor_variable_propagation.py` — composite fan-out contract
