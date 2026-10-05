# PYPOST-1292: Share window-activation test helper between hotkey test modules

## Goals

During PYPOST-1285, hotkey integration testing required activating real Qt windows to simulate
and verify actual key clicks via `QTest.keyClick`.

Currently, two separate test modules implement duplicate logic:
- `tests/test_hotkeys.py` defines `_ACTIVATION_SKIP` and the context manager `_ActivatedWindow`
  with `activate()` and `click()` methods.
- `tests/test_main_window_hotkeys.py` defines `_ACTIVATION_SKIP` and duplicated helper methods
  `_activate()` and `_click()` in `TestMainWindowSendKeyWiring`.

This duplication creates maintenance overhead and the risk of policy drift (e.g. timeout durations,
skip messaging, and event processing semantics). Any future test involving real key simulation would
introduce a third copy.

The goal of this task is to:
1. Extract the shared Qt window activation and key simulation helper into a reusable test helper module
   under `tests/helpers/` (specifically `tests/helpers/qt_activation.py`).
2. Centralize `_ACTIVATION_SKIP` constant and activation logic (`qWaitForWindowActive(..., 2000)`).
3. Refactor both `tests/test_hotkeys.py` and `tests/test_main_window_hotkeys.py` to use the shared helper.
4. Ensure all existing hotkey tests continue passing without regression.

## User Stories

- As a developer writing GUI hotkey tests in PyPost, I want a standardized and shared test helper
  for window activation and key simulation, so that tests behave consistently across different
  QPA platforms and do not duplicate timeout or skip logic.
- As a maintainer auditing test harness quality, I want shared test utilities organized cleanly under
  `tests/helpers/`, preventing duplicated boilerplate across test files.

## Definition of Done

This task is considered `done` when:
1. A new test helper module `tests/helpers/qt_activation.py` is created with clean type annotations,
   docstrings, and exports for window activation and key simulation.
2. `tests/test_hotkeys.py` is refactored to use the shared activation helper, removing duplicated code.
3. `tests/test_main_window_hotkeys.py` is refactored to use the shared activation helper, removing
   duplicated code.
4. All existing tests in `tests/test_hotkeys.py` and `tests/test_main_window_hotkeys.py` pass.
5. Every test has explicit timeout markers.
6. `make lint`, `make typecheck`, and `make verify-ai-tasks` pass cleanly.

## Task Description

### Problem Description
Window activation under headless / offscreen / X11 test environments can be flaky or unsupported.
The pattern:
```python
window.show()
window.activateWindow()
if not QTest.qWaitForWindowActive(window, 2000):
    pytest.skip(ACTIVATION_SKIP)
focus_widget.setFocus()
QApplication.processEvents()
```
was independently written in both `test_hotkeys.py` and `test_main_window_hotkeys.py`. Both declare
identical skip strings and handle key clicking. Consolidating this logic into `tests/helpers/qt_activation.py`
eliminates code duplication and standardizes QPA skip behavior.

### Scope
- Create `tests/helpers/qt_activation.py`.
- Re-export or import helper in `tests/helpers/__init__.py` if appropriate.
- Refactor `tests/test_hotkeys.py` to consume the helper.
- Refactor `tests/test_main_window_hotkeys.py` to consume the helper.
- Verify test suites pass without regression.

### Non-Functional Requirements
- Maintain clean code formatting (lines <= 100 characters).
- Maintain type correctness (`make typecheck`).
- Zero production code impact (`pypost/` unchanged).

### Constraints and Assumptions
- Implementation language: Python.
- Test runner: pytest executed via `make test`.
- Do not alter runtime behavior or skip conditions of existing test suites.

## Q&A

- **Q: Where should the shared helper live?**
  **A:** In `tests/helpers/qt_activation.py`, sitting alongside existing Qt test helpers like
  `tests/helpers/qt_wait.py` and `tests/helpers/qt_item_view.py`.
- **Q: Does this affect production code?**
  **A:** No. This is a test-only technical debt cleanup task.
