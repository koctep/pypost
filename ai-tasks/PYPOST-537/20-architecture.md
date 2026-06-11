# PYPOST-537: Architecture

## Approach

Introduce `tests/collection_tree_actions_test_support.py` with `build_isolated_tree_actions()`
that mirrors the minimum presenter wiring:

| Piece | Test harness |
|-------|----------------|
| `QTreeView` + `QStandardItemModel` | Built in harness |
| `find_item` / `remove_item` | Local dict + tree scan |
| `refresh_tree` / `restore_tree_state` | `MagicMock` spies |
| Signal-like callbacks | `MagicMock` for emit_* callables |
| `FakeRequestManager` | In-memory collections + rename/delete |

## Test file layout

| File | Scope |
|------|-------|
| `test_collection_tree_actions.py` | Menu dispatch, rename cancel/commit/reject |
| `test_collection_tree_delete_confirmation.py` | Delete Yes/No + metric sequences |
| `collection_tree_actions_test_support.py` | Shared harness |

## Patch targets

All Qt/dialog patches remain under `pypost.ui.presenters.collection_tree_actions` so tests
exercise the same import paths as production.
