# PYPOST-538: Code Cleanup

## Changes

- Removed duplicate `_make_collection`, `_make_request`, `FakeRequestManager`,
  `FakeStateManager`, `FakeMetrics`, and `_patch_menu` from `test_collections_presenter.py`.
- Removed per-class `_patch_menu` and `_delete_via_menu` from isolated test modules.
- Deleted `collection_tree_actions_test_support.py` after merging into `tests/helpers/`.
- Enhanced `FakeRequestManager` with `deleted`/`renamed` tracking used by isolated tests.

## Verification

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest \
  tests.test_collections_presenter \
  tests.test_collection_tree_actions \
  tests.test_collection_tree_delete_confirmation -v
```

All 51 tests pass.
