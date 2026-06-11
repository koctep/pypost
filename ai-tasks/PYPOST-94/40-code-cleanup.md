# PYPOST-94: Code Cleanup

## Changes Reviewed

Verification-only task. `restore_tree_state` in `collections_presenter.py` already:

- Iterates `get_expanded_collections()` only (not root rows).
- Uses `_collection_items_by_id.get(collection_id)` for lookup.
- Skips missing ids silently.

No lint, format, or refactor changes required for this task.

## Verification

- Code review of `restore_tree_state` and index maintenance paths — clean.
- No dead code or duplicate root-scan logic found.
