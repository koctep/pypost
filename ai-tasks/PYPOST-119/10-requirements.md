# PYPOST-119: Review mouseMoveEvent regex search performance

## Context

- **Jira:** PYPOST-119
- **Origin:** Follow-up from [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13)
  (`40-tech-debt.md`): variable hover runs regex on every `mouseMoveEvent`; full-buffer scans
  may matter for large body text.
- **Related:** [PYPOST-122](https://pypost.atlassian.net/browse/PYPOST-122) (line-scoped scan),
  [PYPOST-132](https://pypost.atlassian.net/browse/PYPOST-132) (table cell cache).
- **Type:** Debt (Sprint 502)

## Problem statement

Variable hover tooltips call expression lookup on each pointer move. For large request bodies
and rapid pointer movement, redundant regex scans and resolution work can cause UI lag even
when the cursor stays on the same token.

## Goals

- Review all variable-hover `mouseMoveEvent` paths and confirm mitigations are in place.
- Reduce redundant regex and resolution work when the pointer moves without changing the
  scanned text position.
- Preserve existing tooltip content and behaviour across URL, body, and table widgets.

## Scope

### In scope

- Performance review of `VariableHoverMixin`, `VariableAwarePlainTextEdit`,
  `VariableAwareLineEdit`, and `VariableAwareTableWidget` hover paths.
- Scan-position cache on `VariableHoverMixin` when prior mitigations do not cover repeated
  moves at the same index.
- Unit tests for repeated moves on text widgets.
- Developer documentation of the hover performance strategy.

### Out of scope

- Full-document indexing or incremental parse caches.
- Recursive tooltip resolution ([PYPOST-123](https://pypost.atlassian.net/browse/PYPOST-123)).
- UI automation for tooltip appearance ([PYPOST-131](https://pypost.atlassian.net/browse/PYPOST-131)).
- Changes to `JsonHighlighter` placeholder colours.

## User stories

- As a **user**, I want hover tooltips to stay responsive while I move the mouse over
  `{{variables}}` in long JSON bodies so editing large templates does not stutter.
- As a **user**, I want the same resolved tooltip values as before when hovering placeholders
  in URL fields, body editors, and tables.

## Functional requirements

1. **FR-1:** Hover over `{{...}}` tokens in URL, body, and table widgets still shows the
   resolved tooltip.
2. **FR-2:** Hover over non-placeholder text still hides the tooltip.
3. **FR-3:** Function expressions (`{{urlencode(db)}}`) still resolve via the hover path.
4. **FR-4:** Line-scoped scan for multiline editors and table cell cache remain unchanged.

## Non-functional requirements

1. **NFR-1:** Multiline editors must not scan the full document buffer on each move
   (line-scoped scan).
2. **NFR-2:** Repeated moves at the same scanned text index must not repeat expression lookup
   or resolution.
3. **NFR-3:** Caches invalidate when environment variables or hidden keys change.
4. **NFR-4:** No new user-visible settings or configuration.

## Definition of Done

- [ ] Hover performance review documented with per-widget mitigations.
- [ ] Mixin scan cache implemented and tested.
- [ ] Existing `tests/test_variable_hover.py` cases pass.
- [ ] `doc/dev/ui_mixins.md` documents the performance strategy.

## Q&A

- **Q:** Is line-scoped scan enough for large documents?
  **A:** It bounds scan size to one line; a position cache avoids re-scanning that line on
  every move while the cursor stays on the same index.
