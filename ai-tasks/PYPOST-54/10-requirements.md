# PYPOST-54: Requirements

## Business goal

Decouple `EnvironmentDialog` from presenter-owned environment state so UI edits do not mutate
shared lists by reference.

## User stories

- As a developer, I want the environment manager dialog to work on a copy so the presenter
  controls when changes are committed.
- As a user, I expect the same manage-environments behavior (add, rename, copy, delete,
  variables, MCP toggle) after closing the dialog.

## Acceptance criteria

1. `EnvironmentDialog` deep-copies the incoming environment list and edits the working copy.
2. Dialog exposes the edited list via an `environments` property (or equivalent).
3. `EnvPresenter` assigns presenter state from the dialog result before persisting.
4. Existing Qt-level environment dialog tests pass; input lists are not mutated in place.
5. No regression in hidden-variable logging or persistence flows.

## Out of scope

- Hardcoded UI strings ([PYPOST-55](https://pypost.atlassian.net/browse/PYPOST-55)).
- Additional dialog OK/Cancel buttons (close still commits, matching prior behavior).
