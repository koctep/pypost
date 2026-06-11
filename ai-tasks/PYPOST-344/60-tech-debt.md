# PYPOST-344: Technical Debt

## Resolved

- **Duplicated rename/delete QMessageBox usage** in `CollectionTreeActions` — consolidated into
  `pypost/ui/collection_item_dialogs.py`.

## Follow-up Tasks

- Extend shared QMessageBox helpers to tabs, environments, and history panels (same pattern as
  collection flows). — [PYPOST-539](https://pypost.atlassian.net/browse/PYPOST-539)

## Non-blockers

- Other UI modules still call `QMessageBox` directly; behavior is unchanged and can be migrated
  incrementally.
