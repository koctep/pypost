# PYPOST-10: Technical Debt Analysis

## Status: FIXED
Addressed in PYPOST-14 by implementing `StateManager`.

## Shortcuts Taken

- **[FIXED] Direct Settings Manipulation from UI**: Tree state logic
  (`expanded_collections`) is now managed via `StateManager`. `MainWindow` no longer depends
  directly on the settings structure for this functionality.
- **Synchronous Saving**: Settings are saved synchronously on every click
  (expand/collapse). With very frequent clicking, this might cause excess I/O operations, but
  for current scale, it's not critical.

## Code Quality Issues

- **Type Check Duplication**: In methods `on_tree_expanded`, `on_tree_collapsed`, and `restore_tree_state`, the check `isinstance(data, str)` is repeated to determine if an item is a collection. This could be moved to a helper method `_is_collection_item(index)`.

## Missing Tests

- Unit tests for tree state save/restore logic are missing. Testing was done manually.
- No tests for edge cases (e.g., ID exists in settings but collection is gone).

## Performance Concerns

- **Linear Search on Restore**: `restore_tree_state` iterates through all root level items. With a huge number of collections (thousands), this might be slow, but for typical usage (dozens of collections), it's instant.

## Follow-up Tasks

- Write tests to verify UI state preservation.
- Consider debouncing settings saving if I/O performance issues arise.
