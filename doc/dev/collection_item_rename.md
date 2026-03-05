# Collection Item Rename

## Overview

Collection tree items now support a context-menu `Rename` action with inline editing.
Supported item types:
- Collection
- Request inside a collection

The goal is to allow quick in-place renaming directly in the tree.

## Architecture

- **`MainWindow` (`pypost/ui/main_window.py`)**:
  - Adds `Rename` action to collection tree context menu.
  - Starts inline edit mode in `QTreeView`.
  - Finalizes rename on editor close (commit/cancel), validates non-empty names.
  - Refreshes tree and tabs after successful rename.
- **`RequestManager` (`pypost/core/request_manager.py`)**:
  - Owns rename business logic:
    - `rename_request(request_id, new_name)`
    - `rename_collection(collection_id, new_name)`
    - `rename_collection_item(item_id, item_type, new_name)`
- **`StorageManager` (`pypost/core/storage.py`)**:
  - Persists renamed collections/requests via `save_collection(...)`.
  - For collection rename, old name file is removed and new file is saved.
- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Tracks rename-action outcomes:
    - `gui_collection_rename_actions_total{item_type,status}`

## API / Usage

### `MainWindow.show_collection_item_context_menu(pos)`

Entry point for right-click actions on collection tree items.

- Builds a `QMenu` with `Rename` and `Delete`.
- On `Rename`, records selection telemetry and starts inline editing.

### `MainWindow.start_collection_item_rename(index)`

Starts inline rename.

- Resolves selected item target (`collection` or `request`).
- For request items, shows editable request name in place.
- Activates `QTreeView.edit(...)`.

### `MainWindow.on_collection_item_editor_closed(_editor, hint)`

Finalizes rename on editor close.

- Cancel (`RevertModelCache`): no mutation, tree is reloaded.
- Commit:
  - validates non-empty name,
  - calls `RequestManager.rename_collection_item(...)`,
  - updates request tab titles when request name changed,
  - reloads tree and restores state.

### `RequestManager.rename_collection_item(item_id: str, item_type: str, new_name: str) -> bool`

Type-based rename dispatch.

- `item_type == "request"` -> `rename_request(...)`
- `item_type == "collection"` -> `rename_collection(...)`
- Unsupported type returns `False`

## Configuration

No task-specific settings were added.

Observability relies on existing global metrics server configuration:
- `settings.metrics_host`
- `settings.metrics_port`

## Troubleshooting

### Right-click does not show `Rename`

- Verify `collections_view` uses `Qt.CustomContextMenu`.
- Verify `customContextMenuRequested` is connected to
  `show_collection_item_context_menu`.

### Rename fails with an error dialog

- Check logs for `collection_item_rename_*` messages in `MainWindow`.
- Confirm item has valid `Qt.UserRole` payload (`RequestData` or collection ID).
- Check write permissions for collection storage path.

### Empty names are not accepted

- This is expected behavior by requirement: empty names are rejected.

### Rename metrics are missing

- Confirm metrics server is running.
- Inspect `/metrics` for
  `gui_collection_rename_actions_total{item_type="...",status="..."}` after actions.
