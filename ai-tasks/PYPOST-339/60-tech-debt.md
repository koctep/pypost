# PYPOST-339: Technical Debt Analysis

## Shortcuts Taken

- None for this task.

## Code Quality Issues

- Test helpers duplicate `test_collection_tree_delete_confirmation.py` — acceptable
  for isolated modules; consolidate only if a third delete-test module appears.

## Missing Tests

- None introduced by this task. Remaining PYPOST-35 delete debt:
  - Context-menu composition (PYPOST-329) — may be done elsewhere.
  - PYPOST-331 duplicate tracking — close or merge when PYPOST-331 is picked up.

## Performance Concerns

- None.

## Follow-up Tasks

- Close or deduplicate PYPOST-331 now that `error` / `not_found` metrics are tested.
- Consider a shared `tests/helpers/collection_tree_test_utils.py` if more delete tests
  land (optional, low priority).
