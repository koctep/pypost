# PYPOST-354: Deduplicate search navigation metrics/logging

## Goals

`_find_next` and `_find_previous` in `ResponseView` repeat the same metrics emission and debug
logging after each navigation action. Extract a shared helper so behaviour stays identical and
future observability changes happen in one place.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want search navigation metrics and logging defined once so Next/Previous/Enter
  cannot drift apart.
- As a user, I want search navigation to behave exactly as before (counter, metrics, logs).

## Definition of Done

- `_find_next` and `_find_previous` share a helper for post-find metrics and logging.
- Empty-query guard is not duplicated between the two methods.
- Existing `tests/test_response_view_search.py` and integration tests pass unchanged.
- Developer docs mention the new helper.

## Task Description

Source: `ai-tasks/PYPOST-37/60-tech-debt.md` — "Duplicate search nav logging".
Jira: [PYPOST-354](https://pypost.atlassian.net/browse/PYPOST-354).

### In Scope

- Refactor `pypost/ui/widgets/response_view.py` only.
- Update `doc/dev/response_search.md`.

### Out of Scope

- Changing metrics labels, log format, or navigation semantics.
- New tests (existing coverage is sufficient for a pure refactor).

### Constraints and Assumptions

- `_on_search_text_changed` keeps its own typed-search metrics/logging (different log message).
- No user-visible behaviour change.

## Functional Requirements

- FR-1: Next, Previous, and Enter still call `track_gui_response_search_action` with the same
  `source` and `has_matches` values as before.
- FR-2: DEBUG log `response_search_find source=%s matches=%d` still emitted per navigation.
- FR-3: Empty search query still clears the status label and skips find.

## Non-functional Requirements

- **Maintainability:** Single helper for navigation observability.
- **Compatibility:** No API or UI changes.

## Stakeholder Approval

Approved via sprint-task-runner autonomous mode (2026-06-11).
