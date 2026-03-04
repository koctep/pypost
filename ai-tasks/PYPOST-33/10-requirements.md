# PYPOST-33: Refactoring Technical Debt

## Goals

Eliminate technical debt accumulated in previous development iterations (PYPOST-29, PYPOST-31, PYPOST-32) to improve performance, code readability, and project maintainability.

## User Stories

- As a developer, I want request search to be faster (O(1)) so the application scales with the growth of collections.
- As a developer, I want `HTTPClient` code to be cleaner and split into methods so it's easier to test and maintain.
- As a developer, I want request completion logic in UI not to be duplicated to avoid errors during changes.

## Acceptance Criteria

1. `RequestManager` uses an internal dictionary for request lookup by ID in O(1).
2. `HTTPClient.send_request` method is split into sub-methods (parameter preparation extracted).
3. `MainWindow` has and uses `_reset_tab_state` (or similar) method for clearing tab state after request completion.
4. Existing functionality is not broken (regression testing).

## Task Description

Based on the analysis of technical debt files (`40-tech-debt.md`), the following areas for improvement were identified:

1.  **RequestManager Lookup Optimization (from PYPOST-32)**:
    - Current: Request search iterates through all collections (O(N)).
    - Required: Implement a hash map (dictionary) `id -> (RequestData, Collection)` for fast lookup. The index must be updated on load and save.

2.  **HTTPClient Complexity (from PYPOST-29)**:
    - Current: `send_request` method is overloaded with templating and parameter preparation logic.
    - Required: Extract template rendering and `requests` arguments preparation logic into a separate private method.

3.  **UI Code Duplication (from PYPOST-31)**:
    - Current: `on_request_finished` and `on_request_error` duplicate UI reset code (Send button, worker cleanup).
    - Required: Extract common cleanup code into `_on_request_completed` or `_reset_tab_state` method.

## Q&A

- **Should new tests be added?**
  - It is desirable to verify refactoring with existing manual tests, as automated infrastructure is currently limited. The main focus is on preserving current behavior.

- **Programming Language**: Python.

