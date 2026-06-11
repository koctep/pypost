# PYPOST-390: Code Cleanup

## Changes Reviewed

- Removed full root scan from `restore_tree_state`; logic is shorter and intent is clearer.
- Reused `_collection_items_by_id` in `_find_collection_item` for collections — no duplicate
  linear search.
- No dead code or unused helpers introduced.

## Verification

- `python -m unittest tests.test_collections_presenter.TestCollectionsPresenter` — pass (venv).
