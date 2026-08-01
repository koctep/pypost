# PYPOST-988: Export environments

## Research

Mirrors PYPOST-986 import architecture in reverse:

- Reuse `EnvironmentVariablesAdapter.serialize_environment` via new
  `StorageManager.serialize_environment_records`.
- First file-picker save dialog in the app (`QFileDialog.getSaveFileName`).
- Import precedent: `environment_import.py`, `EnvironmentListWidget.import_environments`.

## Implementation Plan

1. **`pypost/core/environment_export.py`** — pure module:
   `ExportScope`, `ExportPlanResult`, `environments_for_export`,
   `export_includes_hidden`, `build_export_payload`, `write_export_file`,
   `format_export_result`, `suggested_export_filename`.
2. **`StorageInterface` / `StorageManager`** — `serialize_environment_records`.
3. **Dialogs** in `collection_item_dialogs.py`:
   `prompt_export_scope`, `confirm_export_includes_secrets`,
   `prompt_export_environments_file`, `show_export_result`, `show_export_error`,
   `show_export_no_selection_error`.
4. **`EnvironmentListWidget.export_environments()`** — inject
   `serialize_export_records` callable from presenter.
5. **`ENV_EXPORT_BUTTON`** in `widget_ids.py`.

## Hidden policy

Include native serialized values; `confirm_export_includes_secrets` before write when
`hidden_keys` non-empty. Document in user docs.

## Failing repro (Step 3)

`tests/test_environment_export.py` importing `pypost.core.environment_export` before
module exists → `ModuleNotFoundError`.

## Worklog

tokens_used: 12000
role: execution
step: 2
step_name: Architecture
