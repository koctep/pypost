# PYPOST-363: Debounce search input on large responses

## Goals

PYPOST-37 added response-body search. Each keystroke runs a full-document scan and match count.
For typical response sizes this is fine; for large payloads (>100KB) rapid typing can feel laggy.
This task adds a short debounce so search work runs after the user pauses typing on large documents.

## Programming Language

Python 3.10+

## User Stories

- As a user searching a large API response, I want typing in the search box to stay responsive so
  I can finish my query without UI stalls on every keystroke.
- As a user searching a small response, I want the match counter to update immediately as today.
- As a user clearing search text, I want the status label to clear right away without delay.

## Definition of Done

- Typed search on large documents (>100KB) is debounced by ~200–300 ms.
- Small documents keep immediate search-on-keystroke behaviour.
- Clearing search input clears the status label immediately.
- Existing ResponseView search tests pass; new tests cover debounce behaviour.
- Developer docs describe debounce scope and interval.

## Task Description

Source: `ai-tasks/PYPOST-37/60-tech-debt.md` — follow-up "Debounce search input".
Jira: [PYPOST-363](https://pypost.atlassian.net/browse/PYPOST-363).

### In Scope

- Debounce `_on_search_text_changed` for large documents only.
- Stop pending debounce when body is cleared or a new response is displayed.
- Tests and dev docs.

### Out of Scope

- Lazy match counting (PYPOST-364 — already done).
- Debouncing Next/Previous navigation or Enter key.
- GUI tests beyond existing `test_response_view_search.py` patterns.

### Constraints and Assumptions

- Large-document threshold matches existing `LARGE_DOC_CHAR_THRESHOLD` (100KB).
- Debounce interval 250 ms (within 200–300 ms range).
- Same `QTimer` single-shot pattern as `ValidationController` and `FoldController`.

## Functional Requirements

- FR-1: On large documents, each text or case-sensitivity change restarts a single-shot timer;
  search runs when the timer fires.
- FR-2: On small documents, search runs immediately on text or case-sensitivity change.
- FR-3: Empty query clears status immediately without waiting for debounce.
- FR-4: `clear_body()` and `display_response()` cancel any pending debounced search.

## Non-functional Requirements

- **Responsiveness:** Avoid redundant full-document scans while the user is still typing on
  large bodies.
- **Compatibility:** No change to metrics source labels or navigation shortcuts.

## Stakeholder Approval

Approved via sprint-task-runner autonomous mode (2026-06-11).
