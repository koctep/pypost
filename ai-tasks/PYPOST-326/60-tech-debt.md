# PYPOST-326: Technical Debt

## Resolved

- **MainWindow delete-flow growth**: delete context menu, confirmation, and metrics now live
  in `CollectionTreeActions`; `MainWindow` only wires `requests_deleted` to tabs.

## Follow-up Tasks

- Add direct unit tests for `CollectionTreeActions` in isolation (menu dispatch, rename
  cancel/commit). — [PYPOST-537](https://pypost.atlassian.net/browse/PYPOST-537)
- Consolidate QMessageBox error/confirmation helpers across UI. —
  [PYPOST-344](https://pypost.atlassian.net/browse/PYPOST-344)

## Non-blockers

- `_pending_rename` property on presenter still delegates to `CollectionTreeActions` for
  test setup convenience.
