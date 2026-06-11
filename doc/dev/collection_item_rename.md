# Collection Item Rename

## Overview

Collection tree items support a context-menu `Rename` action with inline editing.
Supported item types:
- Collection
- Request inside a collection

The goal is to allow quick in-place renaming directly in the tree.

## Architecture

- **`CollectionTreeActions` (`pypost/ui/presenters/collection_tree_actions.py`)**:
  - Adds `Rename` to the collection tree context menu.
  - Starts inline edit mode via `QTreeView.edit(...)`.
  - Finalizes rename on editor close (commit/cancel), validates non-empty names.
  - Syncs the edited tree row in place after success or cancel.
- **`CollectionsPresenter` (`pypost/ui/presenters/collections_presenter.py`)**:
  - Wires the tree view to `CollectionTreeActions`.
  - Owns tree model build, expand/collapse state, and left-click open.
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

### `CollectionTreeActions.show_context_menu(pos)`

Entry point for right-click actions on collection tree items.

- Builds a `QMenu` with optional **New tab** (requests), `Rename`, and `Delete`.
- On `Rename`, records selection telemetry and starts inline editing.

### `CollectionTreeActions._start_rename(index)` (internal)

Starts inline rename.

- Resolves selected item target (`collection` or `request`).
- For request items, shows editable request name in place.
- Activates `QTreeView.edit(...)`.

### `CollectionTreeActions.on_editor_closed(_editor, hint)`

Finalizes rename on editor close.

- Cancel (`RevertModelCache`): no mutation; `_finish_rename_tree_update` restores the
  canonical label on the edited item without rebuilding the full tree.
- Commit:
  - validates non-empty name,
  - calls `RequestManager.rename_collection_item(...)`,
  - emits `request_renamed` when request name changed,
  - syncs the edited tree item in place via `_finish_rename_tree_update` (falls back to
    `refresh_tree` only when the item cannot be found in the model).

### `CollectionTreeActions._finish_rename_tree_update(item_id, item_type, item=None, *, new_name=None)`

Updates a single tree row after rename completes or is cancelled. When `new_name` is set, the
label and `UserRole` (for requests) reflect the renamed in-memory object. When omitted, the
label is restored from `RequestManager`. Calls `refresh_tree` only if the target item is missing
from the model.

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

- Verify the collections tree view uses `Qt.CustomContextMenu`.
- Verify `customContextMenuRequested` is connected to
  `CollectionTreeActions.show_context_menu` via `CollectionsPresenter`.

### Rename fails with an error dialog

- Check logs for `collection_item_rename_*` messages in `collection_tree_actions`.
- Confirm item has valid `Qt.UserRole` payload (`RequestData` or collection ID).
- Check write permissions for collection storage path.

### Empty names are not accepted

- This is expected behavior by requirement: empty names are rejected.

### Rename metrics are missing

- Confirm metrics server is running.
- Inspect `/metrics` for
  `gui_collection_rename_actions_total{item_type="...",status="..."}` after actions.
