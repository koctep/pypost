# PYPOST-329: Technical Debt Analysis

## Shortcuts Taken

None for this task — tests only.

## Code Quality Issues

- Context menu test helpers (`_patch_menu`, fake managers) overlap with
  `test_collections_presenter.py`. A shared `tests/helpers/collections_tree.py` could
  deduplicate setup if more tree-action tests are added.

## Missing Tests

None for the PYPOST-329 scope. Confirmation-dialog metric label tests remain in
PYPOST-330; open-tab reconciliation after delete in PYPOST-332.

## Performance Concerns

None.

## Follow-up Tasks

- Extract shared collections tree test fixtures used by presenter and context-menu tests.
  — [PYPOST-538](https://pypost.atlassian.net/browse/PYPOST-538)
