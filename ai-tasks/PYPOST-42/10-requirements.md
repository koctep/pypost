# PYPOST-42: Auto-switch to Body Tab When HTTP Method Changes to PUT/POST

## Goals

When a user selects PUT or POST as the HTTP method in the request editor, the UI should
automatically switch the active tab to "Body". Currently the user must manually click the
Body tab after choosing a method that typically requires a request body, which adds friction
to the workflow. The goal is to eliminate that extra step and guide the user to the relevant
input immediately.

## User Stories

- As a developer, I want the Body tab to be automatically selected when I choose POST or PUT
  so that I can start typing the request body without extra clicks.
- As a user, I want the UI to stay on my current tab when I switch to GET, DELETE, PATCH, or
  other body-less methods so that my workflow is not disrupted.

## Definition of Done

- Selecting POST or PUT in the method combo box automatically switches `detail_tabs` to the
  Body tab.
- Selecting any other method (GET, DELETE, PATCH, MCP) does NOT force a tab switch.
- The auto-switch only triggers on explicit user interaction (method combo change), not on
  initial data load or programmatic `load_data` calls.
- Existing behaviour of `_on_method_changed` (placeholder text for MCP) is preserved.
- No regressions in existing tests.

## Task Description

**Scope:** `pypost/ui/widgets/request_editor.py` — `RequestWidget` class.

**Problem:** After selecting POST or PUT, users have to manually navigate to the Body tab
to enter the request body. This is a common and repetitive action that should be automated.

**Functional scope:**

- In `RequestWidget._on_method_changed`, when `method` is `"POST"` or `"PUT"`, call
  `self.detail_tabs.setCurrentWidget(self.body_edit)` (or equivalent by index).
- Do not switch tabs for other methods.
- Ensure `load_data` does not trigger the auto-switch (it calls `_on_method_changed`
  internally — may need a guard flag or a separate method).

**Out of scope:** Changing tab order, renaming tabs, or modifying other widgets.

**Programming language:** Python (PyPost, PySide6).

## Q&A

- **Q:** Which methods should trigger the auto-switch? **A:** POST and PUT only.
- **Q:** Should the switch happen when loading a saved request? **A:** No — only on explicit
  user interaction via the method combo box.
- **Q:** What if the user is already on the Body tab? **A:** No-op; `setCurrentWidget` is
  idempotent.
