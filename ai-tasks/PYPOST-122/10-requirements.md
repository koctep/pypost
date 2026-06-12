# PYPOST-122: Optimize VariableAwarePlainTextEdit for large documents

## Context

- **Jira:** PYPOST-122
- **Origin:** Follow-up from [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13)
  (`40-tech-debt.md`): variable hover scanned the entire document on every mouse move.
- **Type:** Debt (Sprint 500)

## Problem statement

When users edit large JSON request bodies with many lines, hovering over `{{variable}}`
placeholders triggers a full-document regex scan on each mouse move. This causes noticeable
lag in the body editor as documents grow.

## Goals

- Keep variable hover tooltips responsive in large multiline editors.
- Preserve existing tooltip behaviour for URL fields, table cells, and small documents.
- Avoid regressions in plain-variable and function-expression hover resolution.

## Scope

### In scope

- Line-scoped expression scan for `VariableAwarePlainTextEdit` (JSON body / CodeEditor).
- Unit tests covering line slicing and hover on a deep line in a large document.
- Developer documentation for the line-scoped scan flag.

### Out of scope

- Recursive variable resolution in tooltips ([PYPOST-123](https://pypost.atlassian.net/browse/PYPOST-123)).
- JsonHighlighter placeholder colours ([PYPOST-124](https://pypost.atlassian.net/browse/PYPOST-124)).
- Caching or incremental document indexing.
- Changes to single-line `VariableAwareLineEdit` behaviour.

## User stories

- As a **user**, I want hover tooltips on `{{variables}}` in a large request body to appear
  without lag so I can inspect templates while editing long JSON payloads.
- As a **user**, I want the same resolved values shown in tooltips as before the
  optimization.

## Functional requirements

1. **FR-1:** Hover over a `{{...}}` token on any line in a multiline body editor shows the
   resolved tooltip value.
2. **FR-2:** Hover over non-placeholder text hides the tooltip (unchanged).
3. **FR-3:** Function expressions (`{{urlencode(db)}}`) on a line still resolve via the
   hover path.
4. **FR-4:** Single-line URL and table-cell hover behaviour is unchanged.

## Non-functional requirements

1. **NFR-1:** Expression lookup for multiline editors scans only the line under the cursor,
   not the full document buffer.
2. **NFR-2:** No new user-visible settings or configuration.

## Definition of Done

- [ ] Line-scoped scan implemented in hover mixin and enabled for `VariableAwarePlainTextEdit`.
- [ ] Existing `tests/test_variable_hover.py` cases pass.
- [ ] New tests cover line slicing and deep-line hover in a large document.
- [ ] `doc/dev/ui_mixins.md` documents the optimization.

## Q&A

- **Q:** Why not scan the full document with a cached index?
  **A:** Out of scope; line-scoped scan is the minimal fix identified in PYPOST-13 tech debt.
