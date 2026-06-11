# PYPOST-539: Extend shared QMessageBox helpers

## Goals

Tabs presenter, environment dialog, and history panel still call `QMessageBox` directly with
patterns similar to the collection rename/delete flows consolidated in PYPOST-344. Shared helpers
reduce duplication and keep user-facing messages consistent.

## User Stories

- As a maintainer, I want tab, environment, and history dialogs centralized so wording stays
  consistent when these flows change.
- As a user, I want the same confirmations and error messages as before.

## Definition of Done

- `tabs_presenter`, `env_dialog`, and `history_panel` no longer call `QMessageBox` directly.
- Shared helpers cover request errors, sibling-tab stale prompts, environment delete/copy
  validation, and history clear confirmation.
- Existing automated tests pass with updated patch targets.
- User-visible dialog text is unchanged.

## Scope

In scope: `tabs_presenter.py`, `env_dialog.py`, `history_panel.py`, and
`collection_item_dialogs.py`.

Out of scope: `env_presenter.py` and other UI modules (separate follow-up).

## Programming Language

Python
