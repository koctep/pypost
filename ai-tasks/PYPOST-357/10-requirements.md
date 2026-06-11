# PYPOST-357: Integration Test for Response Search Flow

## Goals

Close the PYPOST-37 technical-debt gap for end-to-end search wiring: automated tests must exercise
search through a `RequestTab` after a response is displayed, using widget signals and controls — not
only direct calls to `ResponseView` private methods.

## User Stories

- As a **developer**, I want **integration tests that type a query and click Next**, so search bar
  signal wiring regressions are caught in CI.
- As a **maintainer**, I want **match counter assertions after navigation**, so find-next behavior
  stays correct when wired through `RequestTab`.

## Definition of Done

- Integration tests drive search via `QLineEdit.textChanged`, Next button, and Enter key on a tab
  whose body was populated by `display_response`.
- Typed query shows match counter (`N of M` or `No matches`).
- Next navigation advances the counter.
- New response via `display_response` clears search state.
- Developer docs list integration test location and focused run command.

## Task Description

Follow-up from PYPOST-37 (`ai-tasks/PYPOST-37/60-tech-debt.md`). Unit-level search tests exist in
`tests/test_response_view_search.py` (PYPOST-365); this task adds presenter-tab wiring coverage.

### In Scope

- New integration test module for response search flow.
- Workflow artifacts and dev-doc updates.

### Out of Scope

- Production search behavior changes.
- Full `MainWindow` e2e tests or live HTTP requests.
- Debounce, lazy match count, or other PYPOST-37 performance follow-ups.

### Constraints and Assumptions

- Tests run headlessly with explicit pytest timeouts.
- `TabsPresenter.add_new_tab` provides a real `RequestTab` with `ResponseView`.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not full MainWindow e2e? | RequestTab integration covers display → search wiring; main window chrome is separate. |
| Relation to PYPOST-365? | PYPOST-365 covers ResponseView unit tests; this task covers tab-level GUI entry points. |
