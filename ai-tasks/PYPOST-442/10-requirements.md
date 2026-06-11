# PYPOST-442: Enforce non-negative RetryPolicy.max_retries validation

## Context

- **Jira:** PYPOST-442
- **Origin:** Technical debt from [PYPOST-421](https://pypost.atlassian.net/browse/PYPOST-421)
  review (`60-review.md`): `RetryPolicy.max_retries` accepts negative values, which can
  trigger the defensive `retry_loop_invariant_failed` path in `RequestService`.
- **Type:** Debt (Sprint 167)

## Problem statement

`RetryPolicy.max_retries` is an integer with no lower bound. A negative value produces an
empty `range(max_retries + 1)` in the HTTP retry loop, so no attempts run and the service
falls through to a defensive invariant error. Invalid configuration should be rejected at
model construction time, not at runtime inside the retry loop.

## Goals

- Reject negative `max_retries` values when a `RetryPolicy` (or nested request model) is
  constructed or deserialized.
- Preserve existing behavior for `max_retries >= 0` (including default `0`).
- Add automated tests that document and enforce the constraint.

## Scope

### In scope

- Pydantic validation on `RetryPolicy.max_retries` (non-negative, `ge=0`).
- Unit tests for direct `RetryPolicy` construction and `RequestData` with nested policy.
- Developer notes for the validation rule.

### Out of scope

- Changing retry loop logic, UI spin-box ranges, or other `RetryPolicy` fields.
- Covering the defensive post-loop branch with a contrived test (remains theoretical once
  validation is enforced).
- Upper bound on `max_retries` (Settings UI already caps at 10; API limit is separate).

## User stories

- As a **developer**, I want invalid retry configuration to fail fast at parse/construct
  time so HTTP execution never hits the defensive invariant path for this reason.
- As a **maintainer**, I want tests that prove negative `max_retries` cannot be persisted
  through the `RetryPolicy` model.

## Functional requirements

1. **FR-1:** `RetryPolicy(max_retries=n)` must succeed when `n >= 0`.
2. **FR-2:** `RetryPolicy(max_retries=n)` must raise a validation error when `n < 0`.
3. **FR-3:** `RequestData` carrying a `retry_policy` with negative `max_retries` must fail
   validation at model construction (nested Pydantic validation).
4. **FR-4:** Default `max_retries=0` behavior is unchanged.

## Acceptance criteria

1. **AC-1:** `RetryPolicy(max_retries=-1)` raises `ValidationError`.
2. **AC-2:** `RetryPolicy(max_retries=0)` and `RetryPolicy(max_retries=3)` construct
   successfully.
3. **AC-3:** `RequestData(..., retry_policy=RetryPolicy(max_retries=-1))` raises
   `ValidationError`.
4. **AC-4:** Existing retry unit tests continue to pass.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | No legitimate use case for negative retry counts. |
| **Assumption** | Settings UI already constrains spin-box to 0–10; this hardens programmatic paths. |
| **Risk** | Low: persisted configs with negative values (if any) would fail on load; unlikely. |

## Programming language

**Python** — `pypost` package, Pydantic v2 `Field(ge=0)`.
