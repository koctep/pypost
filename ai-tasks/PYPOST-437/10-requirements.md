# PYPOST-437: Add "Hidden" Checkbox for Variables

## Goals

Improve security posture by allowing users to mark environment variables as hidden,
masking their values in the UI to prevent accidental exposure of secrets (API keys,
tokens, passwords).

## Programming Language

Python

## User Stories

- As a user, I want to mark a variable as "hidden" so its value is masked in the
  variables list, preventing shoulder-surfing or accidental screen-sharing exposure.
- As a user, I want hidden variables to not show their real values in hover previews
  (tooltips), so secrets are protected during normal request editing.
- As a user, I want to uncheck "hidden" to reveal the value again, so I can verify or
  edit it when needed.
- As a user, I want the hidden flag to persist across sessions, so I do not need to
  re-mark variables every time I open the application.

## Definition of Done

1. A "Hidden" checkbox column exists in the variable table within the Environment
   Manager dialog.
2. When a variable is marked hidden, its value is masked with asterisks (`********`)
   in the variables list view.
3. Hidden variables show masked values (not real values) in hover tooltips / previews.
4. When the "Hidden" checkbox is unchecked, the real value is shown again immediately.
5. When the "Hidden" checkbox is checked, the variable is explicitly marked as hidden
   (persisted in the Environment model).
6. The hidden flag state is saved and restored correctly across application restarts.
7. Cloning an environment preserves the hidden flags of its variables.
8. Existing environments without hidden flags load without errors (backward
   compatibility).
9. Tests cover all new behavior.

## Task Description

### Problem Statement

Environment variables may contain sensitive values (API keys, tokens, passwords). The
current UI displays all variable values in plain text in the Environment Manager dialog
and in hover tooltips. This creates a risk of accidental exposure during screen sharing,
pair programming, or casual shoulder-surfing.

### Scope

- In scope:
  - Add `hidden_keys: Set[str]` field to the `Environment` model.
  - Add a "Hidden" checkbox column to the variables table in `EnvironmentDialog`.
  - Mask hidden variable values with `********` in the variables list view.
  - Mask hidden variable values in hover tooltips (`VariableHoverHelper`).
  - Update `clone_environment` to copy `hidden_keys`.
  - Persist the flag via existing JSON serialization (Pydantic).
  - Update existing tests and add new tests.
- Out of scope:
  - Encryption of hidden variable values at rest.
  - Password-protected reveal of hidden variables.
  - Changes to template rendering or HTTP request execution (hidden is a display
    concern only; actual values are still substituted into requests).
  - Changes to post-script variable access.

### Constraints and Assumptions

- Constraint: `variables: Dict[str, str]` must remain unchanged to avoid breaking
  existing code that reads variables for template rendering, HTTP requests, and scripts.
- Constraint: backward-compatible with existing `environments.json` files that do not
  contain `hidden_keys`.
- Constraint: maximum line length 100 characters (project rule).
- Assumption: the hidden flag is a UI/display concern only. The actual variable value
  is always available for template substitution at runtime.
- Assumption: primary impacted users are developers who store sensitive values in
  environment variables.

### Main Business Entities and Interactions

- **Environment**: model that stores variables and the new `hidden_keys` set.
- **EnvironmentDialog**: UI dialog where users manage variables and toggle the hidden
  checkbox.
- **VariableHoverHelper**: utility that resolves variable values for hover tooltips.
- **EnvPresenter**: presenter that propagates variable data (and now hidden keys) to
  downstream widgets.

Interaction flow:
1. User opens Environment Manager and sees a 3-column table: Variable, Value, Hidden.
2. User checks the "Hidden" checkbox for a variable.
3. The value column immediately shows `********` instead of the real value.
4. When hovering over `{{ variable }}` in request fields, the tooltip shows `********`.
5. User unchecks "Hidden" — the real value is shown again in both places.
6. On dialog close, the hidden state is persisted to `environments.json`.

## Non-Functional Requirements

- Backward compatibility: old environment files without `hidden_keys` must load without
  errors.
- Consistency: masked display must be identical in the table and in hover tooltips.
- Performance: no measurable impact (set membership check is O(1)).
- Stability: no regression in existing variable, environment, or request behavior.

## Q&A

- Q: Should hidden variables be encrypted at rest?
  - A: No, out of scope. This is a display-level protection only.
- Q: Should the value be editable while hidden?
  - A: The value column shows `********` in the table. Editing still works on the
    underlying real value. When a user edits a hidden variable's value cell, they type
    the new value; on commit the real value is updated.
- Q: Does the hidden flag affect template substitution?
  - A: No. Template rendering uses the actual value regardless of the hidden flag.
- Q: What mask string to use?
  - A: `********` (8 asterisks), consistent regardless of actual value length.
