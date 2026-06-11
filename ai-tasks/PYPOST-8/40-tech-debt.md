# PYPOST-8: Technical Debt Analysis


## Status: FIXED
Addressed in PYPOST-14 by implementing `StateManager`.

## Shortcuts Taken

- **[FIXED] Direct Settings Manipulation from UI**: Tree state logic
  (`expanded_collections`) is now managed via `StateManager`. `MainWindow` no longer depends
  directly on the settings structure for this functionality.
- **Synchronous tree-state saves** ([PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386)):
  Each expand/collapse persists settings immediately; very frequent clicks add I/O but are fine at
  current scale.

## Code Quality Issues

- **Type Check Duplication**: In methods `on_tree_expanded`, `on_tree_collapsed`, and `restore_tree_state`, the check `isinstance(data, str)` is repeated to determine if an item is a collection. This could be moved to a helper method `_is_collection_item(index)`. — [PYPOST-387](https://pypost.atlassian.net/browse/PYPOST-387)

## Missing Tests

- **[FIXED] Unit tests for tree state save/restore** ([PYPOST-388](https://pypost.atlassian.net/browse/PYPOST-388)):
  `tests/test_collections_presenter.py` and `tests/test_settings_persistence.py`.
- **[FIXED] Edge-case tests (stale collection ids in settings)** ([PYPOST-389](https://pypost.atlassian.net/browse/PYPOST-389)):
  `test_restore_tree_state_skips_stale_saved_collection_ids` in `tests/test_collections_presenter.py`.

## Performance Concerns

- **[FIXED] Linear Search on Restore** ([PYPOST-390](https://pypost.atlassian.net/browse/PYPOST-390)):
  `restore_tree_state` uses `_collection_items_by_id` for O(expanded) lookup instead of
  scanning all root rows.

## Follow-up Tasks

- **[FIXED] UI state preservation tests** ([PYPOST-391](https://pypost.atlassian.net/browse/PYPOST-391)):
  `test_restore_tree_state_expands_only_collections_in_saved_list` in
  `tests/test_collections_presenter.py`.
- Consider debouncing settings saving if I/O performance issues arise. — [PYPOST-392](https://pypost.atlassian.net/browse/PYPOST-392)
