# PYPOST-55: Architecture

## Constants module

New module: `pypost/core/environment_messages.py`

- String constants for titles, labels, menu actions, table columns, MCP checkbox text.
- Message templates with small `format_*` helpers for `{name}` interpolation.
- Shared by UI widgets, `collection_item_dialogs` environment helpers, and
  `environment_ops.validate_environment_rename`.

## Call sites updated

| Component | Strings moved |
| --- | --- |
| `env_dialog.py` | Window title |
| `environment_list_widget.py` | Add button, new/copy dialogs, context menu actions, default copy name |
| `environment_variables_widget.py` | Table headers, MCP label, variable context menu |
| `collection_item_dialogs.py` | Delete confirm, copy validation QMessageBox titles/bodies |
| `environment_ops.py` | Rename validation error messages |

## Testing

- `tests/test_environment_messages.py` — format helper unit tests.
- Existing `tests/test_env_dialog.py` — regression for dialog behavior.

## Observability

No new log events. Log message keys remain English identifiers (unchanged).
