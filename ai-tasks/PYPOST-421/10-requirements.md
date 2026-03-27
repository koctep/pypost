# PYPOST-421: Reliable failure handling on HTTP retry exhaustion

This task delivers the outcome described for related finding **PYPOST-402** (“bare assert in
production retry path”) within the **PYPOST-421** work item only. No other Jira tasks are in
scope.

## Programming language

- **Python** — all changes for PYPOST-421 are implemented and verified in Python, following
  `.cursor/lsr/do-python.md` during later steps.

## Problem statement

When an HTTP request is executed with retries, the path that runs after all retry attempts are used
up must always behave correctly. Relying on a bare assertion to enforce an expected condition in
that path is unsafe: it does not communicate a clear, stable failure mode to callers and may not run
as intended in every deployment configuration. The product needs predictable, explicit handling
when retries are exhausted so failures are visible and actionable.

## Goals

- Ensure retry exhaustion is always handled through explicit failure semantics, not through
  assertion-only checks that are unsuitable for production behavior.
- Preserve existing user-observable behavior for successful requests and for errors that already
  propagate through defined error types, except where fixing the defect requires tightening
  failure reporting.

## Scope

- In-scope: Behavior of the HTTP execution flow that performs retries until a final outcome
  (success or failure), specifically the branch where retries are exhausted after retryable
  outcomes.
- In-scope: Consistency of error propagation and observability when that exhaustion occurs.
- In-scope: Automated tests that guard the intended behavior for this path.

## Out of scope

- Broader redesign of retry policies, back-off, or HTTP client internals beyond what is needed to
  satisfy this defect.
- Changes unrelated to the retry exhaustion path or tracked under other Jira IDs.
- Non-Python components or repositories outside the agreed Python deliverable for PYPOST-421.

## Main entities (business view)

- **HTTP request attempt**: A single try to obtain a response for a configured request.
- **Retry policy**: Rules that define how many times to retry and what counts as retryable.
- **Execution outcome**: Either a successful response or a failure that the application surfaces to
  the user or calling workflow.
- **Retry exhaustion**: The situation where, under the configured retry policy, no further retries
  are allowed (typically after one or more retryable outcomes) and the outcome must be finalized
  as a failure with a clear reason.

## User stories

- As a **user of workflows that call HTTP endpoints**, I want exhausted retries to fail in a clear
  way so I understand the request did not complete after retries.
- As an **operator or integrator**, I want failures after retry exhaustion to be diagnosable from
  logs and existing signals without depending on optional runtime modes.

## Functional requirements

1. When retries are exhausted after retryable HTTP outcomes, the system must finalize the outcome
   as a failure using the same structured error reporting mechanism used elsewhere for execution
   failures (not an assertion-only guard).
2. The failure path after exhaustion must still emit the same class of diagnostic information
   (e.g. exhaustion alerts and relevant metrics) as intended for “retries used up” scenarios,
   without skipping steps due to assertion behavior.
3. Behavior for cancellation during retry or back-off remains correct and must not regress.
4. Regression tests must cover the exhaustion path so the defect cannot return unnoticed.

## Non-functional requirements

- **Reliability**: Behavior must not depend on optional assertion semantics in production runs.
- **Consistency**: Error categories and messages remain aligned with existing execution error
  patterns for network and HTTP failures.
- **Maintainability**: Future readers can see an explicit control-flow path for exhaustion without
  relying on implicit invariants enforced only by assertions.

## Acceptance criteria

1. The production retry exhaustion path no longer uses a bare assertion as the primary guarantee
   that failure handling runs.
2. Exhaustion after retryable outcomes still raises or returns failure through the established
   execution error path, with exhaustion details preserved.
3. Existing automated test suite passes; new or updated tests specifically cover retry exhaustion
   after retryable HTTP outcomes (including retryable status codes where applicable).
4. No change in scope beyond PYPOST-421 (no mixing of other Jira tasks).

## Risks and assumptions

- **Risk**: A fix might subtly change error text or detail strings; mitigated by aligning with
  existing patterns and reviewing tests.
- **Assumption**: The relevant behavior lives in the Python HTTP request/retry execution path for
  this product; if multiple layers participate, work stays within the scope agreed for PYPOST-421
  in later steps (no scope creep into unrelated Jira items).
- **Assumption**: Reviewers validate behavior under normal Python execution (not only optimized
  modes) while still accepting that assertions must not be the contract for production
  correctness.

## Definition of done (business)

The task is done when retry exhaustion is handled explicitly, the defect described for PYPOST-402 is
addressed within PYPOST-421, tests protect the behavior, and stakeholders accept the requirements
and subsequent implementation after review.

## Q&A

- **Q**: Why is this framed as a reliability issue?  
  **A**: Assertions are not a stable contract for production control flow; exhaustion must always
  surface as a defined failure.

- **Q**: What does “explicit failure” mean for callers?  
  **A**: The same failure channels and categories as other HTTP execution failures, so outcomes are
  predictable without depending on assertion behavior.

## Product Owner review

- **Status**: Approved for architecture (STEP 2). Requirements express business intent and
  acceptance criteria for PYPOST-421 only; technical design is out of scope for this document.
