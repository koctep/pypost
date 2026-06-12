# PYPOST-128: Code Cleanup

## Lint / format

- No new linter warnings in `mixins.py` or `request_editor.py`.
- Imports ordered: helper colocated with variable hover mixins (same module family).

## Refactor notes

- Removed duplicated per-child calls in `set_variables` and `set_hidden_keys`.
- `_variable_snapshot_targets` property keeps registration explicit and grep-friendly.

## Line count

Development iteration under 100 LOC (helper + property + test module core).
