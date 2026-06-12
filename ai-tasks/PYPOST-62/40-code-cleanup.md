# PYPOST-62: Code Cleanup

## Actions

- [x] Added `Dict` import; no unused symbols.
- [x] Index rebuild colocated with `_entries` assignment in `refresh()`.
- [x] Line length within 100 characters.

## Verification

- `make test` targeted module: `tests/test_history_panel.py` passes.
- No new linter issues in touched files.
