# PYPOST-10: Technical Debt Analysis


## Status: FIXED
Addressed in PYPOST-14 by implementing `StateManager`.

## Shortcuts Taken

- **[FIXED] Direct Settings Manipulation from UI**: Tree state logic
  (`expanded_collections`) is now managed via `StateManager`. `MainWindow` no longer depends
  directly on the settings structure for this functionality.
- **Synchronous tree-state saves** ([PYPOST-90](https://pypost.atlassian.net/browse/PYPOST-90)):
  Each expand/collapse persists settings immediately; very frequent clicks add I/O but are fine at
  current scale.

## Code Quality Issues

- **Type Check Duplication**: In methods `on_tree_expanded`, `on_tree_collapsed`, and `restore_tree_state`, the check `isinstance(data, str)` is repeated to determine if an item is a collection. This could be moved to a helper method `_is_collection_item(index)`. — [PYPOST-91](https://pypost.atlassian.net/browse/PYPOST-91)

## Missing Tests

- Unit tests for tree state save/restore logic are missing. Testing was done manually. — [PYPOST-92](https://pypost.atlassian.net/browse/PYPOST-92)
- No tests for edge cases (e.g., ID exists in settings but collection is gone). — [PYPOST-93](https://pypost.atlassian.net/browse/PYPOST-93)

## Performance Concerns

- **Linear Search on Restore**: `restore_tree_state` iterates through all root level items. With a huge number of collections (thousands), this might be slow, but for typical usage (dozens of collections), it's instant. — [PYPOST-94](https://pypost.atlassian.net/browse/PYPOST-94)

## Follow-up Tasks

- Write tests to verify UI state preservation. — [PYPOST-95](https://pypost.atlassian.net/browse/PYPOST-95)
- Consider debouncing settings saving if I/O performance issues arise. — [PYPOST-96](https://pypost.atlassian.net/browse/PYPOST-96)
