# PYPOST-989: Export collection

## Research

Mirrors PYPOST-988 (export environments) and PYPOST-987 (import collections) in reverse:

- On disk each collection is one JSON file (`collection.model_dump_json(indent=2)` in
  `StorageManager.save_collection`).
- Import accepts a single top-level object or a list (`collection_import.py`).
- UI precedent: Import button row on `CollectionsPresenter.panel`; environment export uses
  `QFileDialog.getSaveFileName` and injected serialize callable for tests.

## Implementation Plan

1. **`pypost/core/collection_export.py`** — pure module:
   `CollectionExportResult`, `collection_for_export`, `build_export_payload`,
   `suggested_export_filename`, `write_export_file`, `format_export_result`.
2. **`pypost/core/collection_messages.py`** — export strings (button, dialog titles,
   no-selection message).
3. **`pypost/ui/collection_item_dialogs.py`** — save dialog and result/error boxes.
4. **`pypost/ui/presenters/collection_export_actions.py`** — tree selection → save →
   write → result (mirrors `CollectionImportActions`).
5. **`CollectionsPresenter`** — **Export Collection…** button, `export_collection()`,
   optional `serialize_collection` injection.
6. **`COLLECTION_EXPORT_BUTTON`** in `widget_ids.py` (not in `KEY_WIDGET_IDS`).
7. **Tests:** `tests/test_collection_export.py`, `tests/test_collection_export_ui.py`.
8. **Docs:** `doc/user/collections.md`, `doc/dev/collection_export.md`.

## Failing repro (Step 3)

`tests/test_collection_export.py` importing `pypost.core.collection_export` before the
module exists → `ModuleNotFoundError`.

## Worklog

tokens_used: 10000
role: execution
step: 2
step_name: Architecture
