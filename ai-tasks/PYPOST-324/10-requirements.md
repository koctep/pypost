# PYPOST-324: Extract collection context-menu delete from MainWindow

## Goals

Collection tree delete was added on `MainWindow` during PYPOST-35. Architecture called for a
dedicated UI action/controller layer so the main window stays a thin composition root.

## User Stories

- As a maintainer, I want delete confirmation and persistence outside `MainWindow` so I can
  evolve collection UX without touching the shell window.
- As a user, I want delete from the collection context menu to behave unchanged (confirm,
  remove item, close affected tabs).

## Definition of Done

- `MainWindow` has no context-menu delete methods or delete-flow logic.
- Delete is owned by `CollectionTreeActions` and wired through `CollectionsPresenter`.
- `MainWindow` only composes presenters (e.g. `requests_deleted` → tab closure).
- Regression tests pass.

## Task Description

Debt follow-up from PYPOST-35. Extraction was completed incrementally (presenters refactor,
`CollectionTreeActions`, PYPOST-326 boundary finalization). This task verifies the target
architecture and closes the original debt ticket.

### Programming Language

Python

## Q&A

- **Q:** Is new code required? **A:** No — verify existing extraction and document closure.
- **Q:** Relation to PYPOST-326? **A:** PYPOST-326 removed leftover presenter shims and added
  regression guards; PYPOST-324 closes the PYPOST-35 debt item for the same boundary.
