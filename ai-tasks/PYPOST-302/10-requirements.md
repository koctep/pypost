# PYPOST-302: Refactor Tab Action Controls into Dedicated Tab-Header Component

## Goals

Improve maintainability of the request-tab UI by isolating tab-bar chrome (close buttons,
trailing new-tab control, and label updates) from tab business logic. This reduces presenter
complexity and prepares for future tab-bar enhancements without touching request workflows.

## Programming Language

Python

## User Stories

- As a **developer**, I want tab-bar controls in a dedicated component so I can change tab
  chrome without editing request save/send logic.
- As a **user**, I want existing tab behavior unchanged: close tabs, rename labels from
  collections, and create tabs via `+` or `Ctrl+N`.

## Definition of Done

1. Tab-bar chrome (plus placeholder tab, close affordance setup, label helper) lives in a
   dedicated `RequestTabHeader` component under `pypost/ui/widgets/`.
2. `TabsPresenter` delegates plus-tab, close-guard, navigation-skip, and label-update calls to
   the header component.
3. Existing plus-tab, close, rename, and navigation behavior is unchanged (regression tests pass).
4. Developer documentation describes the new component and its relationship to `TabsPresenter`.

## Task Description

### Problem Statement

Tab action controls were embedded in `TabsPresenter` after PYPOST-293 moved them out of
`MainWindow`. The presenter still mixes tab-bar UI mechanics with request lifecycle logic,
making both harder to test and evolve.

### Scope

- In scope:
  - Extract tab-header controls into `RequestTabHeader`.
  - Wire `TabsPresenter` to the new component.
  - Unit tests for the header; keep presenter integration tests green.
  - Update dev docs.
- Out of scope:
  - Changing new-tab, close, or rename business rules.
  - MainWindow layout changes beyond existing delegation.
  - New metrics or UI redesign.

### Constraints and Assumptions

- Constraint: Behavior parity with PYPOST-293 plus-tab implementation.
- Constraint: `PLUS_TAB_MARKER` remains the plus-tab discriminator.
- Assumption: `TabsPresenter` continues to own request tabs and orchestration.

### Main Business Entities and Interactions

- **Request tab bar**: shows request tabs, close buttons, and trailing `+` control.
- **Tabs presenter**: opens/closes request tabs and syncs labels after collection renames.
- **User**: closes tabs, creates tabs, sees renamed labels after collection edits.

## Non-Functional Requirements

- **Maintainability**: tab-bar code isolated in one module.
- **Stability**: no regression in tab UX.
- **Testability**: header unit-testable without request managers.

## Q&A

- Q: Why extract from `TabsPresenter` instead of `MainWindow`?
  - A: PYPOST-293 already moved tab UI to the presenter; this task completes the decomposition
    with a dedicated header component.
- Q: Does rename logic move entirely?
  - A: Label text updates go through the header; request-id matching stays in the presenter.
