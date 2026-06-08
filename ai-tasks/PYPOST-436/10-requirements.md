# PYPOST-436: Remove Delete button from Environments window and move action to context menu

## Goals

Streamline the Environments window UI by removing the prominent "Delete" button from the main interface and moving the deletion action to a context menu. This will help declutter the UI and reduce the risk of accidental environment deletions.

## User Stories

- As a user managing environments, I want to be able to delete an environment using a context menu (right-click) so that the main interface remains clean and focused on primary actions.
- As a user, I want the deletion process to retain all existing safety checks (confirmations, validations) so that I don't accidentally lose important environment data.

## Definition of Done

- The `Delete` button is no longer visible in the Environments window's main UI.
- Environment deletion action is available and functional from the context menu.
- Deletion behavior (confirmation dialogs, validation, error handling) has no regressions and works exactly as it did before.
- UI tests and documentation are updated if needed.

## Task Description

**Programming Language**: Python

In the Environments window, the current UI includes a `Delete` button for removing environments. This task requires removing that button from the main UI and introducing a context menu (right-click menu) on the environment items that includes the "Delete" action. The underlying deletion logic and safety mechanisms must remain intact.

## Q&A

*(No questions at this time)*