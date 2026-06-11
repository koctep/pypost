# PYPOST-94: Technical Debt Analysis

## Status

**RESOLVED** — linear root scan removed in PYPOST-390; PYPOST-94 verifies and closes the
PYPOST-10 follow-up.

## Shortcuts Taken

None for this task (verification-only).

## Code Quality Issues

None introduced. Resolved concern:

- **Linear search on restore** — `restore_tree_state` no longer iterates all root items;
  uses `_collection_items_by_id` (PYPOST-390).

## Missing Tests

None for this concern. Covered by:

- `test_restore_tree_state_expands_via_collection_index`
- `test_collection_index_updated_on_incremental_insert_and_remove`
- PYPOST-388/389/391 restore tests in `tests/test_collections_presenter.py`

## Performance Concerns

None remaining for restore. Request lookup in `_find_collection_item` still scans request
children per collection — acceptable at current scale; separate from restore path.

## Follow-up Tasks

None new. Related items already tracked:

- Synchronous tree-state saves — [PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386)
- Debounced settings save — [PYPOST-392](https://pypost.atlassian.net/browse/PYPOST-392)

## Verdict

**SAFE TO CLOSE**
