# PYPOST-449 — Developer Documentation

## Summary

Updated `doc/dev/environments_dialog.md` with a row-update helper table for
`EnvironmentVariablesWidget`.

## Changes

- Documented `_is_edited_cell`, `_revert_invalid_variable_key`,
  `_resolve_hidden_value_on_edit`, and `_refresh_value_cell_for_hidden_toggle`.
- Linked new `tests/test_environment_variables_widget.py` in the Testing section.

## Related

- [PYPOST-437](https://pypost.atlassian.net/browse/PYPOST-437) — hidden variables; original
  value-item helpers
- [PYPOST-496](https://pypost.atlassian.net/browse/PYPOST-496) — widget extraction from
  `EnvironmentDialog`
