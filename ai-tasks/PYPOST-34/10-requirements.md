# PYPOST-34: Add "Save As..." Action for Request Duplication

## Goals

Allow users to take an existing request, adjust it, and save it as a new request entity.
This protects the original request while supporting reuse and faster workflow iteration.

## User Stories

- As a user, I want to open an existing request, modify it, and save it as a new request,
  so I can create variants without changing the original.
- As a user, I want to access `Save As...` from the `Actions` menu before `Save`, so the action
  appears in the expected save-related location.

## Definition of Done

- `Save As...` is available in the `Actions` menu before `Save`.
- `Save As...` is available via shortcut `Ctrl+Shift+S`.
- User can trigger `Save As...` for a request and provide data for a new save.
- The operation always creates a new request entity.
- The original request remains unchanged after `Save As...` completes.
- User can continue working with the newly created request after save.

## Task Description

### Problem Statement

Users need to create modified versions of existing requests. Current workflow does not provide a
clear action to save a modified copy as a new entity.

### Programming Language

Python

### Functional Requirements

- The system must provide a `Save As...` action in the `Actions` menu before `Save`.
- The system must support `Ctrl+Shift+S` as a shortcut to trigger `Save As...`.
- The system must show a dialog to perform saving as a new item when `Save As...` is selected.
- The system must create a new request entity during `Save As...`.
- The system must not overwrite or mutate the source request during `Save As...`.
- The system should keep user flow clear after save by making the new entity available for
  continued work.

### Non-Functional Requirements

- Usability: action location and naming must be clear to users.
- Data safety: original request data must remain intact.
- Consistency: behavior of save as new must be predictable every time.

### Constraints and Assumptions

- Scope is limited to adding and defining behavior of `Save As...` in request workflow.
- Existing `Send` action remains unchanged.
- Existing regular save behavior (if any) is out of scope unless required for consistency.

### System Boundaries (Scope)

- In scope: user-facing action placement, invocation flow, and business behavior for saving a
  modified request as a new entity.
- Out of scope: unrelated request execution behavior, networking behavior, and non-request UI
  areas.

### Main Entities and Interactions

- User: initiates `Save As...` while working with a request.
- Request: source business object being modified.
- New Request Entity: newly created business object produced by `Save As...`.
- Actions Menu: UI access point for user-triggered request actions.

Interaction summary: user edits a request, uses `Actions -> Save As...`, and obtains a separate
new request while the original remains unchanged.

## Q&A

- Q: Why is `Save As...` needed?
  A: User wants to modify a request and save it as a new one.
- Q: Where should the action be placed?
  A: In the `Actions` menu before `Save`.
- Q: What should happen to unsaved changes/source request during `Save As...`?
  A: Changes must be saved only to the new entity; source request must not be overwritten.
