# PYPOST-29: Technical Debt Refactoring (Managers & Mixins)

## Goals

The main goal is to eliminate technical debt accumulated during development (PYPOST-8, PYPOST-9, PYPOST-14) by decomposing `MainWindow` and reducing code duplication.
This will improve code maintainability, testability, and simplify future feature development.

## User Stories

- **As a developer**, I want request handling logic to be extracted into a separate `RequestManager` service so I don't have to search for it inside the huge `MainWindow` class.
- **As a developer**, I want UI state persistence (`expanded_collections`, `open_tabs`) to be managed by a separate `StateManager` component to offload UI code.
- **As a developer**, I want common variable tooltip logic to be extracted into a mixin to avoid code duplication across different widgets.

## Acceptance Criteria

- [ ] `RequestManager` class is created and used for request search and persistence.
- [ ] `StateManager` class is created and used for UI state management.
- [ ] `VariableHoverMixin` is created and applied to `VariableAwareLineEdit`, `VariableAwarePlainTextEdit`, `VariableAwareTableWidget`.
- [ ] Logic is removed from `MainWindow` and delegated to new managers.
- [ ] Application functions identically (regression testing):
    - Collection tree preserves state (collapsed/expanded).
    - Tabs are restored.
    - Requests are saved and updated correctly.
    - Variable tooltips work in all widgets.
- [ ] Linter reports no new errors.

## Task Description

Refactoring is required in three areas:
1.  **Request Management**: Extract request search by ID logic (currently iterative search in UI) and request saving into `RequestManager` class.
2.  **UI State Persistence**: Extract tree and tab state saving/loading logic into `StateManager`, removing direct UI dependency on settings structure.
3.  **Widget Duplication**: Eliminate `mouseMoveEvent` and variable search logic duplication in editor widgets by extracting it into a mixin.

### Current Issues (from Tech Debt)
- `MainWindow` is overloaded with responsibilities.
- Request search has O(N) complexity and is implemented "in place".
- Code duplication in `VariableAware*` widgets.
- Direct settings manipulation from UI methods.

## Q&A

- **Is a request index needed for O(1) search?**
  - For now, search encapsulation is sufficient. Optimization (index) can be added inside `RequestManager` later without changing external API if performance becomes an issue. The architectural separation is what's important now.

