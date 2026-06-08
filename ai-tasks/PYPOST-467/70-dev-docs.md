# PYPOST-467: Dev Documentation

## Changes Made

### New: `doc/dev/environment_variable_delete.md`

- Overview of context-menu variable delete in Manage Environments.
- Architecture: `EnvironmentDialog` handlers, model mutation, reload, logging.
- API / usage: user flow, `_on_vars_table_context_menu`, `_delete_variable_at_row`,
  alternate clear-name path.
- Configuration: `env_variable_deleted` log and `log_hidden_key_names` policy.
- Troubleshooting and related tests.
- Cross-links to hidden variables, encryption, and PYPOST-493 follow-up.

### Updated: `doc/dev/README.md`

- Added index entry for **Environment Variable Delete**.

### Updated: `doc/dev/hidden_variables.md`

- Noted PYPOST-467 delete action on `EnvironmentDialog` in Architecture.
- Added cross-link to `environment_variable_delete.md`.

## Validation

- [x] Documented handlers match `pypost/ui/dialogs/env_dialog.py`
- [x] Test names align with `tests/test_env_dialog.py`
- [x] Log format matches `ai-tasks/PYPOST-467/50-observability.md`
- [x] Follow-up linked: [PYPOST-493](https://pypost.atlassian.net/browse/PYPOST-493)
- [x] `doc/dev/README.md` index updated
