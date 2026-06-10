# PYPOST-435: Rename Environment

## Goals

Allow users to rename their existing environments in the application. This provides flexibility, enabling users to correct typos or update environment names to better reflect their purpose (e.g., from "dev" to "staging").

## User Stories

- As a user, I want to be able to rename an environment by right-clicking it in the list and selecting "Rename" from the context menu, so I can easily update its name.
- As a user, I want to be able to rename an environment by selecting it and pressing the F2 hotkey, for a faster, keyboard-driven workflow.
- As a user, I expect the new environment name to be saved and applied consistently across the application.

## Definition of Done

- The environment context menu includes a "Rename" action.
- Pressing the F2 hotkey while an environment is selected triggers the rename flow.
- The rename flow allows the user to input a new name.
- The new name is applied consistently and saved.
- All references to the environment name in the UI are updated immediately.
- Checks/tests pass without regressions.

## Task Description

**Programming Language**: Python

The application currently allows creating, duplicating, and deleting environments in the Environment Manager dialog, but lacks a direct way to rename an existing environment. This task introduces a rename flow for environments. The flow must be accessible via two methods:
1. A "Rename" option in the context menu of the environment list.
2. The `F2` keyboard shortcut when an environment is selected.

When the rename action is triggered, the user should be prompted to enter a new name. The system must validate the input (e.g., preventing empty names or duplicates) and then update the environment's name consistently.

## Q&A

- **Q**: The task description mentions "Rename `environment` to a clearer, consistent name across code, configs, and docs." Does this mean we are renaming the actual concept/entity of "environment" in the codebase to a different word (like "workspace"), or does it mean we are implementing the UI feature to let users rename their created environments, and the new name they choose should be saved consistently?
  - **A**: We are ONLY adding a UI feature to let users rename their environments (via F2/context menu).
