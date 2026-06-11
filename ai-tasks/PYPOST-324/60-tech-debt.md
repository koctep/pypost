# PYPOST-324: Technical Debt

## Resolved

- **Tree delete in MainWindow**: delete context menu, confirmation, persistence, and metrics
  now live in `CollectionTreeActions`; `MainWindow` only wires `requests_deleted` to tabs.
  Finalized in [PYPOST-326](https://pypost.atlassian.net/browse/PYPOST-326).

## Follow-up Tasks

- Add direct unit tests for `CollectionTreeActions` menu dispatch in isolation. —
  [PYPOST-537](https://pypost.atlassian.net/browse/PYPOST-537)
- Consolidate QMessageBox error/confirmation helpers across UI. —
  [PYPOST-344](https://pypost.atlassian.net/browse/PYPOST-344)

## Non-blockers

- `_pending_rename` property on presenter still delegates to `CollectionTreeActions` for test
  setup convenience.
