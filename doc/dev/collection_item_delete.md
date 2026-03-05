# Collection Item Delete

## Overview

Collection tree items now support a context-menu `Delete` action with confirmation.
Supported item types:
- Collection
- Request inside a collection

The goal is to allow direct cleanup from the tree without extra navigation.

## Architecture

- **`MainWindow` (`pypost/ui/main_window.py`)**:
  - Enables custom context menu on `collections_view`.
  - Resolves clicked item type (`collection` or `request`).
  - Prompts user confirmation and handles success/error UI flow.
- **`RequestManager` (`pypost/core/request_manager.py`)**:
  - Owns deletion business logic:
    - `delete_request(request_id)`
    - `delete_collection(collection_id)`
    - `delete_collection_item(item_id, item_type)`
- **`StorageManager` (`pypost/core/storage.py`)**:
  - Persists collection changes and can remove collection files:
    - `delete_collection(collection_name)`
- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Tracks delete-action outcomes:
    - `gui_collection_delete_actions_total{item_type,status}`

## API / Usage

### `MainWindow.show_collection_item_context_menu(pos)`

Entry point for right-click actions on collection tree items.

- Builds a `QMenu` with `Delete`.
- Emits telemetry for selected/cancelled/succeeded/not-found/error outcomes.
- Delegates deletion to `handle_delete_collection_item(...)`.

### `MainWindow.confirm_delete(item_label: str) -> bool`

Shows a confirmation dialog before destructive action.

- Returns `True` only when user confirms.

### `MainWindow.handle_delete_collection_item(item_id, item_type, item_label)`

Executes delete flow and applies UI refresh behavior.

- Calls `RequestManager.delete_collection_item(...)`.
- On success: reloads collections and restores tree state.
- On failure: shows warning/critical dialogs and logs context.

### `RequestManager.delete_collection_item(item_id: str, item_type: str) -> bool`

Type-based delete dispatch.

- `item_type == "request"` -> `delete_request(...)`
- `item_type == "collection"` -> `delete_collection(...)`
- Unsupported type returns `False`

## Configuration

No task-specific settings were added.

Observability relies on existing global metrics server configuration:
- `settings.metrics_host`
- `settings.metrics_port`

## Troubleshooting

### Right-click does not show `Delete`

- Verify `collections_view` uses `Qt.CustomContextMenu`.
- Verify `customContextMenuRequested` is connected to
  `show_collection_item_context_menu`.

### Clicking `Delete` does nothing

- Check confirmation dialog was not cancelled.
- Check logs for `collection_item_delete_*` messages in `MainWindow`.
- Confirm item carries valid `Qt.UserRole` data (`RequestData` or collection ID string).

### Delete appears successful but item returns after reload

- Check storage write permissions for collection data directory.
- For collection deletion, confirm collection filename still matches collection name
  (current persistence uses name-based filenames).

### Delete metrics are missing

- Confirm metrics server is running.
- Inspect `/metrics` for
  `gui_collection_delete_actions_total{item_type="...",status="..."}` after actions.
