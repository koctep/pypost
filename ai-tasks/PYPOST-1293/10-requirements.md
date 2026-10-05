# PYPOST-1293: Add assertions to test_keys_noop_without_tabs; docstrings for HTTP routing tests

## Goals

Ensure complete test coverage and clear documentation standards for HTTP hotkey routing and
empty-state hotkey behavior in PyPost:
1. **Prevent regressions in empty workspace states**: Ensure hotkey keypresses (`F5` and
   `Ctrl+Return`) when no tabs are open perform a true no-op and do not unexpectedly mutate tab state
   or trigger handlers.
2. **Maintain documentation consistency**: Provide standard descriptive one-line docstrings across
   all HTTP hotkey routing tests to match the rest of the test suite.

## User Stories

- As a developer maintaining PyPost's UI, I want automated tests to explicitly verify that pressing
  execution hotkeys when no tabs are present leaves the tab container completely empty and
  unmutated, so that unintentional side effects or crashes are reliably caught.
- As a contributor reading test suites, I want all test cases in the HTTP routing group to have
  clear, consistent docstrings, so that I immediately understand each test's intent and scope.

## Definition of Done

- `test_keys_noop_without_tabs` explicitly asserts that the tab count remains zero and active tab
  kind remains None before and after pressing `F5` and `Ctrl+Return`.
- All tests in `TestCtrlReturnF5RoutingHttp` contain one-line docstrings describing their
  verification purpose.
- All modified tests run quickly, reliably, and pass quality gates (`make lint`, `make typecheck`,
  `make test`).

## Task Description

In `tests/test_main_window_hotkeys.py`, `TestCtrlReturnF5RoutingHttp` contains three tests:
1. `test_f5_sends_http_request`
2. `test_ctrl_return_sends_http_request`
3. `test_keys_noop_without_tabs`

Currently, `test_keys_noop_without_tabs` checks `active_tab_kind()` is None initially, then sends
`F5` and `Ctrl+Return`, but performs no post-invocation assertions. This could allow silent
regressions (such as opening a phantom tab or modifying state). Furthermore, the three tests in
`TestCtrlReturnF5RoutingHttp` lack one-line docstrings, unlike the rest of the test suite.

Constraints:
- Implementation language: Python.
- Test suite lines must not exceed 100 characters.
- Must follow project test standards including explicit timeout markers.

## Q&A

- Q: What exact state should be verified in `test_keys_noop_without_tabs`?
  A: Verify that before and after keypresses: `presenter.tabs.count()` is 0, and
  `presenter.active_tab_kind()` is None.
- Q: Should routing log lines be verified here or in `TestHotkeyRoutedLogging`?
  A: `TestHotkeyRoutedLogging.test_no_tab_logged_as_noop` already asserts the DEBUG log contract for
  no tabs. `test_keys_noop_without_tabs` focuses on state invariance (tab count and active kind
  remaining None/0).
