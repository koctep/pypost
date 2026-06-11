# PYPOST-347: Code Cleanup

## Static Analysis

- No new linter issues in modified files.

## Formatting

- Line length within 100 characters.
- Trailing whitespace removed.

## Cleanup Actions

- Removed redundant `restore_tree_state` calls on rename paths where the tree is not rebuilt.
- Grouped rename tree-sync helpers adjacent to `remove_item_from_tree` (same concern).
- Updated `FakeRequestManager.rename_collection_item` to mirror real rename semantics for tests.

## Tests

- All existing and new presenter rename tests pass before final review.
