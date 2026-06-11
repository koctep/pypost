# Collection Tree Actions

## Overview

`CollectionTreeActions` (`pypost/ui/presenters/collection_tree_actions.py`) owns
right-click context-menu behavior for the collections tree: **New tab** (requests only),
**Rename**, and **Delete**. It also handles the inline rename editor lifecycle and delete
confirmation flow.

`CollectionsPresenter` wires the tree view to this class and keeps tree loading, navigation,
and expand/collapse state.

## Architecture

```mermaid
flowchart TB
    CP[CollectionsPresenter]
    CTA[CollectionTreeActions]
    RM[RequestManager]
    CP -->|callbacks + signals| CTA
    CTA --> RM
    CP --> Model[QStandardItemModel]
    CP --> View[QTreeView]
    CTA --> View
```

| Component | Role |
|-----------|------|
| `CollectionsPresenter` | Builds tree model, left-click open, expand/collapse state |
| `CollectionItemRenameDelegate` | Inline rename editor lifecycle |
| `CollectionTreeActions` | Context menu, rename callbacks, delete with confirmation |
| `collection_item_dialogs` | Shared QMessageBox helpers for rename/delete flows |
| `RequestManager` | `rename_collection_item`, `delete_collection_item` |

Wiring in `CollectionsPresenter.__init__`:

- `setItemDelegate(CollectionItemRenameDelegate)` — commit/cancel callbacks to tree actions
- `customContextMenuRequested` → `CollectionTreeActions.show_context_menu`

## Expand/collapse state (`CollectionsPresenter`)

Collection rows store a collection id (`str`) in `Qt.UserRole`; request rows store `RequestData`.
`_is_collection_item(index)` centralizes that discrimination for:

- `_on_tree_expanded` / `_on_tree_collapsed` — persist expanded collection ids in `StateManager`
- `restore_tree_state` — re-expand saved collection nodes after model rebuild

`CollectionsPresenter` keeps `_collection_items_by_id` (`dict[str, QStandardItem]`) in sync on
`refresh_tree`, `_insert_collection_into_tree`, and `remove_item_from_tree`. Restore iterates
only saved expanded ids and looks up each collection in O(1) instead of scanning every root
row (PYPOST-390). `_find_collection_item` uses the same index for collection lookups.

Request indices are ignored by expand/collapse persistence (unchanged behavior).

## API / Usage

### `CollectionTreeActions.show_context_menu(pos)`

Resolves the item at `pos`, builds the menu, and dispatches the selected action.

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
and delete:

| Helper | When used |
|--------|-----------|
| `confirm_delete(parent, item_label)` | Delete context-menu action (Yes/No) |
| `show_rename_empty_name_error(parent)` | Delegate rejects empty rename |
| `show_rename_failure(parent, label, error)` | Rename persistence exception |
| `show_rename_not_found(parent, label)` | Rename returned false |
| `show_delete_failure(parent, label, error)` | Delete persistence exception |
| `show_delete_not_found(parent, label)` | Delete returned false |

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

## Configuration

No task-specific settings. Metrics use existing `MetricsManager` counters documented in
`doc/dev/collection_item_rename.md` and `doc/dev/collection_item_delete.md`.

## Automated tests

`tests/helpers/collections_tree.py` provides shared fixtures (`FakeRequestManager`,
`patch_tree_context_menu`, `build_isolated_tree_actions()`, etc.) for presenter integration
and isolated `CollectionTreeActions` tests. The isolated harness builds a minimal
`QTreeView` + `QStandardItemModel` with `MagicMock` callbacks (no `CollectionsPresenter`).

`tests/test_collection_tree_actions.py` covers menu dispatch and rename callbacks in isolation:

| Test | Behavior |
|------|----------|
| `test_invalid_index_skips_context_menu` | Blank click — no menu |
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

Patch `QMenu` under `pypost.ui.presenters.collection_tree_actions`. Patch dialog helpers
(`confirm_delete`, `show_rename_empty_name_error`, `show_delete_failure`, etc.) at the same
import site. Unit tests for helpers live in `tests/test_collection_item_dialogs.py`.
Presenter wiring and integration paths remain in `tests/test_collections_presenter.py`.

### Tree expand/collapse state tests (PYPOST-388)

| Test | Behavior |
|------|----------|
| `test_on_tree_expanded_updates_state` | Expand adds collection id to `StateManager` |
| `test_on_tree_collapsed_updates_state` | Collapse removes collection id |
| `test_restore_tree_state_expands_known_ids` | `restore_tree_state` expands saved ids |
| `test_tree_expansion_saved_and_restored_after_reload` | Round-trip after `load_collections` |
| `test_restore_tree_state_skips_stale_saved_collection_ids` | Stale ids ignored (PYPOST-389) |
| `test_restore_tree_state_expands_only_collections_in_saved_list` | Subset expansion (PYPOST-391) |
| `test_restore_tree_state_expands_via_collection_index` | Many collections; subset restore (PYPOST-390) |
| `test_collection_index_updated_on_incremental_insert_and_remove` | Index sync on insert/remove (PYPOST-390) |

`tests/test_settings_persistence.py` (`TestStateManagerPersistence`) covers disk persistence
of `expanded_collections` via real `StateManager` + `ConfigManager`.

## Troubleshooting

### Context menu tests fail after moving imports

Patch `QMenu` and dialog helpers under `pypost.ui.presenters.collection_tree_actions`,
not `collections_presenter`.

### Rename pending state in tests

For isolated tests, set `harness.actions._pending_rename` directly. In presenter tests,
`presenter._pending_rename` delegates to `presenter._tree_actions._pending_rename`.
