# PYPOST-547: Technical Debt

## Resolved

- Direct `QMessageBox` usage in `env_presenter`, `main_window`, `settings_dialog`,
  `request_save_orchestrator`, and `save_dialog` migrated to `collection_item_dialogs.py`.

## Follow-up Tasks

- Rename `collection_item_dialogs` to a broader module name (e.g. `ui_dialogs`) now that it
  covers save, settings, metrics, and environment flows beyond collection items.

## Non-blockers

- `QMessageBox` remains encapsulated only in `collection_item_dialogs.py` for standard flows;
  custom multi-button dialogs (sibling-tab reload) also live there by design.
