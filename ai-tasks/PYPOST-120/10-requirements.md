# PYPOST-120: Optimize variable hover search to scan only current line on mouse move

## Context

- **Jira:** PYPOST-120
- **Origin:** [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13) `40-tech-debt.md`
- **Implementation:** [PYPOST-122](https://pypost.atlassian.net/browse/PYPOST-122)

## Problem statement

Variable hover scanned the full `QPlainTextEdit` buffer on each `mouseMoveEvent`, causing lag
in large JSON bodies.

## Goals

- Responsive hover tooltips in large multiline editors.
- Unchanged behaviour for URL fields and table cells.

## User stories

- As a **user**, I want hover tooltips on `{{variables}}` in large bodies without lag.
- As a **user**, I want the same resolved tooltip values as before.

## Functional requirements

1. **FR-1:** Hover on any line shows resolved tooltip.
2. **FR-2:** Non-placeholder hover hides tooltip.
3. **FR-3:** Function expressions still resolve.
4. **FR-4:** Single-line URL and table hover unchanged.

## Non-functional requirements

1. **NFR-1:** Multiline editors scan only the line under the cursor.
2. **NFR-2:** No new user-visible settings.

## Definition of Done

- [x] Line-scoped scan enabled for `VariableAwarePlainTextEdit`.
- [x] Tests cover slice helper and deep-line hover.
- [x] `doc/dev/ui_mixins.md` documents the optimization.
