# Collection Export

## Overview

**Export Collection** (PYPOST-989) writes one sidebar collection — with all of its
requests — to a JSON file the user chooses. The format is PyPost's native collection
serialization: one JSON object, the same shape as `{data_dir}/collections/{id}.json` and
as accepted by [Collection Import](collection_import.md) (PYPOST-987).

It mirrors [Export environments](environments_dialog.md) (PYPOST-988) structurally: a
Qt-free core for payload shaping and file writing, and a thin Qt shell for the save dialog
and result feedback. Collections export one tree target at a time (no scope dialog).

Two UI entry points share the same orchestration (PYPOST-1013):

- **Below-tree button** — exports from the tree's `currentIndex()`.
- **Context menu** — **Export Collection…** on collection or request rows; exports from
  the **clicked** index (not a distant prior selection).

## Architecture

```text
CollectionsPresenter.panel          Export Collection… button (COLLECTION_EXPORT_BUTTON)
CollectionTreeActions context menu  Export Collection… on collection/request rows
        │
        ▼  delegates (button: currentIndex; menu: clicked index)
CollectionExportActions             selection → save dialog → write → result
        │
        ├─ collection_item_dialogs  QFileDialog.getSaveFileName + QMessageBox helpers
        └─ collection_export        pure: resolve target, payload, write, summary
```

- **`pypost/core/collection_export.py`** — pure core. Resolves the export target from a
  collection id, builds the JSON payload via `Collection.model_dump(mode="json")`, writes
  the file, and formats the success summary. No Qt, no storage.
- **`pypost/core/collection_messages.py`** — export dialog titles, button label
  (`BUTTON_EXPORT_COLLECTION`), file filter, and the no-selection message (import strings
  live in the same module).
- **`pypost/ui/presenters/collection_export_actions.py`** — `CollectionExportActions`.
  Maps a tree index to a collection id (collection row or parent of a request row), runs
  the save dialog, writes through the core, and shows success or error. The below-tree
  button uses `currentIndex()`; the context menu passes the clicked index.
- **`pypost/ui/presenters/collection_tree_actions.py`** — adds **Export Collection…** to
  collection and request row menus (PYPOST-1013); logs `collection_export_selected`, then
  calls the injected export callback with the clicked index. See
  [Collection Tree Actions](collection_tree_actions.md).
- **`pypost/ui/collection_item_dialogs.py`** — `prompt_export_collection_file`,
  `show_collection_export_no_selection_error`, `show_collection_export_result`,
  `show_collection_export_error`.
- **`pypost/ui/presenters/collections_presenter.py`** — adds **Export Collection…** next
  to Import in the panel action row; wires `export_collection` (button, no index) and
  `_export_collection_at_index` (menu) to the same `CollectionExportActions` path.
  Optional constructor injection `serialize_collection` for tests (defaults to
  `build_export_payload`).

### Round-trip with import

Export produces a single JSON object. Import (`load_collection_import_candidates`) accepts
that shape directly. Automated tests in `tests/test_collection_export.py` assert export →
import field fidelity for method, URL, headers, params, body, scripts, and MCP flags.

### Selection rules

Both entry points resolve a model index the same way (`_selected_collection_id`):

| Resolved tree index | Exported collection |
| --- | --- |
| Collection row | That collection |
| Request row | Parent collection |
| Invalid / none | Error: select a collection first |

| Entry point | Index source |
| --- | --- |
| Below-tree **Export Collection…** | `tree.currentIndex()` |
| Context-menu **Export Collection…** | Clicked `indexAt(pos)` via optional `source_index` |

Unlike environment export, there is no Hidden-secrets confirmation — collections do not
store encrypted environment variables.

## API / Usage

### `CollectionExportActions.export_collection(source_index=None)`

Runs one export interaction end to end.

- **`source_index`**: Optional `QModelIndex`. When omitted, uses `tree.currentIndex()`
  (button). Context-menu callers pass the clicked index.
- Resolves collection id → `collection_for_export` → save dialog → serialize/write →
  success or error dialog.
- **Returns**: `None` (side effects only).

### `CollectionsPresenter.export_collection()`

Panel-button entry: delegates to `CollectionExportActions.export_collection()` with no
index.

### `CollectionsPresenter._export_collection_at_index(source_index)`

Menu entry: delegates with `source_index=` so the clicked row wins over selection.

### Core helpers (`pypost.core.collection_export`)

| Function | Role |
| --- | --- |
| `collection_for_export(collections, selected_collection_id)` | Pick target or `None` |
| `build_export_payload(collection)` | JSON-ready `dict` via `model_dump` |
| `suggested_export_filename(collection)` | Default save-dialog name |
| `write_export_file(path, payload)` | Atomic-style write; raises `CollectionExportError` |
| `format_export_result(result)` | Success dialog body |

## Configuration

No task-specific settings or environment variables. Dialog copy and the button/menu label
come from `pypost.core.collection_messages` (`BUTTON_EXPORT_COLLECTION`, titles, filters).

## Widget identity

| Widget | `objectName` | In `KEY_WIDGET_IDS` |
| --- | --- | --- |
| Export button | `pypost_collection_export_button` | No (same as import button) |

## Logging

| Event | Level | When |
| --- | --- | --- |
| `collection_export_selected` | INFO | Menu only (`item_type`, `item_id`) |
| `collection_export_no_selection` | WARNING | No exportable collection for index |
| `collection_export_failed` | WARNING | Serialize/write error (`reason`) |
| `collection_export_completed` | INFO | Success (`collection_name`, count, `path`) |

Button path emits only the shared outcome events (no `collection_export_selected`). Catalog
entry: [Logging](logging.md#collections-and-persistence).

## Tests

| Module | Coverage |
| --- | --- |
| `tests/test_collection_export.py` | Pure core: target, filename, payload, write, round-trip |
| `tests/test_collection_export_ui.py` | Button path: wiring, happy/cancel/error, request→parent |
| `tests/test_collection_tree_actions.py` | Menu labels, clicked-index dispatch, selection log |

Run:

```bash
make test PYTEST_ARGS="tests/test_collection_export.py \
  tests/test_collection_export_ui.py tests/test_collection_tree_actions.py"
```

Rename/delete suites that mock the context menu use `action_count=3` (collection) or
`4` (request) so the Export action occupies a stable slot — see
[Collection Tree Actions](collection_tree_actions.md#automated-tests).

## Troubleshooting

**Menu exports the wrong collection**

Clicked index was not passed through. Menu must call `_export_collection_at_index` /
`export_collection(source_index=…)`. The button correctly uses `currentIndex()`.

**"Select a collection first" with a row highlighted**

Invalid index or blank click. Ensure the click resolved a collection or request
`UserRole`; an empty tree has nothing to export.

**Context menu missing Export**

`export_collection` callback not injected. Production `CollectionsPresenter` always
injects it; isolated harnesses may pass `None` and omit the action.

**Import rejects an exported file**

Wrong shape or truncated write. Export is one JSON object; compare with
`collections/<id>.json` and check `collection_export_failed` logs.


## Related docs

- User guide: [Collections — Export a collection](../user/collections.md#export-a-collection)
- Tree menu wiring: [Collection Tree Actions](collection_tree_actions.md)
- Import counterpart: [Collection Import](collection_import.md)
- On-disk format: [Collection Storage](collection_storage.md)
- Log catalog: [Logging](logging.md)
