# PYPOST-344: Consolidate collection rename/delete dialog handling

## Goals

Rename and delete flows in the collections tree repeat the same QMessageBox patterns for
confirmation, validation errors, and persistence failures. Shared helpers reduce duplication
and lower the risk of inconsistent user-facing messages when these flows change.

## User Stories

- As a maintainer, I want one place to update rename/delete dialog titles and wording so
  collection tree behavior stays consistent.
- As a user, I want rename and delete to show the same confirmations and error messages as
  before.

## Definition of Done

- Rename and delete flows in `CollectionTreeActions` no longer call `QMessageBox` directly.
- Shared helpers cover delete confirmation, empty-name rename warning, and rename/delete
  failure and not-found notifications.
- Existing automated tests pass with updated patch targets.
- User-visible dialog text is unchanged.

## Task Description

Follow-up from PYPOST-36 tech debt. Scope is limited to collection item rename/delete flows;
other UI areas (tabs, environments, history) remain out of scope.

### Programming Language

Python

## Q&A

- **Why not migrate all QMessageBox usage in the app?** Broader consolidation is valuable but
  a separate follow-up; this task focuses on the duplicated rename/delete patterns called out
  in PYPOST-36.
