# PYPOST-332: Add tests for open-tab behavior after collection item delete

## Goals

When a user deletes a request or an entire collection from the collections tree, any open editor
tabs that reference those requests should close automatically. Without automated tests, regressions
in this behavior could leave stale tabs open and confuse users. This task adds test coverage so
the delete-to-tab-close flow remains reliable across future changes.

## User Stories

- As a developer, I want automated tests for tab closure after request delete so I can refactor
  presenters without breaking the user experience.
- As a developer, I want automated tests for tab closure after collection delete so all affected
  request tabs are closed in one operation.
- As a QA engineer, I want tests that cover signal wiring between collections and tabs presenters
  so integration regressions are caught in CI.

## Definition of Done

- Unit tests cover `TabsPresenter.close_tabs_for_request_ids` for matching tabs, blank-tab
  fallback, empty input, duplicate tabs, and persisted tab-state updates.
- Unit tests cover `CollectionsPresenter.requests_deleted` emission for request and collection
  delete paths.
- Integration tests verify that connecting `requests_deleted` to `close_tabs_for_request_ids`
  closes the correct tabs and updates persisted open-tab state.
- Full test suite passes.

## Task Description

Follow-up from PYPOST-35 technical debt: open tabs were reconciled in PYPOST-328 via
`requests_deleted` and `close_tabs_for_request_ids`, but no dedicated automated tests existed.
This task adds the missing test coverage without changing production behavior.

### In Scope

- Automated unit and integration tests for open-tab behavior after delete.
- Developer documentation of test locations and scenarios.

### Out of Scope

- Changes to delete or tab-close production logic.
- GUI tests for context menus or confirmation dialogs (covered by PYPOST-329/330).
- Metrics tests for delete actions (covered by PYPOST-331).

## Q&A

- **Why not only unit tests?** Signal wiring in `MainWindow` is a one-liner; an integration test
  between presenters catches disconnect or signature mismatches without spinning up the full
  window.
- **Parent task?** [PYPOST-35](https://pypost.atlassian.net/browse/PYPOST-35) — collection item
  delete; implementation in [PYPOST-328](https://pypost.atlassian.net/browse/PYPOST-328).
