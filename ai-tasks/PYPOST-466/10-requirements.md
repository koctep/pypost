# PYPOST-466: Manual variables order

## Goals

Users managing environments in pypost often work with many variables at once. The order
variables appear in Manage Environments affects how quickly they can scan, compare, and
maintain related keys (for example, grouping auth tokens with their base URLs). Today,
variables appear in an order the user cannot control after creation — the only workaround
is to delete and re-enter variables in the desired sequence. Sprint 235 targets
day-to-day environment workflows; **reorder variables** is an explicit sprint goal.
This task makes variable order a deliberate, user-controlled part of the Manage
Environments experience.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a user, I want to change the order of variables in the current environment so that
  related or important keys appear where I expect them in the table.
- As a user, I want reordered variables to stay in that order when I switch to another
  environment and back so I do not lose my arrangement mid-session.
- As a user, I want the order I set to remain after I close Manage Environments and open
  it again so my environments stay organized over time.
- As a user, I want reordering to move the whole variable — name, value, and hidden
  status — together so nothing is split or reset when I rearrange rows.
- As a user, I want the empty row for adding a new variable to remain at the bottom of
  the table after I reorder so adding variables still works as today.

## Definition of Done

- The user can manually change the relative order of two or more populated variable rows
  in Manage Environments for the selected environment.
- After a reorder, the table reflects the new order immediately.
- Switching to another environment and returning shows variables in the updated order.
- Closing Manage Environments and reopening later shows the same order for that
  environment.
- Reordering preserves each variable's key, value, and hidden status.
- The trailing empty add row stays last; it is not treated as a reorderable variable.
- Reordering does not affect variables in other environments.
- No regressions to adding, editing, deleting, or toggling hidden on variables.
- Behaviour is covered by automated tests where the project tests similar Manage
  Environments flows.

## Task Description

Sprint 235 (**Environment Management UX**) includes delete variables (PYPOST-467, done),
rename environments (PYPOST-435), Copy cURL (PYPOST-468, done), and copy from history
(PYPOST-469). PYPOST-466 is the **reorder variables** story in that sprint goal. It
applies only to the Manage Environments dialog and the currently selected environment's
variable table.

### Example scenario

1. User opens Manage Environments and selects an environment with several variables.
2. User rearranges two variables so a frequently used key appears above others.
3. The table updates; values and hidden flags are unchanged.
4. User switches environment, returns, and later closes the dialog — order is kept.

### Scope

**In scope**

- Manually changing display order of populated variable rows in the selected environment
  in Manage Environments.
- Persisting the updated order when the user closes Manage Environments (same persistence
  model as other variable edits today).

**Out of scope**

- Sorting variables automatically (alphabetical, by key length, etc.).
- Reordering environments in the environment list.
- Reordering request params, headers, or other tables outside Manage Environments.
- Bulk reorder or multi-select move.
- Deleting variables (PYPOST-467), renaming environments (PYPOST-435), Copy cURL
  (PYPOST-468), copy from history (PYPOST-469).

### Constraints and assumptions

- Variables are key/value pairs belonging to one environment; order is meaningful only
  within that environment's variable list in Manage Environments.
- Hidden variables remain hidden after reorder; masked display must not leak values.
- Reordering must not create duplicate keys or drop variables.
- The add row (empty key) is not a variable and must remain at the bottom.
- Order is a presentation concern for the environment editor; variable substitution for
  requests does not depend on display order (keys are looked up by name).

### Main entities (business perspective)

| Entity | Role |
|--------|------|
| **Environment** | Named collection of variables used when sending requests. |
| **Variable** | Named key with a value; may be marked hidden; has a position in the environment's list. |
| **Manage Environments dialog** | UI where users select an environment and edit its variables. |

## Non-functional requirements

- Reordering must not regress add, edit, delete, or hidden-toggle behaviour on remaining
  variables.
- Behaviour should be covered by automated UI tests consistent with existing Manage
  Environments tests.
- Reorder actions should feel immediate (no perceptible lag for typical environment
  sizes).

## Q&A

- **Q:** Why does variable order matter if requests resolve variables by key name?  
  **A:** Order affects scanability and maintenance in Manage Environments. Users with
  long lists want a stable, intentional layout — not a workaround of delete-and-re-add.

- **Q:** How should the user trigger reorder — drag-and-drop, toolbar buttons, context
  menu, keyboard shortcuts?  
  **A:** Not fixed in this requirements phase. The business need is *manual* control
  over order; the implementation step will choose a discoverable interaction consistent
  with existing Manage Environments patterns (context menus, table editing).

- **Q:** Should reorder require confirmation?  
  **A:** No. Reordering is a reversible layout change inside Manage Environments, similar
  in risk to editing a value.

- **Q:** Is multi-row or bulk reorder required?  
  **A:** No. Moving one variable at a time relative to its neighbours is sufficient for
  this story.

- **Q:** Does reorder apply when copying an environment?  
  **A:** A copied environment should start with the same variable order as the source at
  copy time (inherits whatever order the source had). No separate reorder UI is required
  for the copy action itself.

- **Q:** Jira has no description for PYPOST-466 — what is the source of truth?  
  **A:** Sprint 235 goal ("reorder variables"), issue title ("Manual variables order"),
  and explicit deferral in PYPOST-467 scope. Assumptions above are documented for review.
