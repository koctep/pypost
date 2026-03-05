# PYPOST-36: Add Rename Action to Context Menu

## Goals

Allow users to rename items in the tree directly from the context menu so item names can be kept
clear and up to date during daily work.

## User Stories

- As an API user, I want to rename any tree item from the context menu so I can keep my workspace
  organized.
- As an API user, I want to rename the selected item inline so the action is quick and does not
  interrupt my flow.

## Definition of Done

- Every tree item supports a context menu action named `Rename`.
- Renaming is available for all tree item types in scope.
- Renaming is performed inline in the tree.
- Empty names are rejected and cannot be saved.
- Duplicate names under the same parent are allowed.

## Task Description

### Problem Statement

Users need the ability to rename tree items. Without it, they cannot maintain meaningful names in
the interface.

### Programming Language

Python

### Functional Requirements

- The system must provide a `Rename` action in the context menu for every tree item.
- The system must allow renaming of all tree item types.
- The system must start rename in inline edit mode.
- The system must reject empty names.
- The system must allow duplicate names under the same parent.

### Non-Functional Requirements

- UX speed: rename should be fast and low-friction.
- UX consistency: rename behavior should be the same for all tree item types.
- Data quality: item names must never be saved as empty.

### Constraints and Assumptions

- Scope is limited to renaming through the tree item context menu.
- No additional validation constraints were provided beyond non-empty names.
- No role-based restrictions were provided for rename.

### System Boundaries (Scope)

- In scope: context menu rename action for all tree items, inline rename flow, non-empty name
  validation.
- Out of scope: unrelated item management features and non-context-menu rename flows.

### Main Entities and Interactions

- User: starts and confirms/cancels rename.
- Tree item: business object being renamed.
- Tree view: interaction surface where inline rename is performed.

Interaction summary: user opens context menu for a tree item, chooses `Rename`, edits the name
inline, then applies or cancels the rename.

## Q&A

- Q: Why is this task needed?
  A: Users need the ability to rename items.
- Q: Which items are in scope?
  A: All tree items.
- Q: How should rename be performed?
  A: Inline in the tree.
- Q: What validation is required?
  A: Empty names are prohibited.
- Q: Are duplicate names allowed under the same parent?
  A: Yes.
