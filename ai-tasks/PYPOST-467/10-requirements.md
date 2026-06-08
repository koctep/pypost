# PYPOST-467: Delete variables from environments

## Goals

Users managing environments in pypost need a clear, reliable way to remove individual
variables they no longer need. Today, variable rows can be edited and new variables
added, but there is no explicit delete action — users must discover that clearing a
variable name removes it. That workflow is easy to miss and leaves stale rows in the
table. This task makes variable deletion an intentional, discoverable part of the
Manage Environments experience.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a user, I want to delete a variable from the current environment so that outdated
  or incorrect entries do not linger in my configuration.
- As a user, I want to right-click a variable row and choose **Delete** so I do not have
  to guess how to remove it.
- As a user, I want deleted variables to disappear from the environment immediately
  and stay removed after I close Manage Environments so my requests use the updated set
  of variables.
- As a user, I want deleting a hidden variable to remove both its value and hidden
  status so no orphaned hidden-key metadata remains.

## Definition of Done

- Right-clicking a populated variable row in Manage Environments shows a context menu
  with **Delete**.
- Choosing **Delete** removes the row from the table and drops the variable from the
  selected environment.
- After deletion, the variable is no longer present in that environment's variable set.
- Deleting a hidden variable also clears its hidden status for that key.
- The trailing empty row used for adding new variables remains available after
  deletion.
- Deletion does not affect other environments or variables in other environments.
- Clearing a variable name continues to remove it from the environment (existing
  alternate path preserved).
- Behaviour is covered by automated tests where the project tests similar UI flows.
- No regressions to adding, editing, renaming, or toggling hidden on remaining
  variables.

## Task Description

Sprint 235 (**Environment Management UX**) targets day-to-day environment workflows.
PYPOST-467 is the first story in that sprint goal: **delete … variables**. It applies
only to the Manage Environments dialog and the currently selected environment's
variable table.

### Example scenario

1. User opens Manage Environments and selects an environment with variables.
2. User right-clicks a variable row and chooses **Delete**.
3. The row disappears; the variable is not used for requests after the dialog closes.
4. Other environments and remaining variables are unchanged.

### Scope

**In scope**

- Deleting individual variable rows from the selected environment in Manage
  Environments via context menu **Delete**.
- Persisting the updated variable set when the user closes Manage Environments (same
  behaviour as today).

**Out of scope**

- Deleting entire environments (separate work: existing Delete button; PYPOST-436 moves
  it to a context menu).
- Reordering variables (PYPOST-466).
- Renaming environments (PYPOST-435).
- Copy cURL / copy from history (PYPOST-468, PYPOST-469).
- Bulk or multi-select delete.

### Constraints and assumptions

- Variables are key/value pairs belonging to one environment at a time.
- Hidden variables are a display/privacy concern; removal must clean up hidden metadata
  for that key.
- Removing a variable must remove its key, value, and hidden status from the selected
  environment, consistent with how other variable edits in that dialog behave today.
- Single-variable delete does not require a confirmation step.

### Main entities (business perspective)

| Entity | Role |
|--------|------|
| **Environment** | Named collection of variables used when sending requests. |
| **Variable** | Named key with a value; may be marked hidden. |
| **Manage Environments dialog** | UI where users select an environment and edit its variables. |

## Non-functional requirements

- Deletion must not regress add, edit, rename, or hidden-toggle behaviour on remaining
  variables.
- Behaviour should be covered by automated UI tests consistent with existing Manage
  Environments tests.

## Q&A

- **Q:** How should the user trigger delete — button per row, context menu, keyboard
  shortcut, or something else?  
  **A:** Context menu on a variable row with a **Delete** action. This matches the
  environment list in the same dialog (context menu already used for **Copy** in
  PYPOST-53) and aligns with delete patterns elsewhere in the app (history entries,
  collections). The trailing add row and blank table areas do not show a delete menu.

- **Q:** Should deletion require a confirmation step?  
  **A:** No. Single-variable delete is immediate, like deleting one history entry.
  Variables are easy to re-add; a confirmation dialog would add friction for a reversible
  edit inside Manage Environments. (Collections use confirmation because deleting
  requests or folders is more destructive — different risk profile.)

- **Q:** Is bulk/multi-row delete required?  
  **A:** No. Out of scope for PYPOST-467; only one variable row is deleted per action.

- **Q:** Does clearing the variable name cell (current implicit behaviour) remain
  valid, or should empty-name rows be rejected?  
  **A:** Yes — clearing the name remains a valid alternate path. The variable is
  removed from the environment when the name is empty, as today. The explicit context
  menu **Delete** is the primary, discoverable path; users who already clear names are
  not broken. Empty-name rows should not block or replace the new delete action.
