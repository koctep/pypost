# PYPOST-516: Add integration test for Body tab line-number gutter in RequestWidget

## Goals

PYPOST-510 added line numbers to `CodeEditor`, which the Body tab already uses. Unit tests
cover `CodeEditor` in isolation; this task closes the gap by verifying the gutter behaves
correctly inside the full `RequestWidget` hierarchy so regressions in tab wiring or layout
cannot slip through.

## User Stories

- As a maintainer, I want an integration test that loads `RequestWidget` and checks the Body
  tab gutter so line-number behaviour is guarded at the widget level users actually see.
- As a developer refactoring the request editor, I want confidence that gutter width and
  read-only behaviour still work when `CodeEditor` is embedded in the Body tab.

## Definition of Done

- Integration test loads `RequestWidget`, navigates to the Body tab, and asserts the body
  editor is a `CodeEditor` with a non-zero gutter width matching viewport margins.
- Test asserts gutter width adapts when line count crosses a digit boundary inside the widget.
- Test asserts clicking the gutter does not modify body text in the integrated hierarchy.
- All new and existing tests pass.

## Task Description

Follow-up from PYPOST-510 tech debt. Scope is test-only: no production code changes unless a
bug is discovered.

**Programming language:** Python (unittest, PySide6 QTest).

**Out of scope:** Script tab gutter, visual screenshot tests, new line-number features.
