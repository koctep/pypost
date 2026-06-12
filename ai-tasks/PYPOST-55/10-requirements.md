# PYPOST-55: Extract hardcoded UI strings from EnvironmentDialog

## Goals

Environment manager dialogs and related flows scattered user-visible text (titles, labels,
menu actions, validation errors) across UI and core modules. Centralizing these strings
improves maintainability and prepares for future localization without changing runtime
behavior.

## Programming Language

Python 3.11+ (PyPost project standard).

## User Stories

- As a **contributor**, I want environment UI strings in one module, so copy changes do not
  require hunting through multiple widgets.
- As a **user**, I want the same dialog titles and error messages as before, so this refactor
  does not change the experience.
- As a **maintainer**, I want validation error text shared between UI and core rename logic,
  so duplicate wording cannot drift.

## Definition of Done

- [x] All user-visible strings from EnvironmentDialog and its child widgets live in
  `pypost/core/environment_messages.py`.
- [x] Copy/delete confirmation and duplicate-name errors use shared formatters.
- [x] `validate_environment_rename` returns messages from the constants module.
- [x] Existing Qt tests in `tests/test_env_dialog.py` pass unchanged.
- [x] New unit tests cover message formatters and rename validation messages.

## Task Description

### Problem

Dialog titles (e.g. "Copy Environment"), button labels, table headers, context-menu actions,
and validation messages were hardcoded inline in `EnvironmentDialog`, list/variables widgets,
and `collection_item_dialogs`.

### Scope

**In scope**

- Environment manager dialog window title
- Environment list widget: Add button, input dialogs, context menu
- Variables widget: table headers, MCP label, context menu
- Environment-specific QMessageBox helpers in `collection_item_dialogs`
- Rename validation messages in `environment_ops`

**Out of scope**

- Full i18n / Qt translation files
- Unrelated collection-tree "Rename" strings
- Logging message changes

### Non-functional requirements

- **No behavior change** — same English text shown to users.
- **Single source of truth** — parameterized messages use small formatter functions.

## Q&A

| Question | Answer |
| --- | --- |
| UI vs core module? | `core/environment_messages.py` — shared by UI and `environment_ops`. |
| Internationalization now? | No; constants only, no `tr()` wiring. |
