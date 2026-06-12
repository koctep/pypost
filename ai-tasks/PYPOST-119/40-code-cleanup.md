# PYPOST-119: Code Cleanup

## Lint and format

- No new linter warnings in `pypost/ui/widgets/mixins.py` or `tests/test_variable_hover.py`.
- `make test` passes for variable hover tests.

## Review notes

- Cache helpers mirror naming from `VariableAwareTableWidget` (`_clear_hover_*`, `_resolve_*`).
- `_show_or_hide_tooltip` keeps optional `resolved` for backward-compatible direct calls.

## No further cleanup required
