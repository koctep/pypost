# PYPOST-478: Centralize environment variable name validation

## Goals

PYPOST-163 introduced validation when users create new environment variable names so names
work reliably in Jinja2 templates used across requests. That validation currently lives in
one UI flow. As more entry points may need the same checks (other UI flows, programmatic
creation, automated tests), duplicating the rules would risk inconsistent enforcement and
harder maintenance.

This task establishes a single, reusable place for variable-name validation so every
caller applies the same Jinja2-compatible rules and user-facing error messages. End-user
behavior for creating variables today must not change; the goal is consistency and
maintainability for current and future callers.

## Programming Language

Python 3.10+

## User Stories

- As a user creating a new environment variable, I want invalid names rejected with the
  same clear messages as today so I am not surprised by different rules in different
  parts of the app.
- As a maintainer, I want one authoritative definition of valid variable names so new
  features do not reimplement or drift from existing rules.
- As a maintainer adding tests for variable naming, I want to verify validation rules
  without depending on UI presentation code so tests stay focused and reliable.

## Definition of Done

- Variable name validation rules from PYPOST-163 are available through a single
  authoritative capability invoked by all creation entry points and automated tests.
- The existing "new variable" creation flow continues to enforce the same rules and show
  the same error messages as before this change.
- No duplicate copies of the validation rule logic remain where new-variable creation
  was handled previously.
- Developer documentation for variable validation reflects that rules are centralized
  (updated in a later step if needed).
- Behaviour is ready for dedicated unit-test coverage in follow-up work (PYPOST-477).

## Task Description

Technical debt follow-up from PYPOST-163. Validation currently enforces Jinja2-compatible
variable names when users create variables via the response view context menu. The rules are documented in project developer documentation for variable validation:

1. Name cannot be empty (after trimming whitespace in the UI flow).
2. First character must be a letter or underscore (cannot start with a digit).
3. Remaining characters must be letters, digits, or underscores only.

Invalid names produce these user-facing messages:

- "Variable name cannot be empty."
- "Variable name cannot start with a digit."
- "Variable name can only contain letters, numbers, and underscores."

### In Scope

- Establish one authoritative validation capability for all callers.
- Ensure the existing new-variable creation flow uses that capability.
- Preserve current validation outcomes and error messages for that flow.
- Preserve existing observability behaviour (metrics and logging tied to validation) for
  the new-variable flow unless a later observability step explicitly adjusts it.

### Out of Scope

- Changing validation rules or adding new rules (e.g. Unicode policy, length limits).
- New UI flows that create variables (they may adopt the helper later).
- Comprehensive unit tests (PYPOST-477) and integration tests (PYPOST-480).
- Consolidating duplicate error-message strings between validation and UI layers
  (PYPOST-472).
- Reducing validation debug logging verbosity (PYPOST-479).
- Validating or renaming existing variables already stored in environments.

## Functional Requirements

- The application must expose a single shared validation capability for environment
  variable names that encodes the three rules above.
- The shared capability must return whether a name is valid and, when invalid, a specific
  reason aligned with the existing user-facing messages.
- The existing new-variable creation path must delegate to the shared capability and
  behave identically from the user's perspective.
- The shared capability must be invocable from automated tests without driving the GUI.
- Validation must continue to apply only when creating new variable names, not when
  reading or using existing variables (backward compatibility unchanged).

## Non-functional Requirements

- **Consistency**: all current and future callers of the shared helper must get the same
  pass/fail result for the same input.
- **Backward compatibility**: users with existing environments see no change to stored
  variables or to the new-variable creation experience.
- **Maintainability**: validation rules exist in one place so updates require a single
  change.
- **Testability**: the helper can be covered by unit tests independently of GUI code
  (tests themselves are a separate issue).

## Constraints and Assumptions

- Rules match Jinja2 template variable naming conventions already documented for PyPost.
- Whitespace trimming before validation remains the responsibility of the UI input flow;
  the shared helper validates the name string it receives.
- Metrics and logging for validation attempts may remain associated with the UI flow that
  creates variables; centralizing rules does not require redesigning observability in this
  task.
- Python 3.10+ and project code-style rules apply.

## Main Entities and Interactions

| Entity | Attributes | Role |
|--------|------------|------|
| **Environment variable** | name, value | Named key used in templates and request configuration; new names must be Jinja2-compatible. |
| **Variable name validation** | validity outcome, error reason | Business rules that accept or reject a proposed name with an explanatory message. |
| **New variable creation flow** | proposed name, current environment | User action that prompts for a name, validates it, and adds the variable to the current environment. |
| **Validation capability** | input name, pass/fail, message | Single authoritative enforcement of naming rules for any caller. |

Interaction overview:

1. User initiates new variable creation and enters a proposed name.
2. The UI flow trims input and passes the name to the shared validation helper.
3. If valid, the variable is created; if invalid, the user sees the same error message as
   today and creation is aborted.
4. Automated tests invoke the same helper directly to assert rule behaviour.

## Q&A

- **Q:** Why extract now if only one flow uses validation today?
  A: PYPOST-163 tech debt identified duplication risk as other modules adopt the same
  rules. Centralizing before drift occurs is cheaper than reconciling multiple copies
  later (PYPOST-471).

- **Q:** Does this task add unit tests?
  A: No. PYPOST-477 adds comprehensive unit tests; this task makes the rules testable in
  one place.

- **Q:** Will error messages change?
  A: No. Users must see the same three messages for empty, leading digit, and invalid
  character cases.

- **Q:** Does extraction change which names are valid?
  A: No. Valid and invalid examples in the existing variable-validation documentation
  remain the reference behaviour.

- **Q:** What about observability (metrics/logging)?
  A: Existing tracking for the new-variable flow should continue to work. Moving metrics
  into the shared helper is not required unless needed to preserve current behaviour;
  observability review belongs in STEP 5.

- **Q:** Source of truth for this task?
  A: Jira PYPOST-478, PYPOST-163 tech-debt follow-up, and existing variable-validation
  documentation from PYPOST-163.
