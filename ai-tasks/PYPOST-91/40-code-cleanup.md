# PYPOST-91: Code Cleanup

## Static Analysis

- No new linter issues; no code changes required for this task.

## Formatting

- Existing implementation conforms to project line-length and style rules.

## Cleanup Actions

- Verified `_is_collection_item` is placed adjacent to expand/collapse handlers.
- Early-return pattern in expand/collapse handlers reduces nesting.

## Tests

- `test_is_collection_item_true_for_collection_index`
- `test_is_collection_item_false_for_request_index`
- `test_on_tree_expanded_updates_state`
- `test_on_tree_collapsed_updates_state`
- `test_restore_tree_state_*` suite
