# PYPOST-547: Migrate remaining QMessageBox callers

## Goals

Follow-up to PYPOST-539. Remaining UI modules still call `QMessageBox` directly with patterns
that belong in `collection_item_dialogs.py`. Centralizing them keeps wording consistent and
simplifies test patching.

## User Stories

- As a maintainer, I want all standard QMessageBox flows in shared helpers so future dialog
  changes happen in one place.
- As a user, I want the same confirmations and error messages as before.

## Definition of Done

- `env_presenter`, `main_window`, `settings_dialog`, `request_save_orchestrator`, and
  `save_dialog` no longer call `QMessageBox` directly.
- Shared helpers cover environment save/MCP failures, variable validation, metrics startup
  failure, save-dialog validation, overwrite confirmations, and settings migration/retry flows.
- Existing automated tests pass with updated patch targets.
- User-visible dialog text is unchanged.

## Scope

In scope: `env_presenter.py`, `main_window.py`, `settings_dialog.py`,
`request_save_orchestrator.py`, `save_dialog.py`, and `collection_item_dialogs.py`.

Out of scope: renaming `collection_item_dialogs` module; new dialog types.

## Programming Language

Python
