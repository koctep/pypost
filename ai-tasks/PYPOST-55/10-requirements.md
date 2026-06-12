# PYPOST-55: Requirements

## Business goal

Environment manager UI text (dialog titles, labels, menu actions, validation messages)
should live in one place so copy stays consistent and future localization is easier.

## User stories

- As a developer, I want environment dialog strings centralized so I do not hunt literals
  across widgets and helpers.
- As a user, I expect the same wording for add, copy, delete, and rename flows after
  this refactor.

## Acceptance criteria

1. User-visible strings for Manage Environments (dialog title, list actions, variable
   table headers, MCP label, copy/delete prompts) are defined in a constants module.
2. `EnvironmentDialog`, `EnvironmentListWidget`, `EnvironmentVariablesWidget`, and
   environment-related helpers in `collection_item_dialogs` import those constants.
3. Validation messages in `environment_ops.validate_environment_rename` use the same
   module (no duplicate literals).
4. Existing Qt-level environment dialog tests pass unchanged in behavior.

## Out of scope

- Full i18n / Qt translation files.
- Non-environment strings in `collection_item_dialogs.py` (collections, history, etc.).

## Programming language

Python (PySide6 UI).
