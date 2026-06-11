# PYPOST-345: Technical Debt

## Resolved

- **End-to-end rename via delegate editor** (PYPOST-345): Added
  `test_collection_tree_rename_delegate_e2e.py` with real `QTreeView.edit`, delegate commit,
  cancel, and empty-name flows for collection and request nodes.

## Remaining (non-blockers)

- **Storage collision on collection rename** ([PYPOST-346](https://pypost.atlassian.net/browse/PYPOST-346)):
  No automated test when target filename already exists.
- **Presenter-level delegate e2e** (optional): E2E tests use isolated harness; presenter wiring
  is still covered by unit tests plus the new delegate path through shared `CollectionTreeActions`.

## Follow-up Tasks

None new — PYPOST-346 and other PYPOST-36 follow-ups remain tracked separately.
