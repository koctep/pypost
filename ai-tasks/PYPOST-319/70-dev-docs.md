# PYPOST-319: Developer Documentation

## Purpose

Document the incremental Collections tree update path for save-as.

## Modified Files

| File | Change |
|------|--------|
| `doc/dev/collection_loading.md` | `add_saved_request_to_tree` API and MainWindow save-as wiring |

## Key Takeaways for Developers

- After **save-as**, emit/handle `request_save_as_completed` → `add_saved_request_to_tree`.
- After **regular save**, keep using `request_saved` → `refresh_tree()` + `restore_tree_state()`.
- Incremental insert reuses `_make_collection_item` / `_make_request_item` shared with
  `refresh_tree()`.
- Expansion after save-as uses `StateManager` ids already updated in `TabsPresenter`.
