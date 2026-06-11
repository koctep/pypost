# PYPOST-325: Technical Debt Analysis

## Shortcuts Taken

- None. Umbrella debt closed by verifying existing PYPOST-330 and PYPOST-339 test
  modules cover the full metric matrix.

## Code Quality Issues

- Test helpers duplicate between confirmation and metrics modules — acceptable for
  isolated modules; consolidate only if a third delete-test module appears.

## Missing Tests

- None for delete metric emission. Remaining PYPOST-35 delete debt:
  - Context-menu composition (PYPOST-329)
  - Open-tab behavior after delete (PYPOST-332)

## Performance Concerns

- None.

## Follow-up Tasks

- Close or deduplicate [PYPOST-331](https://pypost.atlassian.net/browse/PYPOST-331)
  (duplicate tracking of metric label tests now delivered).
- Consider shared `tests/helpers/collection_tree_test_utils.py` if more delete tests
  land (optional, low priority).
