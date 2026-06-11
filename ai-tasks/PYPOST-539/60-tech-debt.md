# PYPOST-539: Technical Debt

## Resolved

- Direct `QMessageBox` usage in `tabs_presenter`, `env_dialog`, and `history_panel` migrated to
  `collection_item_dialogs.py`.

## Follow-up Tasks

- Migrate remaining direct `QMessageBox` callers (e.g. `env_presenter`, `save_dialog`,
  `settings_dialog`, `request_save_orchestrator`) to shared helpers. —
  [PYPOST-547](https://pypost.atlassian.net/browse/PYPOST-547)

## Non-blockers

- Module name `collection_item_dialogs` is broader than its original collection-only scope;
  rename to `ui_dialogs` or similar in a future cleanup task.
