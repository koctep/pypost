# PYPOST-982: Optional POST-path mapping settle timeout companion

## Goals

The mapping multi-URL GUI scenario already demonstrates that a successful POST
Send reaches its expected response. It also has a failure-diagnostic contract
for response settling, but the POST path is not yet protected by a focused
automated assertion.

The business and maintainer goal is to make POST mapping-settle failures
actionable and regression-resistant. When a POST response does not settle,
maintainers and automated agents must be able to identify the failed lifecycle
step and see concise response-panel context in the failure diagnostics.

This closes the optional POST-path companion identified by PYPOST-955 while
preserving the confidence already provided by the existing happy-path mapping
coverage and GET-path diagnostic companion.

## User Stories

- As a maintainer, I want a deterministic POST mapping-settle timeout check so
  regressions in failure diagnostics are caught by CI.
- As an AI agent or test-harness author, I want a POST settle failure to identify
  `wait_response_after_mapping_post_send` so I can locate the failed action
  without reconstructing the scenario from logs.
- As a maintainer diagnosing a CI failure, I want `response_excerpt` to contain
  a concise response-panel excerpt so the failure includes useful UI context.
- As a CI or headless-runner maintainer, I want the forced-timeout scenario to
  finish within a bounded time and never hang the job.
- As the owner of the existing mapping multi-URL coverage, I want the POST
  companion to preserve the meaning and independent value of the successful
  GET and POST checks.

## Definition of Done

The task is complete when all of the following acceptance criteria are met:

- A focused automated companion covers the mapping multi-URL POST Send path.
- The companion forces a near-zero response-settle budget and reaches the
  intended timeout path deterministically.
- The resulting failure diagnostics identify the exact stable step
  `wait_response_after_mapping_post_send`.
- The resulting failure diagnostics include `response_excerpt` as a string
  containing concise response-panel context.
- The scenario has a bounded execution time and cannot leave CI waiting
  indefinitely for the response to settle.
- Existing successful mapping multi-URL behavior remains valid, including the
  POST response outcome already covered by the scenario.
- Existing GET-path mapping diagnostic coverage and the golden Send diagnostic
  companion retain their acceptance meaning.
- Validation runs through the repository's Make targets, including focused
  agent-e2e coverage and the applicable quality/artifact gates.

## Task Description

### Problem and business reason

PYPOST-955 established the need to assert mapping Send settle diagnostics.
Its first companion covers the GET path, while this follow-up targets the
optional POST path. Without the POST assertion, a regression could remove or
mislabel POST timeout context while successful POST requests continue to pass.

The required outcome is a small, deterministic maintainer safeguard: a forced
POST settle timeout must prove that both the stable lifecycle step and concise
response context remain available.

### In Scope

- Automated failure-path coverage for POST Send under the existing mapping
  multi-URL GUI scenario.
- A near-zero settle budget whose purpose is to exercise the timeout path
  deterministically.
- Assertions for `wait_response_after_mapping_post_send` and `response_excerpt`.
- Bounded execution appropriate for the standard agent-e2e and quality gates.
- Preservation checks for the existing successful POST mapping behavior.

### Out of Scope and Non-Goals

- Changing production request, mapping, response-settle, or timeout behavior.
- Changing the public meaning of the mapping or POST Send workflow.
- Replacing the existing happy-path mapping multi-URL coverage.
- Expanding into a complete mapping URL/method/status failure matrix.
- Altering GET-path coverage, golden Send coverage, or unrelated lifecycle tests.
- Adding user-facing product behavior or user documentation.
- Introducing new logging or metrics solely for this test companion.
- Creating or synchronizing additional Jira debt issues during this task.

### Deterministic behavior

The companion must deliberately exercise the POST response-settle failure
condition with a near-zero budget. It must fail in the intended bounded manner,
with stable diagnostic values, rather than depending on ambient network,
event-loop, display, or machine timing. A normal successful POST response must
remain distinguishable from the intentionally forced timeout scenario.

### Compatibility and constraints

- Implementation language: Python 3.10+.
- The coverage remains within the existing agent-e2e test boundary and uses the
  established mapping multi-URL POST scenario as its business context.
- The change is test-harness-only and must not affect production behavior,
  live-network behavior, or user-visible application flows.
- The existing diagnostic contract is the source of truth for the stable POST
  step name and `response_excerpt` field.
- The scenario must remain compatible with standard offscreen/headless CI
  execution and repository timeout policy.
- Documentation and task artifacts are written in English Markdown with normal
  repository formatting and line-length rules.

### Validation expectations

- Focused agent-e2e validation demonstrates the POST timeout companion and its
  two required diagnostics.
- The existing mapping multi-URL success checks continue to pass.
- Relevant neighboring diagnostic coverage continues to pass.
- Repository linting and AI-task artifact verification are run through Make
  targets; broader quality gates are run when required by the workflow.
- Any pre-existing unrelated failures are recorded with their owning issue and
  are not presented as evidence that this requirement is satisfied.

### Main business entities and interactions

| Entity | Business role | Required attributes |
| --- | --- | --- |
| Mapping POST Send | User action needing diagnostic protection | POST path; mapping context |
| POST settle timeout | Bounded failure state for diagnosis | Near-zero budget; intentional timeout |
| Stable POST step | Name of the failed lifecycle step | Exact POST wait-step name |
| Response excerpt | Concise response-panel context | String; present on timeout |
| Successful POST outcome | Compatibility baseline | Existing response behavior |
| Agent-e2e runner | Bounded CI execution environment | Headless-safe; finite duration |

Interaction expectations:

1. The scenario reaches the normal mapping POST Send context.
2. The companion enters a deliberately forced, near-zero settle-timeout state.
3. The timeout diagnostics identify `wait_response_after_mapping_post_send`.
4. The same diagnostics provide a string `response_excerpt` with response-panel
   context.
5. The bounded scenario completes, and the normal successful POST behavior
   remains covered independently.

## Q&A

- **Why is this separate from PYPOST-955?** PYPOST-955 established the mapping
  diagnostic companion and its GET-path proof. This task closes the explicitly
  optional POST-path gap without broadening the original acceptance scope.
- **Why is the POST path required?** GET and POST are separate user actions and
  have distinct stable settle-step identifiers. A GET assertion alone cannot
  detect a POST-specific diagnostic regression.
- **What must be asserted?** The exact stable POST step identifier
  `wait_response_after_mapping_post_send` and a string `response_excerpt` with
  concise response-panel context.
- **What does “near-zero” mean here?** It means a deliberately minimal settle
  budget sufficient to force the intended timeout path while remaining bounded;
  the exact implementation value is deferred to later workflow steps.
- **Does this change production behavior?** No. The requirement is for
  maintainer-facing automated coverage of an existing diagnostic contract.
- **What happens if unrelated baseline checks fail?** They must be recorded and
  attributed separately; they do not change the acceptance criteria for this
  focused test companion.
