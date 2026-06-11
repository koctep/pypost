# PYPOST-538: Architecture

## Approach

Introduce `tests/helpers/collections_tree.py` as the single shared module for collection-tree
test fixtures. Merge content from `collection_tree_actions_test_support.py` (PYPOST-537) with
helpers previously duplicated in `test_collections_presenter.py`.

## Module layout

| Symbol | Purpose |
|--------|---------|
| `make_collection`, `make_request` | Model factories |
| `FakeRequestManager` | In-memory manager with delete/rename tracking |
| `FakeStateManager` | Expanded-collection state stub |
| `FakeMetrics` | No-op metrics stub |
| `patch_tree_context_menu` | Patch `QMenu` on `CollectionTreeActions` |
| `patch_view_context_menu` | Patch `indexAt` + `QMenu` |
| `patch_delete_context_menu` | Delete-selected menu preset |
| `IsolatedTreeActions` | Harness dataclass for direct actions tests |
| `build_isolated_tree_actions` | Factory for isolated harness |

## Test consumers

| File | Uses |
|------|------|
| `test_collections_presenter.py` | Fakes, `patch_view_context_menu` |
| `test_collection_tree_actions.py` | Full harness + patch helpers |
| `test_collection_tree_delete_confirmation.py` | Harness + `patch_delete_context_menu` |

## Removed

- `tests/collection_tree_actions_test_support.py` — superseded by `tests/helpers/collections_tree.py`
