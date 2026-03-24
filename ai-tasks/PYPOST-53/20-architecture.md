# PYPOST-53: Architecture — environment Copy (duplicate)

## Scope

Manage Environments dialog only: `EnvironmentDialog` in `pypost/ui/dialogs/env_dialog.py`.

## UI

- `env_list` (`QListWidget`): set `contextMenuPolicy` to `Qt.ContextMenuPolicy.CustomContextMenu`.
- Connect `customContextMenuRequested` to a handler that:
  - Maps position to a list row via `itemAt(pos)`; if none, return.
  - Builds `QMenu` with action **Copy**.
  - On **Copy**, runs duplicate flow for that row (not only `currentRow()`).

## Duplicate logic

- **Pure helper** (unit-tested): `clone_environment(source: Environment, new_name: str) -> Environment` in new module `pypost/core/environment_ops.py`.
  - New `Environment` with `name=new_name.strip()`, `variables=dict(source.variables)`,
    `enable_mcp=source.enable_mcp`; new `id` comes from model default factory.
- **Dialog orchestration** in `EnvironmentDialog`:
  - `QInputDialog.getText` title e.g. “Copy Environment”, label “Name:”, default text
    `Copy of {source.name}`.
  - Loop until valid: non-empty name, and name not equal to any existing
    `env.name` in `self.environments`. On conflict or empty after trim, `QMessageBox.warning`
    and re-show input with last entered value as default.
  - Insert new env at `source_index + 1`, call existing `load_list()`, then
    `setCurrentRow(source_index + 1)` so selection lands on the duplicate.
  - Call `on_env_selected` path implicitly via `setCurrentRow` + signal.

## Edge cases

- Context menu on blank area of list: no menu or empty: no-op (no item).
- Cancel on input dialog: no change to `self.environments`.

## Observability

- `logging.getLogger(__name__).info` when a duplicate is created (source name, new name).

## Testing

- `tests/test_environment_ops.py`: `unittest` tests for `clone_environment` (new id,
  copied variables/MCP flag, name set, variables decoupled from source dict mutation).
