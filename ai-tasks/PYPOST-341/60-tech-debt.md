# PYPOST-341: Technical Debt Analysis

## Resolved

- **Inline rename without delegate**: Replaced `closeEditor` on default tree delegate with
  `CollectionItemRenameDelegate`.

## Remaining (non-blockers)

- **Rename tests omit GUI** ([PYPOST-342](https://pypost.atlassian.net/browse/PYPOST-342)):
  Coverage focuses on `RequestManager` business logic, not full GUI integration.
- **GUI rename gaps** ([PYPOST-345](https://pypost.atlassian.net/browse/PYPOST-345)):
  Context-menu visibility, full editor commit/cancel in Qt, metrics assertions in UI flow.
- **Direct `CollectionTreeActions` unit tests** ([PYPOST-349 follow-up](https://pypost.atlassian.net/browse/PYPOST-349)):
  Presenter tests cover rename handlers; isolated action tests still thin.

## Follow-up Tasks

- Add GUI integration tests for context-menu rename lifecycle — [PYPOST-348](https://pypost.atlassian.net/browse/PYPOST-348)
- Add direct unit tests for `CollectionTreeActions` rename dispatch — defer to PYPOST-348 scope

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; remaining items are pre-existing follow-ups.
