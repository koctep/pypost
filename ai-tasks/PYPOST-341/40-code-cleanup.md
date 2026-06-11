# PYPOST-341: Code Cleanup

## Changes

- Removed unused `QAbstractItemDelegate` import from `collection_tree_actions.py`.
- Removed unused `QAbstractItemDelegate` import from `test_collections_presenter.py`.
- Exported `CollectionItemRenameDelegate` from `pypost/ui/delegates/__init__.py`.

## Lint

- `make test` — 802 passed (full suite).
