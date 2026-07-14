# PYPOST-798: Test tabBarClicked fallback on plus-tab chrome

## Goals

Close the test coverage gap identified in [PYPOST-797](https://pypost.atlassian.net/browse/PYPOST-797)
for the secondary plus-tab click path. The production fallback (`_on_tab_bar_clicked` on
`tabBarClicked`) must have regression tests so future refactors cannot silently break chrome
clicks outside the embedded `+` button.

## User Stories

- As a maintainer, I want a unit test that emits `tabBarClicked` on the plus index and asserts
  `new_tab_requested`, so the header fallback path is guarded.
- As a maintainer, I want a presenter-level test that emits `tabBarClicked` on the plus index
  and asserts a new request tab is added, so the end-to-end wiring from fallback to
  `add_new_tab` is verified.
- As a maintainer, I want a negative test that `tabBarClicked` on a non-plus index does not
  emit `new_tab_requested`, so the handler remains scoped to the plus tab.

## Definition of Done

- `test_tab_header.py` covers `tabBarClicked.emit(plus_idx)` → `new_tab_requested`.
- `test_tab_header.py` covers non-plus `tabBarClicked` → no emission.
- `test_tabs_presenter.py` covers `tabBarClicked.emit(plus_idx)` → request tab count increases.
- Primary path tests (`QTest.mouseClick` on embedded button) remain unchanged.
- `make check` passes.
- Dev docs updated to describe both primary and fallback test paths.

## Task Description

Follow-up from PYPOST-797. Primary click path is already covered via `QTest.mouseClick` on the
real `+` button. This task adds regression tests for the belt-and-suspenders fallback:
clicks on plus-tab chrome outside the embedded `QPushButton`.

**Scope**

- In scope: unit tests for `_on_tab_bar_clicked` fallback; presenter integration test;
  documentation sync.
- Out of scope: production code changes, macOS manual verification, end-to-end MainWindow
  tests.

## Q&A

- **Q**: Why synthetic `tabBarClicked.emit` instead of `QTest.mouseClick` on chrome?
- **A**: Qt routes clicks on the embedded button to the child widget, not `tabBarClicked`.
  Emitting the signal directly is the reliable way to exercise the fallback handler without
  platform-dependent hit-test geometry.

- **Q**: Is presenter-level coverage required?
- **A**: Yes — the acceptance criterion references both `new_tab_requested` and
  `add_new_tab` behavior; presenter test confirms wiring through `handle_new_tab`.
