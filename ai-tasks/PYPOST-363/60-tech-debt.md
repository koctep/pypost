# PYPOST-363: Technical Debt Analysis

## Shortcuts Taken

- None. Debounce reuses established `QTimer` single-shot pattern from editor controllers.

## Code Quality Issues

- None introduced.

## Missing Tests

- No test for debounced case-sensitivity toggle on large documents (low risk; same code path as
  text change).

## Performance Concerns

- **Resolved:** Keystroke-driven full scans on large documents are debounced (addresses
  PYPOST-37/PYPOST-359 follow-up).

## Hardcoded Values

- `SEARCH_DEBOUNCE_MS = 250` — documented in dev docs and architecture.

## Follow-ups

- None required for task closure.

## Blocker Review

**SAFE TO CLOSE**
