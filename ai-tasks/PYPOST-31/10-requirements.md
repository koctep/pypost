# PYPOST-31: Consolidate Save Action into Actions Menu Near Send

## Goals

Improve the main screen user interface by reducing button clutter near the request execution
area and preparing the UI for action list growth in one consistent place.

## Programming Language

Python

## User Stories

- As a user of the main screen, I want to access `Save` from an actions menu next to `Send` so the
  action area is more compact and consistent.
- As a user of the main screen, I want the `Save` action behavior to remain unchanged so my current
  workflow is preserved.
- As a keyboard user, I want `Save` to remain reachable through keyboard navigation and shortcuts so
  accessibility and speed are not degraded.

## Definition of Done

1. On the main screen, there is no standalone `Save` button to the left of `Send`.
2. On the main screen, an actions control is placed to the right of `Send`.
3. The actions control opens a list that currently contains one action: `Save`.
4. Triggering `Save` from the actions list performs the same user-visible flow and result as the
   previous standalone `Save` button.
5. Keyboard accessibility and existing `Save` shortcuts/navigation behavior are preserved.

## Task Description

### Problem Statement

The current main screen action area contains a standalone `Save` button near `Send`. The interface
should be simplified and aligned with a menu-based action model.

### Scope

- In scope:
  - Main screen request action area.
  - Relocation of `Save` from standalone button to actions menu near `Send`.
  - Preservation of existing `Save` user behavior.
  - Preservation of keyboard accessibility and shortcuts for `Save`.
- Out of scope:
  - Other screens and contexts outside the main screen.
  - Changes to business logic of saving.
  - Adding new actions beyond `Save` in this task.

### Constraints and Assumptions

- Constraint: Only main screen UI is affected.
- Constraint: No behavior change for save operation.
- Assumption: Existing users rely on current save flow and keyboard usage; this must remain intact.

### Main Business Entities and Interactions

- User: initiates request-related actions on the main screen.
- Main Screen Action Area: exposes request actions to the user.
- Action Menu: grouped entry point for available actions near `Send`.
- Save Action: persists current request state using the existing business flow.

Interaction flow:
1. User opens actions menu near `Send`.
2. User selects `Save`.
3. System executes the same save outcome as before.

## Non-Functional Requirements

- Usability: action controls are clear and discoverable on the main screen.
- Consistency: action placement is consistent with a menu-based model.
- Accessibility: keyboard navigation and shortcut behavior for `Save` remain available.

## Q&A

- Q: Why is this change needed?
  - A: To improve the user interface by reducing clutter and moving to an expandable actions list.
- Q: Where should the change be applied?
  - A: Only on the main screen.
- Q: Should `Save` behavior change?
  - A: No. It must remain the same.
- Q: Should keyboard support be preserved?
  - A: Yes.
