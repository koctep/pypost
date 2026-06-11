# PYPOST-342: Technical Debt

## Resolved

- **Rename tests omit GUI** (PYPOST-342): Added isolated context-menu tests, presenter metrics
  tests, and presenter inline-edit wiring tests mirroring delete-flow coverage.

## Remaining (non-blockers)

- **End-to-end rename via delegate editor** ([PYPOST-345](https://pypost.atlassian.net/browse/PYPOST-345)):
  Tests still invoke `handle_rename_*` directly or patch QMenu; full delegate commit through
  `QTreeView.edit` is not simulated.
- **Storage collision on collection rename** ([PYPOST-346](https://pypost.atlassian.net/browse/PYPOST-346)):
  No automated test when target filename already exists.

## Follow-up Tasks

None new — existing PYPOST-345/346/348/351 cover remaining gaps.
