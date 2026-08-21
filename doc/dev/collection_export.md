# Collection Export

## Overview

**Export Collection** (PYPOST-989) writes one sidebar collection — with all of its
requests — to a JSON file the user chooses. **Export All Collections…** (PYPOST-1012)
writes a snapshot of the complete collection library. Both use PyPost's native collection
serialization and the [shared JSON root policy](json_export_root.md): one record is a JSON object,
while zero or multiple records are an array accepted by [Collection Import](collection_import.md)
(PYPOST-987).

It mirrors [Export environments](environments_dialog.md) (PYPOST-988) structurally: a
Qt-free core for payload shaping and file writing, and a thin Qt shell for the save dialog
and result feedback. The bulk action is selection-independent and deliberately retains the
same injected per-collection serializer used by single export.

Two UI entry points share the same orchestration (PYPOST-1013):

- **Below-tree button** — exports from the tree's `currentIndex()`.
- **Context menu** — **Export Collection…** on collection or request rows; exports from
  the **clicked** index (not a distant prior selection).

## Architecture

```text
CollectionsPresenter.panel          Export Collection… button (COLLECTION_EXPORT_BUTTON)
                                    Export All Collections… (COLLECTION_EXPORT_ALL_BUTTON)
CollectionTreeActions context menu  Export Collection… on collection/request rows
        │
        ▼  delegates (single button: currentIndex; menu: clicked index; all: no index)
CollectionExportActions             selection/snapshot → save dialog → write → result
        │
        ├─ collection_item_dialogs  QFileDialog.getSaveFileName + QMessageBox helpers
        └─ collection_export        pure: resolve target, object/list payload, write, summary
```

- **`pypost/core/collection_export.py`** — pure core. Resolves the single-export target,
  builds JSON-ready object or ordered list payloads via `Collection.model_dump(mode="json")`,
  and formats the typed success summaries. Writing delegates to the shared
  `export_file_writer.write_json_export_file` helper. No Qt or storage dependency.
- **`pypost/core/export_file_writer.py`** — shared low-level write helper (PYPOST-1011):
  `write_json_export_file(path, payload, *, error_cls)` creates `path`'s parent
  directories, writes `json.dumps(payload, indent=2)` with a trailing newline via
  `write_text`, and wraps any `(OSError, TypeError, ValueError)` into the caller-supplied
  `error_cls`. Used by both collection and environment export so the write/serialize-error
  behavior stays identical; no Qt dependency, no cross-domain import.
- **`pypost/core/collection_messages.py`** — export dialog titles, button label
  (`BUTTON_EXPORT_COLLECTION` / `BUTTON_EXPORT_ALL_COLLECTIONS`), captions, suggested
  filenames, file filter, and the no-selection message (import strings live in the same
  module).
- **`pypost/ui/presenters/collection_export_actions.py`** — `CollectionExportActions`.
  Maps a tree index to a collection id (collection row or parent of a request row), runs
  the save dialog, writes through the core, and shows success or error. The below-tree
  button uses `currentIndex()`; the context menu passes the clicked index. Bulk export
  snapshots `RequestManager.get_collections()` once, prompts even for an empty snapshot,
  applies the injected serializer to each collection in order, passes the resulting records through
  `json_root_for_records`, and writes one JSON document.
- **`pypost/ui/presenters/collection_tree_actions.py`** — adds **Export Collection…** to
  collection and request row menus (PYPOST-1013); logs `collection_export_selected`, then
  calls the injected export callback with the clicked index. See
  [Collection Tree Actions](collection_tree_actions.md).
- **`pypost/ui/collection_item_dialogs.py`** — single and bulk save prompts plus their
  selection/error/result helpers. `prompt_export_all_collections_file` uses
  `collections.json` and the shared JSON file filter.
- **`pypost/ui/presenters/collections_presenter.py`** — adds both export buttons next to
  Import in the panel action row; wires `export_collection` (accepts optional `source_index`
  and forwards to `CollectionExportActions.export_collection(source_index=source_index)`),
  `_export_collection_at_index` (menu), and `export_all_collections` (no selection) to
  `CollectionExportActions`.
  Optional constructor injection `serialize_collection` for tests (defaults to
  `build_export_payload`).

### Round-trip with import

Single export produces a JSON object. Bulk export produces an object for one collection and an
array for zero or multiple collections, including `[]` for an empty library. Import
(`load_collection_import_candidates`) accepts either shape.
Automated tests in `tests/test_collection_export.py` assert export → import field fidelity
for multiple collections, including method, URL, headers, params, body, scripts, and MCP
flags.

### Selection rules

Both entry points resolve a model index the same way (`_selected_collection_id`):

| Resolved tree index | Node data role (`Qt.ItemDataRole.UserRole`) | Exported collection |
| --- | --- | --- |
| Collection row | `str` (collection id) | That collection |
| Request row | `RequestData` | Parent collection (resolved via `item.parent()`) |
| Invalid / none | `None` or missing | Error: select a collection first |

When `source_index` is explicitly provided, it takes precedence over `tree.currentIndex()`. When `source_index` is omitted or `None`, the action falls back to `tree.currentIndex()`:

| Entry point | Index source | Precedence |
| --- | --- | --- |
| Below-tree **Export Collection…** | Panel button | Uses `tree.currentIndex()` (no `source_index` passed) |
| Context-menu **Export Collection…** | Clicked row `indexAt(pos)` | Passes `source_index=clicked_index` (overrides `currentIndex()`) |

Unlike environment export, there is no Hidden-secrets confirmation — collections do not
store encrypted environment variables.

## API / Usage

### `CollectionExportActions.export_collection(source_index=None)`

Runs one export interaction end to end.

- **`source_index`**: Optional `QModelIndex`. When provided, takes precedence over
  `tree.currentIndex()`. When omitted/`None`, uses `tree.currentIndex()` (panel button).
- Resolves collection id via `_selected_collection_id`:
  - If the item's `Qt.ItemDataRole.UserRole` is a `str`, it is the target collection id.
  - If the item's `Qt.ItemDataRole.UserRole` is `RequestData`, resolves to the `str` id on `item.parent()`.
  - Otherwise returns `None`.
- Resolves collection id → `collection_for_export` → save dialog → serialize/write →
  success or error dialog.
- **Returns**: `None` (side effects only).

### `CollectionsPresenter.export_collection(source_index=None)`

Public export entry point on the presenter. Accepts optional `source_index: QModelIndex | None = None`.
- Delegates directly to `CollectionExportActions.export_collection(source_index=source_index)`.
- When `source_index` is provided, takes precedence over `tree.currentIndex()`, exporting the target collection (or parent collection for a child request node) even if `currentIndex()` points to a distant row.
- When called with no arguments (e.g. from the below-tree action button), defaults to `source_index=None` and uses `tree.currentIndex()`.

### `CollectionExportActions.export_all_collections()`

Runs the complete-backup interaction with no tree-selection input.

1. Takes one ordered snapshot from `RequestManager.get_collections()`.
2. Opens `prompt_export_all_collections_file`; cancellation returns before serialization or
   writing.
3. Serializes every snapshot entry through the injected `serialize_collection` callable, applies
   `json_root_for_records` to the complete record list, writes the resulting JSON document, then
   displays `CollectionsExportResult` with counts and path.
4. Catches serialization/write `CollectionExportError`, `TypeError`, and `ValueError`, logs
   `collections_export_failed`, and displays the all-export error dialog.

### `CollectionsPresenter.export_all_collections()`

Panel-button entry: delegates to `CollectionExportActions.export_all_collections()` and does
not inspect the tree's current index.

### `CollectionsPresenter._export_collection_at_index(source_index)`

Menu entry: delegates with `source_index=` so the clicked row wins over selection.

### Core helpers (`pypost.core.collection_export`)

| Function | Role |
| --- | --- |
| `collection_for_export(collections, selected_collection_id)` | Pick target or `None` |
| `build_export_payload(collection)` | JSON-ready `dict` via `model_dump` |
| `build_all_export_payload(collections)` | Ordered `list[dict]` using the native collection shape |
| `suggested_export_filename(collection)` | Default save-dialog name |
| `write_export_file(path, payload)` | Delegates to `export_file_writer.write_json_export_file(path, payload, error_cls=CollectionExportError)` — writes an object or list as indented UTF-8 JSON |
| `format_export_result(result)` | Success dialog body |
| `CollectionsExportResult` / `format_all_export_result(result)` | Typed bulk outcome and success-dialog body |

## Configuration

No task-specific settings or environment variables. Dialog copy, the default
`collections.json` filename, and button labels come from `pypost.core.collection_messages`.
Bulk export uses the existing JSON filter and does not change collection import, storage, or
conflict settings.

## Widget identity

| Widget | `objectName` | In `KEY_WIDGET_IDS` |
| --- | --- | --- |
| Export button | `pypost_collection_export_button` | No (same as import button) |
| Export all button | `pypost_collection_export_all_button` | No (same as import button) |

## Logging

| Event | Level | When |
| --- | --- | --- |
| `collection_export_selected` | INFO | Menu only (`item_type`, `item_id`) |
| `collection_export_no_selection` | WARNING | No exportable collection for index |
| `collection_export_failed` | WARNING | Serialize/write error (`reason`) |
| `collection_export_completed` | INFO | Success (`collection_name`, count, `path`) |
| `collections_export_payload_built` | INFO | Bulk core payload built (`collection_count`) |
| `collections_export_cancelled` | INFO | Bulk save dialog cancelled |
| `collections_export_failed` | WARNING | Bulk serialize/write error (`reason`) |
| `collections_export_completed` | INFO | Bulk success (`collection_count`, `request_count`, `path`) |

Button path emits only the shared outcome events (no `collection_export_selected`). Catalog
entry: [Logging](logging.md#collections-and-persistence).

## Tests
 
| Module | Coverage |
| --- | --- |
| `tests/test_collection_export.py` | Pure core: target, filename, object/list payload, write, round-trip |
| `tests/test_collection_export_ui.py` | Single/bulk button wiring, success, empty backup, cancel/error, completion log, `source_index` overriding distant `currentIndex` (`TestExportCollectionSourcePrecedence`) |
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

Wrong shape or truncated write. A one-record export is one JSON object; zero or multiple records
are one JSON array. Compare a single entry with `collections/<id>.json` and check
`collection_export_failed` or `collections_export_failed` logs.

**Bulk backup is unexpectedly empty**

The action intentionally exports the snapshot returned by `RequestManager.get_collections()`
at the time the user chooses the action. Confirm the expected collections are visible before
opening the save dialog. An empty library successfully writes `[]` rather than showing an
error.

**Bulk backup does not restore all collections**

For one collection, verify the file root is a JSON object; for zero or multiple collections,
verify it is a JSON array. Then use **Import Collection…**. Import's existing name-conflict policy
can overwrite, keep both, or skip individual entries; bulk export does not alter that policy.
Check `collections_export_failed` if the backup was not written.


## Related docs

- User guide: [Collections — Export a collection](../user/collections.md#export-a-collection)
- User guide: [Collections — Export all collections](../user/collections.md#export-all-collections)
- Tree menu wiring: [Collection Tree Actions](collection_tree_actions.md)
- Import counterpart: [Collection Import](collection_import.md)
- Root policy: [Shared JSON Export Root Policy](json_export_root.md)
- On-disk format: [Collection Storage](collection_storage.md)
- Log catalog: [Logging](logging.md)
