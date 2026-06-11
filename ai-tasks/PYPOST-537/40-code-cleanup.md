# PYPOST-537: Code Cleanup

## Changes

- Extracted duplicated `FakeRequestManager` and tree builders from test modules into
  `collection_tree_actions_test_support.py`.
- Renamed test class to `TestCollectionTreeActionsIsolated` to reflect direct construction.
- Removed `CollectionsPresenter` imports from dedicated collection-tree action test files.

## Not changed

- `test_collections_presenter.py` integration tests (still validate presenter wiring).
- `test_collection_tree_delete_metrics.py` (handle_delete failure paths via presenter).
