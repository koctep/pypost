# Collection Item Delete

## Overview

Collection tree items now support a context-menu `Delete` action with confirmation.
Supported item types:
- Collection
- Request inside a collection

The goal is to allow direct cleanup from the tree without extra navigation.

## Architecture

- **`CollectionTreeActions` (`pypost/ui/presenters/collection_tree_actions.py`)**:
  - Builds the context menu and prompts user confirmation before delete.
  - Resolves clicked item type (`collection` or `request`).
  - Handles success/error UI flow via `handle_delete`.
- **`CollectionsPresenter` (`pypost/ui/presenters/collections_presenter.py`)**:
  - Wires the tree view to `CollectionTreeActions`.
  - Emits `requests_deleted` after successful delete.
- **`MainWindow` (`pypost/ui/main_window.py`)**:
  - Wires `CollectionsPresenter.requests_deleted` to `TabsPresenter.close_tabs_for_request_ids`.
- **`RequestManager` (`pypost/core/request_manager.py`)**:
  - Owns deletion business logic:
    - `delete_request(request_id)`
    - `delete_collection(collection_id)`
    - `delete_collection_item(item_id, item_type)`
- **`StorageManager` (`pypost/core/storage.py`)**:
  - Persists collection changes and can remove collection files:
    - `delete_collection(collection_id, collection_name=...)`
- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Tracks delete-action outcomes:
    - `gui_collection_delete_actions_total{item_type,status}`

## API / Usage

### `CollectionTreeActions.show_context_menu(pos)`

Entry point for right-click actions on collection tree items.

- Builds a `QMenu` with optional **New tab**, `Rename`, and `Delete`.
- Emits telemetry for selected/cancelled/succeeded/not-found/error outcomes.
- Delegates deletion to `handle_delete` after confirmation.

### `CollectionTreeActions.handle_delete(item_id, item_type, item_label)`

Executes delete flow and applies UI refresh behavior.

- Calls `RequestManager.delete_collection_item(...)`.
- On success: removes the tree node incrementally or falls back to `refresh_tree`.
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
  `CollectionTreeActions.show_context_menu` via `CollectionsPresenter`.

### Clicking `Delete` does nothing

- Check confirmation dialog was not cancelled.
- Check logs for `collection_item_delete_*` messages in `collection_tree_actions`.
- Confirm item carries valid `Qt.UserRole` data (`RequestData` or collection ID string).

### Delete appears successful but item returns after reload

- Check storage write permissions for collection data directory.
- For collection deletion, confirm collection filename still matches collection name
  (current persistence uses name-based filenames).

### Delete metrics are missing

- Confirm metrics server is running.
- Inspect `/metrics` for
  `gui_collection_delete_actions_total{item_type="...",status="..."}` after actions.

## Testing

Delete metric emission by status and item type:

| Layer | File | Scenarios |
| --- | --- | --- |
| Confirmation + metrics | `tests/test_collection_tree_delete_confirmation.py` | `selected` / `cancelled` / `succeeded` for collection and request; `handle_delete` skipped on No |
| `handle_delete` failures | `tests/test_collection_tree_delete_metrics.py` | `error` on exception; `not_found` on false return; collection and request nodes |

Automated coverage for open-tab closure after delete (PYPOST-332):

| Layer | File | Scenarios |
| --- | --- | --- |
| Tab closure | `tests/test_tabs_presenter.py` | Matching tabs close, blank tab fallback, empty ID list, duplicate tabs, persisted state |
| Signal emission | `tests/test_collections_presenter.py` | `requests_deleted` for request and collection delete |
| Integration | `tests/test_delete_open_tabs_integration.py` | `requests_deleted` → `close_tabs_for_request_ids` wiring |

Focused run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_collection_tree_delete_confirmation.py \
  tests/test_collection_tree_delete_metrics.py \
  tests/test_delete_open_tabs_integration.py \
  tests/test_tabs_presenter.py -k "close_tabs" \
  tests/test_collections_presenter.py -k "requests_deleted"
```
