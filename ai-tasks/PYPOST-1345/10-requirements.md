# PYPOST-1345: Guard empty-body success for GitHub dispatch, cancel, and re-run

## Goals

Maintainers need automated proof that GitHub MCP write tools which succeed with no response body
are still reported as successful tool results. Parent collection work already requires that
behavior; without a test that exercises empty-body success statuses, a future regression could
treat those responses as failures or require a body, breaking dispatch, cancel, and re-run
workflows that GitHub documents as body-less successes.

## User Stories

- As a collection maintainer, I can rely on offline GitHub MCP tests to fail if dispatch, cancel,
  or re-run stop reporting success when the upstream response has a documented success status and
  an empty body.
- As a reviewer, I can see explicit coverage that each of those three tools is exercised through a
  full MCP tool call with empty-body success, not only through stubs that always return a JSON
  body with status 200.
- As a PyPost user of the GitHub MCP collection, I continue to receive success results for
  workflow dispatch, cancel, and re-run when GitHub answers with an empty body, guarded by
  regression tests rather than code reading alone.

## Definition of Done

1. Offline tests drive MCP tool calls for GitHub workflow re-run, cancel, and dispatch such that
   each call receives a documented empty-body success outcome for that operation (re-run: 201;
   cancel: 202; dispatch: 204).
2. For each of those three results, the MCP tool outcome is success: not marked as an error,
   carries the expected success status for that operation, and has an empty body.
3. Coverage lives in the GitHub MCP collection test suite and uses the collection’s loopback test
   double so the path is exercised without live GitHub.
4. No production runtime behavior change is required for this debt; the work guards behavior that
   parent requirements already mandate and that code reading already indicates is implemented.
5. Existing MCP collection contract coverage, timeouts, and Make-driven quality gates remain
   effective for the touched suite.

## Task Description

### Problem and evidence

Parent debt: [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) TD-16, recorded in
`ai-tasks/PYPOST-1334/60-tech-debt.md`.

Parent requirement (`ai-tasks/PYPOST-1334/10-requirements.md`): write operations without a
response body (for example dispatch, cancel, re-run) are considered successful on GitHub’s
documented success status; the tool must not require a body to report success.

Today the GitHub MCP collection loopback test double always answers with status 200 and a JSON
body. No test drives an empty-body `201` / `202` / `204` success through an MCP tool call for
re-run, cancel, or dispatch. Maintainers therefore rely on code reading rather than an automated
guard for that success path.

### Business reason

Example-collection tests are the gate that MCP tools behave as required before they ship. The
empty-body success rule is a real product requirement for Actions write tools: GitHub often
returns only a status. If that path is never exercised in tests, a regression could mark those
calls as errors or demand a body, and the suite would still pass. Closing the gap restores
confidence that dispatch, cancel, and re-run remain usable under documented empty-body successes.

### Implementation language

Python.

### Scope

- Extend the GitHub MCP collection offline verification so re-run, cancel, and dispatch can be
  exercised with their documented empty-body success statuses.
- Assert each corresponding MCP tool result is success (not an error, expected status, empty
  body).
- Keep the work test-suite scoped; no change to MCP request execution semantics is required.

### Out of scope

- Changing how the MCP runtime classifies success or error for HTTP responses.
- Live GitHub smoke tests or production MCP server behavior changes.
- Other PYPOST-1334 follow-ups (template-marker checks, shared helpers, API version migration,
  schema enum/`items`, type-preserving JSON helpers, merge/submit tools, path-segment hardening,
  and related tickets).
- Broader changes to non-GitHub MCP collection stubs or suites beyond what this debt needs.

### Functional requirements

- Re-run, cancel, and dispatch each have automated coverage that goes through an MCP tool call
  and receives an empty-body success response with the status GitHub documents for that write.
- Each covered result reports success without requiring response content: not an error, correct
  status, empty body.
- Coverage remains offline and uses the existing GitHub MCP collection test approach (loopback
  double + collection tests).

### Non-functional requirements and constraints

- Verification remains offline, repeatable, and bounded by existing test timeout rules.
- Repository build, analysis, test, dependency, and artifact-verification operations use Make.
- Preserve unrelated files, completed task records, and existing production quality coverage.
- Scope remains limited to this Jira debt issue (PYPOST-1345) and the TD-16 evidence above.
- Estimate context from Jira: approximately 2 story points; test-only.

### Main entities

- **Empty-body write success**: a documented GitHub success status for a write that carries no
  response body (re-run 201, cancel 202, dispatch 204).
- **MCP tool result**: the structured outcome of a tool call (error flag, status, body) that
  callers use to decide whether the operation succeeded.
- **GitHub Actions write tools**: workflow re-run, cancel, and dispatch as exposed by the GitHub
  MCP example collection.
- **Offline collection gate**: the GitHub MCP collection tests and loopback double that prove
  tool behavior without calling live GitHub.

## Q&A

- **Why is this needed if runtime already handles empty bodies?** Code reading is not a
  regression gate. Without a test, the suite can stay green while empty-body success becomes
  mis-reported.
- **Does this change production MCP behavior?** No. The debt is test-only coverage of an
  already-required success rule from PYPOST-1334.
- **Why these three tools and statuses?** Parent requirements and architecture name dispatch,
  cancel, and re-run as writes that succeed without a body; TD-16 maps them to 201 / 202 / 204.
- **Why not keep the stub always returning 200 + JSON?** That shape never exercises empty-body
  success, so it cannot guard the requirement.
- **Who accepts these requirements?** The autonomous sprint orchestrator after independent
  review.
