# PYPOST-329: Architecture — Collection tree context menu GUI tests

## Research

- `CollectionTreeActions.show_context_menu` builds `QMenu`, dispatches New tab /
  Rename / Delete, and calls `QMessageBox.question` before delete.
- `CollectionsPresenter` wires `customContextMenuRequested` to
  `CollectionTreeActions.show_context_menu`.
- Existing partial coverage in `tests/test_collections_presenter.py` (delete Yes/No)
  lives on the presenter test class; no dedicated module for menu behavior.
- `test_history_panel.py` and `test_env_dialog.py` patch `QMenu` at the module under
  test (`collection_tree_actions`, not `collections_presenter`).

## Implementation Plan

### Phase 1 — New test module

Create `tests/test_collection_tree_actions.py`:

| Test | Asserts |
|------|---------|
| `test_invalid_index_skips_context_menu` | `QMenu` not constructed |
| `test_collection_menu_offers_rename_and_delete` | Two actions, correct labels |
| `test_request_menu_offers_new_tab_rename_delete` | Three actions, correct labels |
| `test_rename_selected_starts_inline_edit` | `pending_rename` set, `edit` called |
| `test_new_tab_selected_emits_open_isolated_tab` | `copy_request_for_isolated_tab`, signal |
| `test_delete_cancelled_skips_persistence` | Tree unchanged after No |
| `test_delete_confirmed_removes_request` | Child row removed after Yes |

### Phase 2 — Test harness

- Reuse presenter + fake `RequestManager` pattern from `test_collections_presenter.py`.
- Patch `QMenu` and `QMessageBox` under `pypost.ui.presenters.collection_tree_actions`.
- Use `patch.object(view, "indexAt", ...)` to target collection vs request nodes.

### Phase 3 — Documentation

- Extend `doc/dev/collection_tree_actions.md` troubleshooting with test inventory.

## Non-goals

- No production code changes unless a test reveals a defect.
- No duplication of PYPOST-330 (confirmation metric labels) or PYPOST-331 work.
