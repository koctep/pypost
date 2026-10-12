# PYPOST-1298: Reliable parallel Make fixture preparation

## Goals

Developers and CI need timely, trustworthy feedback from Make quality gates. Parallel test
execution must not turn shared fixture preparation into unrelated test timeouts or obscure
actual regressions. Restore reliable gate execution while preserving test coverage and deadlines.

## User Stories

- As a developer, I can run the full parallel test suite without fixture contention causing
  otherwise valid Make integration tests to time out.
- As a CI maintainer, I receive a bounded, actionable preparation failure when a prerequisite
  cannot become ready, rather than an indefinite wait or unrelated test failure.
- As a test maintainer, I can continue exercising Make behavior in separate test workspaces
  with the existing assertions and timeout protections.

## Definition of Done

1. A regression scenario demonstrates concurrent requests for an initially unprepared shared
   fixture. All successful callers receive a ready, usable environment; none observes a
   partially prepared environment.
2. Contention and deliberately stalled preparation terminate within explicit finite deadlines
   documented by the implementation. Automated regressions verify those deadlines without
   depending on an external package service or machine-specific timing.
3. Preparation failure does not leave subsequent callers indefinitely waiting or allow a failed
   preparation to be treated as successful. A regression verifies a subsequent successful retry.
4. The affected Make fixture suites run through Make with their existing test deadlines,
   assertions, and inclusion rules. They report zero timeouts caused by shared preparation.
5. Full `make test` and `make check` run with the repository's normal parallel execution settings.
   No shared-fixture contention timeouts occur. Any unrelated baseline failures are identified
   separately with evidence under the sprint's failure-triage procedure.
6. Existing successful reuse of prepared fixtures and separate test workspaces remains supported.
   Parallel callers do not corrupt the shared preparation or one another's workspace contents.
7. Existing timeout limits, coverage, and parallel test inclusion are not relaxed to hide the
   reported failure. No application behavior change is required.

## Task Description

### Problem and evidence

The Jira issue reports that full `make check` / `make test` at base commit `10ba60b7` timed out
while waiting for shared Make test environment preparation. Contending tests exhausted 30-second
test deadlines, and multiple Make fixture files exhausted 120-second deadlines. Preparation
currently serves multiple concurrent callers and must finish before their isolated workspaces
can exercise Make behavior.

### Implementation language

Python.

### Scope

- Shared Make integration fixture readiness, concurrent demand, failure, and subsequent recovery.
- Automated regression coverage for the reported contention and bounded failure behavior.
- Verification of affected suites and full Make gates under normal parallel load.
- Documentation of preparation deadlines and actionable failure information.

### Out of scope

- Application features or unrelated test repairs.
- Broad Make target redesign, new dependency versions, or dependency lock changes.
- Disabling parallel execution or increasing test deadlines to mask preparation contention.

### Functional requirements

- Concurrent fixture consumers can obtain a usable environment when preparation succeeds.
- Consumers cannot mistake an incomplete or failed preparation for a ready environment.
- Preparation errors identify the failed prerequisite clearly enough to guide investigation.
- A failed preparation permits a later attempt to succeed when its underlying cause is resolved.
- Each test retains its separate workspace and its expected Make behavior checks.

### Non-functional requirements and constraints

- Waiting and preparation have explicit finite bounds, including failure paths.
- Successful full-suite execution fits existing test timeout protections under normal parallel load.
- Regression verification is repeatable and does not require an external package service.
- Run repository checks, builds, tests, and dependency operations exclusively through Make targets.
- Scope remains limited to this Jira debt issue; preserve unrelated workspace files and artifacts.

### Main entities

- **Fixture consumer**: a Make integration test needing a ready environment and its own workspace.
- **Prepared environment**: reusable test prerequisites with a readiness outcome.
- **Test workspace**: the separate files and environment used to exercise a test's Make behavior.
- **Quality gate run**: concurrent tests, existing deadlines, and a pass or diagnostic failure result.

## Q&A

- **Why is this needed?** The sprint goal and issue evidence establish the business reason:
  reliable Make gates must provide timely, trustworthy feedback under parallel load.
- **What counts as success?** Concurrent fixture preparation remains usable, bounded, recoverable,
  and compatible with existing Make integration coverage and deadlines.
- **Are new numeric preparation limits mandated by Jira?** No. Explicit finite preparation
  deadlines must be chosen and justified during design; existing test deadlines remain unchanged.
- **Who accepts these requirements?** The autonomous sprint orchestrator after independent review.
