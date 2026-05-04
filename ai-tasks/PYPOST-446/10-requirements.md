# PYPOST-446: Evaluate masking policy for hidden env variables in History view/logs

## Goals

Define a clear and consistent security policy for how history and logs display values that
originate from hidden environment variables. Reduce the risk of accidental secret exposure
while preserving useful request history for users.

## User Stories

- As a user who stores sensitive values in hidden variables, I want history and logs to avoid
  exposing those values so I can use the app safely.
- As a user troubleshooting requests, I want history to remain useful and consistent so I can
  understand what happened without seeing sensitive data.
- As a team member responsible for security, I want one documented masking policy applied in all
  history/log surfaces so behavior is predictable and auditable.

## Definition of Done

- A single approved policy defines how hidden-variable-derived values are represented in history
  and logs.
- The policy is applied consistently across all relevant history and logging surfaces in scope.
- Existing behavior from hidden variable UI and preview remains aligned with the new policy.
- Acceptance tests cover key visibility and masking scenarios.
- Documentation of expected user-visible behavior is updated.

## Task Description

This task is a follow-up to `PYPOST-437`, which introduced hidden variables and masking in the
variables UI and preview. A remaining gap is that history and logs do not yet have a formally
defined exposure policy for values resolved from hidden variables.

The task must:

- identify where history persists or resurfaces resolved values;
- define masking rules for values derived from hidden variables;
- apply the approved policy and verify behavior with tests.

The task does not introduce a new hidden-variable feature. It closes the policy and consistency
gap for history and logs.

## Functional Requirements

- The system must detect when a displayed or persisted value comes from a hidden variable source.
- History and logs must follow the same approved masking rules for hidden-derived values.
- Masking behavior must be deterministic so the same input context yields the same visible output.
- The user must not see raw hidden-derived values in places covered by the policy.
- Non-hidden values must remain visible according to existing product behavior.

## Non-functional Requirements

- Security: Prevent accidental disclosure of hidden-derived values through history or logs.
- Consistency: Ensure the policy is applied uniformly across all in-scope history surfaces.
- Usability: Keep history and logs understandable for debugging without exposing sensitive data.
- Maintainability: Policy rules should be explicit and easy to validate through tests.

## Constraints and Assumptions

- This work is scoped to history rendering/logging behavior related to hidden-derived values.
- Existing hidden variable behavior in variable list and preview is treated as baseline context.
- Product behavior for non-hidden values remains unchanged unless explicitly required by policy.
- Policy decisions must prioritize security for sensitive data over full-value visibility.

## Main Entities and Interactions (Business View)

- Hidden variable: user-managed value marked as sensitive.
- Request execution context: resolves variable values when running a request.
- History record: stores and presents past request/response context.
- Log output: user-visible diagnostic output related to executed requests.
- Masking policy: set of business rules controlling visible representation of hidden-derived data.

Interactions:

- Hidden variables can influence request data during execution.
- History records and logs may include execution-derived data.
- The masking policy governs what is visible to users in these surfaces.

## Q&A

- Q: Why is this task needed if hidden variables already exist?
  A: Current masking covers variable UI and preview, but history/log behavior is not yet formally
  defined, creating a potential exposure gap.
- Q: What is the business objective?
  A: Protect sensitive values from accidental exposure while keeping history useful for workflows
  and troubleshooting.
- Q: What is in scope?
  A: Policy definition and consistent behavior for history and logs when values are derived from
  hidden variables.
