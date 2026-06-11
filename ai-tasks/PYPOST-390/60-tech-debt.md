# PYPOST-390: Technical Debt Analysis

## Shortcuts Taken

None.

## Code Quality Issues

None introduced.

## Missing Tests

- **Resolved (PYPOST-390):** `test_restore_tree_state_expands_via_collection_index`,
  `test_collection_index_updated_on_incremental_insert_and_remove` in
  `tests/test_collections_presenter.py`.

## Remaining (out of scope, from PYPOST-8)

- Synchronous tree-state saves on each expand/collapse — [PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386)
- Debounced settings save — [PYPOST-392](https://pypost.atlassian.net/browse/PYPOST-392)

## Follow-up Tasks

None new — related items already tracked in Jira.

## Verdict

**SAFE TO CLOSE**
