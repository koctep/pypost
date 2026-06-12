# PYPOST-722: Isolate Qt style state in theme tests

## Goals

Prevent order-dependence and pollution of Qt global style/stylesheet state in `test_style_manager_theme.py` when running the entire test suite.

## User Stories

As a PyPost developer,
I want our theme tests to run reliably in both isolation and within the full test suite
So that there are no false test failures due to state pollution from other GUI tests.

## Definition of Done

- A module-scoped style reset fixture is introduced in `tests/test_style_manager_theme.py`.
- The fixture saves the global QApplication style, palette, and stylesheet before running the theme tests, and restores them afterwards.
- Running `test_style_manager_theme.py` passes successfully in both isolation and the full suite.

## Task Description

When run in the full suite, previous GUI tests apply an application-level stylesheet on `QApplication.instance()`. In PySide6/Qt, setting an application stylesheet internally wraps the application style in a `QStyleSheetStyle` wrapper. Consequently, `qapp.style().objectName()` returns an empty string or `"stylesheet"` instead of `"fusion"`.

To prevent this order-dependence, `test_style_manager_theme.py` must isolate the global style/stylesheet state.

## Q&A

- **Q**: What should the module fixture do?
- **A**: Save original style, palette, and stylesheet; clear stylesheet before running tests; and restore everything on teardown.
