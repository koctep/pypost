# PYPOST-399: Add tests for JsonHighlighter

## Context

- **Jira:** PYPOST-399
- **Origin:** Follow-up from [PYPOST-9](https://pypost.atlassian.net/browse/PYPOST-9)
  (`40-tech-debt.md`): unit tests for `JsonHighlighter` were missing.
- **Type:** Debt (Sprint 442 — Test infra & coverage)

## Problem statement

`JsonHighlighter` colors JSON keywords, numbers, strings, object keys, and template
placeholders in request/response editors. PYPOST-124 added placeholder tests; baseline JSON
syntax coverage from PYPOST-103 should be explicit and extended so regressions in keys,
strings, and numbers are caught independently of variable highlighting.

## Goals

- Assert foreground colors for each JSON token class via `QTextLayout` format ranges.
- Cover integer, float, scientific notation, array strings, and escaped string content.
- Keep existing variable-highlight tests; no production code changes unless a test reveals
  a defect.

## Scope

### In scope

- Additional unit tests in `tests/test_json_highlighter.py`.
- Developer doc update listing new test cases.

### Out of scope

- Changing `JsonHighlighter` colors or regex rules.
- Dark-theme color configuration ([PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)).
- Screenshot or GUI integration tests.

## User stories

- As a **developer**, I want automated checks for JSON syntax colors so refactors to
  `JsonHighlighter` do not silently break keyword, number, string, or key highlighting.
- As a **maintainer**, I want tests grouped by token kind so failures pinpoint the broken
  rule quickly.

## Functional requirements

1. **FR-1:** Tests assert `true`/`false`/`null` use darkblue (existing + retained).
2. **FR-2:** Tests assert numeric literals (integer, zero, float, scientific) use blue.
3. **FR-3:** Tests assert quoted string values use green; object keys use purple.
4. **FR-4:** Tests assert array string elements are green (not purple key color).
5. **FR-5:** Tests assert escaped characters inside strings remain green.

## Acceptance criteria

1. **AC-1:** `tests/test_json_highlighter.py` includes dedicated cases for integers,
   zero, and scientific notation.
2. **AC-2:** Array string and escaped-string cases pass under `QT_QPA_PLATFORM=offscreen`.
3. **AC-3:** All tests pass; no change to `json_highlighter.py` unless fixing a proven bug.
4. **AC-4:** `doc/dev/json_syntax_highlighting.md` documents the expanded test list.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | Color names (`darkblue`, `blue`, `green`, `purple`) remain stable until PYPOST-395. |
| **Assumption** | `QTextLayout.formats()` remains the correct assertion API for highlighter ranges. |
| **Risk** | Low: tests are read-only against existing highlighter behavior. |

## Programming language

**Python** — PySide6, pytest + unittest, offscreen Qt platform.
