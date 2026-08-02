# PYPOST-970: Golden adopts shared Send-settle behavior

## Goals

The Golden agent end-to-end scenarios and their sibling scenarios currently prove the same
successful Send outcome through equivalent but duplicated settle behavior. That duplication
creates avoidable maintenance work and allows the canonical Golden path to drift from the
shared convention already adopted by its siblings in PYPOST-948.

**Business why:** Keep the Golden response-readiness proof aligned with the shared agent e2e
convention so maintainers have one reusable success-path contract, while users and CI continue
to observe the same Golden request/response outcome and actionable timeout evidence.

This is the Low-priority testing debt recorded as TD-4 in PYPOST-948. The ticket carries the
labels `agent`, `tech-debt`, and `testing` and is estimated at 2 story points.

## Programming Language

Python. The task concerns the Python agent end-to-end test suite. Task artifacts are written in
English Markdown.

## User Stories

- As an **agent e2e maintainer**, I want Golden successful Send scenarios to use the same shared
  settle contract as sibling scenarios, so fixes and diagnostic improvements do not need to be
  repeated in multiple places.
- As a **CI owner**, I want the full agent e2e suite to remain green, so the alignment does not
  weaken or destabilize existing product-flow coverage.
- As a **failure-triage owner**, I want Golden settle failures to retain the established step and
  response-excerpt evidence, so failures remain actionable.
- As a **Golden scenario owner**, I want request setup, Send behavior, expected response, and
  product assertions to remain unchanged in meaning, so this maintenance task does not alter the
  user journey being proved.

## Definition of Done

- Golden successful Send scenarios use the shared `wait_response_after_send` behavior where it
  represents their existing response-readiness contract.
- Successful Golden scenarios still prove the expected response status and body after Send.
- A settle failure still identifies the `wait_response_after_send` step and includes a useful
  response excerpt, while retaining the underlying wait evidence.
- The forced-timeout companion introduced by PYPOST-950 may remain separate because it proves an
  intentional failure path rather than the normal successful settle contract.
- Existing Golden scenario coverage, including the ordinary flow and the no-blank-tab flow,
  remains unchanged in business meaning.
- `make test-agent-e2e` passes.
- No unrelated behavior, production behavior, or user-visible product output changes.

## Task Description

### Problem

PYPOST-948 established a shared response-after-Send contract for sibling agent e2e scenarios,
but deliberately left Golden adoption as optional follow-up debt. Golden still carries its own
successful settle behavior even though it expects the same status, body, bounded completion, and
failure context.

Keeping both success-path forms increases the chance of drift and makes maintainers update the
same testing policy more than once. The desired outcome is consistent ownership of the common
behavior without changing what the Golden journeys prove.

### Optionality and Decision Outcome

The source debt described Golden migration as optional because the existing Golden behavior was
already correct. For PYPOST-970, the decision is to **adopt the shared success-path contract**:
the duplication now has a dedicated ticket, the shared behavior is established by PYPOST-948,
and the acceptance criterion explicitly calls for Golden to use it where appropriate.

The decision is deliberately limited. The PYPOST-950 forced-timeout companion may retain its
separate failure setup because its purpose is to force and inspect a miss, not to exercise a
successful response settle. This exception is an accepted outcome, not incomplete adoption.

### In Scope

- Align the successful response-after-Send behavior used by Golden scenarios with the shared
  contract established by PYPOST-948.
- Preserve Golden response readiness, bounded waiting, and failure-triage outcomes.
- Preserve all existing successful Golden journeys and assertions in meaning.
- Verify the full agent e2e suite remains green.

### Out of Scope

- Changing the user-visible request or response experience.
- Changing response status, body content, request inputs, or HTTP fixture behavior.
- Redesigning the shared Send-settle contract or introducing a new waiting capability.
- Requiring the PYPOST-950 forced-timeout companion to use the shared success-path behavior.
- Broad migration of unrelated agent e2e waits or scenarios.
- Production behavior, public interfaces, or user documentation changes.
- Unrelated cleanup discovered while completing the task.

## Functional Requirements

- FR1: Each applicable Golden successful Send journey must use the shared response-after-Send
  contract.
- FR2: The Golden journey must continue to become ready only after its expected status and body
  are observable.
- FR3: Both the ordinary Golden flow and the no-blank-tab Golden flow must retain their current
  request/response outcomes.
- FR4: Shared settle failures must retain the established step identity and a response excerpt
  suitable for CI triage.
- FR5: Existing underlying wait evidence must remain available when a shared settle fails.
- FR6: The forced-timeout companion may remain separate and must retain the behavior guaranteed
  by PYPOST-950.
- FR7: The complete agent e2e test selection must pass after the alignment.

## Non-Functional Requirements

- **Consistency:** Applicable Golden success paths follow the same response-readiness convention
  as sibling agent e2e scenarios.
- **Maintainability:** Common success-path behavior has one shared ownership point.
- **Stability:** The change must not introduce longer or unbounded waits.
- **Diagnosability:** Failure output remains actionable through step, response excerpt, and
  underlying wait evidence.
- **Compatibility:** Existing Golden and sibling scenario expectations remain valid.
- **Minimal scope:** Only behavior needed to remove the applicable duplication is changed.

## Constraints and Assumptions

- The shared response-after-Send behavior from PYPOST-948 is already established and green for
  sibling scenarios.
- The Golden successful settle and shared settle represent the same observable status-then-body
  readiness outcome.
- Golden continues to operate within its current request tab and current bounded suite budget.
- The successful response fixture and all product assertions remain unchanged in meaning.
- PYPOST-950 owns the forced-timeout companion's intentional failure behavior and preservation
  constraints.
- Step 1 records requirements only; design and implementation choices belong to later steps.
- Step 1 remains pending review and is therefore marked `[/]` in the roadmap.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Golden successful journey | Canonical request/response product proof | Keeps the same result |
| Shared Send-settle contract | Common response-readiness proof | Used by applicable Golden flows |
| Expected response | Status and body observed after Send | Remains unchanged |
| Failure evidence | Information used to diagnose a missed settle | Remains actionable |
| Forced-timeout companion | Intentional failure-path regression proof | May remain separate |
| Agent e2e suite | CI confidence across Golden and sibling scenarios | Remains green |

Interaction overview:

1. A Golden scenario prepares and sends the same deterministic request as today.
2. The applicable successful path uses the shared settle contract to observe the expected
   response status and body.
3. The scenario continues with its existing product assertions.
4. If readiness fails, maintainers receive the established step and response context.
5. The separate forced-timeout companion continues to prove its PYPOST-950 failure guarantees.
6. CI runs the complete agent e2e selection successfully.

## Q&A

- Q: Why change behavior that already passes?
  A: The user outcome is already correct, but duplicate ownership creates drift and repeated
  maintenance. This task adopts the established shared convention without changing the outcome.

- Q: Was Golden adoption optional?
  A: Yes in PYPOST-948, where Golden was explicitly out of scope. PYPOST-970 resolves that
  optional debt by choosing adoption for applicable successful paths.

- Q: Does "where appropriate" include the forced-timeout companion?
  A: No requirement mandates that. Its deliberate miss proves a distinct PYPOST-950 failure
  contract, so preserving it separately is an accepted outcome.

- Q: May Golden assertions or fixtures be simplified as part of this task?
  A: Only if their observable meaning is fully preserved and the change is necessary for shared
  settle adoption. Unrelated cleanup is out of scope.

- Q: What proves completion?
  A: Applicable Golden success paths use the shared settle contract, preservation constraints
  hold, and `make test-agent-e2e` is green.
