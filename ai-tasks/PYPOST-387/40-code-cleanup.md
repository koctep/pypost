# PYPOST-387: Code Cleanup

## Static Analysis

- No new linter issues in modified files.

## Formatting

- Line length within 100 characters.
- Trailing whitespace removed.

## Cleanup Actions

- Placed `_is_collection_item` adjacent to expand/collapse handlers (same concern).
- Early-return pattern in expand/collapse handlers reduces nesting.

## Tests

- `test_is_collection_item_true_for_collection_index`
- `test_is_collection_item_false_for_request_index`
- Existing expand/collapse/restore tests pass.
