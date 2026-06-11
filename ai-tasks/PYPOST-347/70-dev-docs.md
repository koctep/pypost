# PYPOST-347: Dev Docs

## Updates

- `doc/dev/collection_item_rename.md` — documented incremental rename tree sync via
  `_finish_rename_tree_update` and removed references to full tree reload on success/cancel.

## Cross-References

- `doc/dev/collection_loading.md` — `refresh_tree` still applies to save/startup paths; rename
  is now an exception for in-place updates.
