# Collection Tree Actions

## Overview

`CollectionTreeActions` (`pypost/ui/presenters/collection_tree_actions.py`) owns
right-click context-menu behavior for the collections tree: **New tab** (HTTP requests and
saved WebSocket profiles — [PYPOST-1160](websocket_collections_menu.md)), **Export
Collection…** (collection or parent of a request; PYPOST-1013), **Rename**, and
**Delete**. It also handles the inline rename editor lifecycle and delete confirmation flow.

`CollectionsPresenter` wires the tree view to this class and keeps tree loading, navigation,
and expand/collapse state.

Collections **New tab** does not show `NewTabProtocolPicker`. It copies a saved HTTP
request or WebSocket profile into an isolated tab and records
`gui_new_tab_actions_total` with `source=collections_context`. HTTP rows still use
default `protocol=unknown`; WebSocket rows record `protocol=websocket` (PYPOST-1160).
WebSocket isolated tabs, rename tab sync, and delete-close prompts:
[websocket_collections_menu.md](websocket_collections_menu.md). Blank-tab picker
(`Ctrl+N` / **+**): [new_tab_protocol_picker.md](new_tab_protocol_picker.md).

## Architecture

```mermaid
flowchart TB
    CP[CollectionsPresenter]
    CTA[CollectionTreeActions]
    CEA[CollectionExportActions]
    RM[RequestManager]
    CP -->|callbacks + signals| CTA
    CTA -->|export_collection clicked index| CP
    CP --> CEA
    CTA --> RM
    CP --> Model[QStandardItemModel]
    CP --> View[QTreeView]
    CTA --> View
```

| Component | Role |
|-----------|------|
| `CollectionsPresenter` | Tree model, open, expand/collapse; injects export |
| `CollectionItemRenameDelegate` | Inline rename editor lifecycle |
| `CollectionTreeActions` | Context menu (New tab / Export / Rename / Delete) |
| `CollectionExportActions` | Shared export; see [collection_export.md](collection_export.md) |
| `collection_item_dialogs` | Shared dialogs (collection, tab, env, history) |
| `RequestManager` | `rename_collection_item`, `delete_collection_item` |

Wiring in `CollectionsPresenter.__init__`:

- `setItemDelegate(CollectionItemRenameDelegate)` — commit/cancel callbacks to tree actions
- `customContextMenuRequested` → `CollectionTreeActions.show_context_menu`
- `export_collection=self._export_collection_at_index` — menu export passes clicked index as `source_index`, overriding distant selection

## Expand/collapse state (`CollectionsPresenter`)

Collection rows store a collection id (`str`) in `Qt.UserRole`; request rows store `RequestData`.
`_is_collection_item(index)` centralizes that discrimination for:

- `_on_tree_expanded` / `_on_tree_collapsed` — persist expanded collection ids in `StateManager`
  (debounced disk write; flushed on app exit)
- `restore_tree_state` — re-expand saved collection nodes after model rebuild

`CollectionsPresenter` keeps `_collection_items_by_id` (`dict[str, QStandardItem]`) in sync on
`refresh_tree`, `_insert_collection_into_tree`, and `remove_item_from_tree`. Restore iterates
only saved expanded ids and looks up each collection in O(1) instead of scanning every root
row (PYPOST-390, PYPOST-94). `_find_collection_item` uses the same index for collection lookups.

Request indices are ignored by expand/collapse persistence (unchanged behavior).

## API / Usage

### `CollectionTreeActions.show_context_menu(pos)`

Resolves the item at `pos`, builds the menu, and dispatches the selected action.

Menu order (PYPOST-1013):

| Row type | Actions |
|----------|---------|
| Collection | **Export Collection…**, Rename, Delete |
| Request | New tab, **Export Collection…**, Rename, Delete |
| WebSocket profile | New tab, **Export Collection…**, Rename, Delete |

**Export Collection…** is omitted when the optional `export_collection` callback is
`None` (isolated rename/delete harnesses). Production always injects it. Choosing export
logs `collection_export_selected` then calls `export_collection(clicked_index)`.
The passed `clicked_index` acts as `source_index` in `CollectionsPresenter` / `CollectionExportActions`,
ensuring the clicked collection (or parent collection for a clicked request) is exported regardless of
what row currently holds `currentIndex()`. Node resolution inspects `Qt.ItemDataRole.UserRole`:
a `str` payload targets that collection directly, while a `RequestData` payload resolves to the collection id
on `item.parent()`.

### `CollectionTreeActions.handle_rename_committed(new_name)`

Finalizes a successful inline rename (persistence, metrics, tree sync).

### `CollectionTreeActions.handle_rename_cancelled()`

Restores the tree label after Escape cancel.

### `CollectionTreeActions.handle_rename_rejected_empty()`

Handles empty-name rejection from the delegate.

### `CollectionTreeActions.handle_delete(item_id, item_type, item_label)`

Runs delete persistence, emits `requests_deleted` via callback, and updates the tree
incrementally or via `refresh_tree` fallback.

### `collection_item_dialogs`

`pypost/ui/collection_item_dialogs.py` centralizes QMessageBox usage for collection rename
and delete, plus tab, environment, and history flows (PYPOST-539):

| Helper | When used |
|--------|-----------|
| `confirm_delete(parent, item_label)` | Collection delete context-menu (Yes/No) |
| `show_rename_empty_name_error(parent)` | Delegate rejects empty rename |
| `show_rename_failure(parent, label, error)` | Rename persistence exception |
| `show_rename_not_found(parent, label)` | Rename returned false |
| `show_delete_failure(parent, label, error)` | Delete persistence exception |
| `show_delete_not_found(parent, label)` | Delete returned false |
| `show_request_failed_error(parent, error)` | Plain-string request failure in tabs |
| `show_request_error(parent, message)` | Structured request error in tabs |
| `prompt_dirty_sibling_tab_reload(parent, name)` | Dirty sibling tab saved elsewhere |
| `prompt_clean_sibling_tab_reload(parent, name)` | Clean sibling tab saved elsewhere |
| `confirm_delete_environment(parent, env_name)` | Environment dialog delete (Yes/No) |
| `show_copy_environment_empty_name_error(parent)` | Environment copy with empty name |
| `show_copy_environment_duplicate_name_error(parent, name)` | Environment copy duplicate name |
| `confirm_clear_history(parent)` | History panel clear-all (Yes/No) |
| `show_env_save_failed(parent, message)` | Environment storage save failure |
| `show_no_environment_selected(parent)` | Variable set with no environment selected |
| `show_invalid_variable_name_error(parent, error_msg)` | Variable name validation error |
| `show_mcp_server_start_failed(parent, message)` | MCP server startup failure |
| `show_metrics_server_start_failed(parent, message)` | Metrics server startup failure |
| `show_save_request_name_required(parent)` | Save dialog empty request name |
| `show_save_collection_name_required(parent)` | Save dialog empty new collection name |
| `confirm_overwrite_request(parent, message)` | Overwrite existing saved request (Yes/No) |
| `confirm_overwrite_newer_saved_version(parent)` | Overwrite newer disk version (Yes/No) |
| `show_migration_result(parent, title, body, success=…)` | Settings encryption migration outcome |
| `confirm_re_encrypt_environments(parent)` | Settings re-encrypt confirmation (Yes/No) |
| `show_invalid_retryable_status_codes(parent, message)` | Settings retry policy validation |

PYPOST-539 added tab, environment dialog, and history helpers; PYPOST-547 added env presenter,
main window, save dialog, save orchestrator, and settings dialog helpers.

### Callbacks (constructor)

| Callback | Purpose |
|----------|---------|
| `find_item` | Locate `QStandardItem` by id and type |
| `remove_item` | Remove one node without full rebuild |
| `refresh_tree` / `restore_tree_state` | Fallback when item missing from model |
| `emit_collections_changed` | After successful rename or delete |
| `emit_request_renamed` | After request rename |
| `emit_requests_deleted` | After delete with affected request IDs |
| `emit_open_isolated_tab` | After **New tab** on a request |
| `emit_open_isolated_websocket_tab` | After **New tab** on a WebSocket profile (PYPOST-1160) |
| `emit_websocket_renamed` | After WebSocket profile rename |
| `emit_websockets_deleted` | After delete with affected WebSocket profile IDs |
| `export_collection` | Optional clicked-index export (PYPOST-1013) |

## Configuration

No task-specific settings. Metrics use existing `MetricsManager` counters documented in
`doc/dev/collection_item_rename.md` and `doc/dev/collection_item_delete.md`. Export has no
GUI metrics; menu selection logs `collection_export_selected` (see
[collection_export.md](collection_export.md#logging)).

## Automated tests

`tests/helpers/collections_tree.py` provides shared fixtures (`FakeRequestManager`,
`patch_tree_context_menu`, `patch_rename_context_menu`, `patch_delete_context_menu`,
`build_isolated_tree_actions()`, `wire_rename_delegate`, `wait_for_rename_editor`,
`commit_inline_rename`, `cancel_inline_rename`, etc.) for presenter integration and
isolated `CollectionTreeActions` tests. Pass `with_rename_delegate=True` to
`build_isolated_tree_actions` for end-to-end rename editor tests. The isolated harness
builds a minimal `QTreeView` + `QStandardItemModel` with `MagicMock` callbacks (no
`CollectionsPresenter`) and wires a mock `export_collection` by default.

After PYPOST-1013, mocked menu helpers take `action_count` as the **full** menu size:

| `action_count` | Row | Action list |
|----------------|-----|-------------|
| `3` (default) | Collection | `[Export, Rename, Delete]` |
| `4` | Request / WebSocket | `[New tab, Export, Rename, Delete]` |

Rename/delete suites pass `action_count=3` or `4` so they still select Rename/Delete by
position after Export was inserted.

`tests/test_collection_tree_actions.py` covers menu dispatch and rename callbacks in isolation:

| Test | Behavior |
|------|----------|
| `test_invalid_index_skips_context_menu` | Blank click — no menu |
| `test_collection_menu_offers_export_collection` | Collection menu includes Export (PYPOST-1013) |
| `test_request_menu_offers_export_collection` | Request menu includes Export (PYPOST-1013) |
| `test_collection_export_menu_dispatches_clicked_index` | Export dispatch + clicked index |
| `test_request_export_menu_dispatches_clicked_index` | Request-row export passes clicked index |
| `test_collection_export_menu_logs_selected` | Logs `collection_export_selected` |
| `test_collection_menu_offers_rename_and_delete` | Collection node actions |
| `test_request_menu_offers_new_tab_rename_delete` | Request node actions |
| `test_rename_selected_starts_inline_edit` | Rename dispatches inline edit |
| `test_new_tab_selected_emits_open_isolated_tab` | New tab copies request, emits callback |
| `test_delete_cancelled_skips_persistence` | Delete No — tree unchanged |
| `test_delete_confirmed_removes_request` | Delete Yes — row removed |
| `test_rename_cancel_restores_tree_incrementally` | Escape cancel restores label |
| `test_rename_commit_updates_request_tree_and_emits` | Request rename + callbacks |
| `test_rename_commit_updates_collection_tree` | Collection rename |
| `test_rename_rejected_empty_shows_warning` | Empty name rejection |

`tests/test_collection_tree_delete_confirmation.py` asserts Yes/No confirmation
branching and `track_gui_collection_delete_action` call sequences (`selected` →
`cancelled` or `succeeded`) for collection and request nodes.

`tests/test_collection_tree_rename_context_menu.py` asserts rename context-menu dispatch
and `track_gui_collection_rename_action` for `selected`, `cancelled`, `succeeded`, and
`rejected_empty` on collection and request nodes (isolated harness).

`tests/test_collection_tree_rename_metrics.py` asserts presenter-level rename metrics for
`error`, `not_found`, `rejected_empty`, and `cancelled` (mirrors delete metrics module).

| Rename test | Behavior |
|-------------|----------|
| `test_collection_rename_selected_records_selected_metric` | Collection Rename → `selected` + inline edit |
| `test_request_rename_selected_records_selected_metric` | Request Rename → `selected` + pending state |
| `test_collection_rename_cancel_records_cancelled_metric` | Escape cancel → `cancelled` |
| `test_request_rename_cancel_records_cancelled_metric` | Request cancel restores label |
| `test_collection_rename_commit_records_succeeded_metric` | Collection commit → `succeeded` |
| `test_request_rename_commit_records_succeeded_metric` | Request commit → `succeeded` |
| `test_rename_empty_name_records_rejected_empty_metric` | Empty name → `rejected_empty` |
| `test_rename_selected_does_not_emit_succeeded_metric` | Menu select does not emit `succeeded` |
| Presenter `test_context_menu_rename_*` | Full presenter wiring for menu → edit |

`tests/test_collection_tree_rename_delegate_e2e.py` exercises the full inline editor path
(context menu → real `QTreeView.edit` → delegate commit/cancel/empty-name) for collection and
request nodes:

| E2E test | Behavior |
|----------|----------|
| `test_request_rename_commit_via_delegate_records_succeeded_metric` | Menu → edit → commit → `succeeded` |
| `test_collection_rename_commit_via_delegate_records_succeeded_metric` | Collection commit via delegate |
| `test_request_rename_cancel_via_delegate_records_cancelled_metric` | Delegate cancel → `cancelled` |
| `test_request_rename_empty_name_via_delegate_records_rejected_empty_metric` | Empty commit → `rejected_empty` |

Patch `QMenu` under `pypost.ui.presenters.collection_tree_actions`. Patch dialog helpers
(`confirm_delete`, `show_rename_empty_name_error`, `show_delete_failure`, etc.) at the same
import site used by the caller (e.g. `pypost.ui.presenters.tabs_presenter.show_request_error`).
Unit tests for helpers live in `tests/test_collection_item_dialogs.py`.
Presenter wiring and integration paths remain in `tests/test_collections_presenter.py`, while `tests/test_collection_export_ui.py` (`TestExportCollectionSourcePrecedence`) tests end-to-end source index override of distant tree selections.

### Tree expand/collapse state tests (PYPOST-388)

| Test | Behavior |
|------|----------|
| `test_on_tree_expanded_updates_state` | Expand adds collection id to `StateManager` |
| `test_on_tree_collapsed_updates_state` | Collapse removes collection id |
| `test_restore_tree_state_expands_known_ids` | `restore_tree_state` expands saved ids |
| `test_tree_expansion_saved_and_restored_after_reload` | Round-trip after `load_collections` |
| `test_restore_tree_state_skips_stale_saved_collection_ids` | Stale ids ignored (PYPOST-389) |
| `test_restore_tree_state_expands_only_collections_in_saved_list` | Subset expansion (PYPOST-391) |
| `test_restore_tree_state_expands_via_collection_index` | Many collections; subset restore (PYPOST-390/94) |
| `test_collection_index_updated_on_incremental_insert_and_remove` | Index sync on insert/remove (PYPOST-390/94) |

`tests/test_settings_persistence.py` (`TestStateManagerPersistence`) covers disk persistence
of `expanded_collections` via real `StateManager` + `ConfigManager`, including debounced
coalescing and `flush_pending_save()` durability.

## Troubleshooting

### Context menu tests fail after moving imports

Patch `QMenu` and dialog helpers under `pypost.ui.presenters.collection_tree_actions`,
not `collections_presenter`.

### Rename/delete tests assert the wrong action after adding Export

Bump `action_count` to `3` (collection) or `4` (request) so mocked action lists include
the Export slot. See `make_delete_menu_actions` / `patch_rename_context_menu` in
`tests/helpers/collections_tree.py`.

### Rename pending state in tests

For isolated tests, set `harness.actions._pending_rename` directly. In presenter tests,
`presenter._pending_rename` delegates to `presenter._tree_actions._pending_rename`.
