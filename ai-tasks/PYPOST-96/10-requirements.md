# PYPOST-96: Close debt — consider debouncing settings saving

## Goals

PYPOST-10 noted that frequent UI interactions could cause excess settings-file I/O if every
toggle wrote synchronously to disk. This follow-up debt item asked to revisit debouncing when
I/O performance becomes a concern.

The business goal is to keep the desktop app responsive during rapid tree/tab interactions and
avoid unnecessary disk writes without losing the user's final session state after restart.

**Programming language:** Python (PySide6).

## User Stories

- As a user, I want to expand and collapse collections quickly without the app stuttering from
  repeated disk writes.
- As a user, I want my last tree/tab state to persist after a normal quit.
- As a maintainer, I want a clear decision on whether debouncing is already in place or still
  needed, so duplicate debt tickets do not linger.

## Definition of Done

1. Confirm whether settings persistence for high-frequency UI changes is already debounced.
2. If covered by prior work (PYPOST-386 / PYPOST-90), document the decision and close this
   ticket without new implementation.
3. If not covered, implement debouncing — not required when verification shows existing
   `StateManager` debounce (300 ms) and tests.
4. Source tech-debt entry in PYPOST-10 updated to FIXED with cross-references.
5. Developer documentation links this closure.

## Task Description

### Problem

Original PYPOST-10 tech debt: "Consider debouncing settings saving if I/O performance issues
arise." This is a sibling of the synchronous-save item closed in
[PYPOST-90](https://pypost.atlassian.net/browse/PYPOST-90); implementation landed in
[PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386).

### Scope

**In scope**

- Verify current save behavior for tree expand/collapse, tabs, and session fields.
- Decide close-with-docs vs extend implementation.
- Update PYPOST-10 debt tracker and dev docs.

**Out of scope**

- Settings dialog OK path (immediate save on explicit confirm).
- Partial JSON writes or settings file splitting.
- User-configurable debounce interval.

## Q&A

- **Q:** Does PYPOST-386 already cover this? **A:** Yes — `StateManager` debounces UI session
  fields at 300 ms; `flush_pending_save()` runs on exit.
- **Q:** Why a separate PYPOST-96 ticket? **A:** PYPOST-10 listed it as a conditional
  follow-up; PYPOST-90 closed the synchronous-save wording. PYPOST-96 closes the "consider
  debouncing" line explicitly.
- **Q:** Is new code required? **A:** No — verification only.
