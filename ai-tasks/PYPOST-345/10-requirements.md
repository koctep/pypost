# PYPOST-345: End-to-end GUI rename via delegate editor

Parent epic: [PYPOST-36](https://pypost.atlassian.net/browse/PYPOST-36) — Add Rename Action to
Context Menu.

Related: [PYPOST-342](https://pypost.atlassian.net/browse/PYPOST-342) — rename context-menu and
metrics coverage (partial overlap).

## Goals

Close the remaining gap in automated rename GUI coverage: tests must exercise the full inline
editor path from context-menu **Rename** through `QTreeView.edit`, the rename delegate, and
commit/cancel/empty-name outcomes — not only direct calls to `handle_rename_*` or mocked
`view.edit`.

## User Stories

- As a maintainer, I want automated tests that drive the real inline rename editor so delegate
  wiring regressions are caught before release.
- As a maintainer, I want commit, cancel, and empty-name flows to assert the same rename
  metrics and tree updates as production when the delegate is involved.

## Definition of Done

- Context-menu **Rename** starts real `QTreeView.edit` with `CollectionItemRenameDelegate`
  installed (collection and request nodes).
- Commit via delegate records `succeeded` metric and updates tree/model.
- Cancel via delegate records `cancelled` metric and restores labels.
- Empty-name commit via delegate records `rejected_empty` metric and shows warning.
- Tests declare explicit `pytest.mark.timeout` per project rules.
- Full test suite passes.

## Scope

- In scope: test helpers, new e2e rename delegate tests, dev docs.
- Out of scope: storage collision tests (PYPOST-346), production code changes, browser
  verification.

## Q&A

- **Overlap with PYPOST-342?** PYPOST-342 added context-menu dispatch and metrics tests that mock
  `view.edit` or call handlers directly. PYPOST-345 adds the delegate editor integration layer
  those tests intentionally skipped.
