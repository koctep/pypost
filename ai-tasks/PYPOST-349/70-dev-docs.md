# PYPOST-349: Dev Docs

## Updates

- Added `doc/dev/collection_tree_actions.md` — documents `CollectionTreeActions` module.
- Updated `doc/dev/collection_item_rename.md` — presenter vs actions split, corrected
  component references (logic now in presenter + `CollectionTreeActions`, not `MainWindow`).

## Cross-References

- `doc/dev/collection_item_delete.md` — delete flow now implemented in
  `CollectionTreeActions.handle_delete`.
- `doc/dev/collection_loading.md` — tree refresh remains in `CollectionsPresenter`.
