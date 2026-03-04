# PYPOST-35: Add New-Tab Plus Button Next to Tabs

## Goals

Improve user experience by making tab creation more discoverable through a dedicated `+` button in
the tab bar.

## Programming Language

Python

## User Stories

- As a user, I want to see a `+` button next to tabs so I can quickly discover how to create a new
  tab.
- As a user, I want clicking the `+` button to behave exactly like `Ctrl+N` so tab creation is
  consistent across mouse and keyboard flows.

## Definition of Done

1. A `+` button is visible in the tab area, positioned immediately to the right of the last tab.
2. Clicking the `+` button triggers the same user-visible behavior as `Ctrl+N`.
3. Existing `Ctrl+N` behavior remains unchanged.
4. Existing tab behavior (open/select/close current tabs) remains unchanged by this task.

## Task Description

### Problem Statement

Creating a new tab is currently less discoverable in the tab interface, which negatively impacts UX.

### Scope

- In scope:
  - Add a `+` button in the tab area.
  - Position it right of the last tab.
  - Ensure it performs the same action as `Ctrl+N`.
- Out of scope:
  - Changes to the business behavior of tab creation.
  - Redesign of the overall tab system.
  - Any change unrelated to new-tab entry point UX.

### Constraints and Assumptions

- Constraint: The `+` button action must be behaviorally equivalent to `Ctrl+N`.
- Constraint: Existing new-tab shortcut behavior must be preserved.
- Assumption: Primary impacted role is a general application user.

### Main Business Entities and Interactions

- User: interacts with tabs and creates new tabs.
- Tab Bar: area where existing tabs and tab actions are shown.
- New Tab Action: business action that creates a new tab session.

Interaction flow:
1. User clicks the `+` button in the tab bar.
2. System executes the same business action as `Ctrl+N`.
3. User gets the same outcome as keyboard-based new-tab creation.

## Non-Functional Requirements

- Usability: the new-tab action is easy to find in the tab area.
- Consistency: mouse-triggered `+` and keyboard-triggered `Ctrl+N` produce the same result.
- Stability: no regression in existing tab usage behavior.

## Q&A

- Q: What should be changed?
  - A: Add a `+` button next to tabs.
- Q: Where should the button be placed?
  - A: Immediately to the right of the last tab.
- Q: What should happen on click?
  - A: It should perform the same action as `Ctrl+N`.
- Q: Why is this needed?
  - A: To improve UX.
- Q: Who is the primary user?
  - A: User.
