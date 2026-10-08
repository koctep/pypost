# PYPOST-1263: Reliable collection import planning performance coverage

## Goals

Give maintainers a trustworthy performance regression signal for large collection import
plans during normal parallel test runs. Unrelated CPU contention should not falsely report
a planner regression, while a genuinely slow planner must still be detected.

## User Stories

- As a maintainer, I want the large-dataset planner check to tolerate unrelated scheduling
  delays so that a parallel suite failure identifies an actionable problem.
- As a maintainer, I want meaningful planner slowdowns to fail clearly so that responsiveness
  regressions cannot be hidden by a less demanding test.
- As a reviewer, I want a reproducible distinction between contention and planner slowdown
  without depending on the host being busy at the time of verification.

## Definition of Done

- AC-1: The large-dataset planning performance check remains reliable under the repository's
  normal parallel test execution, including unrelated CPU contention.
- AC-2: Verification reproducibly demonstrates that unrelated scheduling delays do not cause
  a false performance regression report. Simulated contention is acceptable; creating live
  host load is not required.
- AC-3: Verification reproducibly demonstrates that an intentionally slow planner is rejected
  by the performance check. Acceptance must preserve a meaningful responsiveness signal.
- AC-4: Preserve the existing fixture scale of 500 incoming collections and 2,500 requests,
  with 25 conflicts exercising overwrite, keep-both, and skip decisions.
- AC-5: Preserve existing functional assertions on the resulting plan, including non-empty
  collections and a positive request count.
- AC-6: Do not obtain a passing result through skipping, expected failures, blind retries,
  or merely increasing the existing performance budget.
- AC-7: Failure output gives maintainers enough context to understand a performance rejection.
- AC-8: Production import planning behavior and application runtime configuration remain
  unchanged. Validation uses repository Makefile targets.

## Task Description

### Problem and evidence

The existing large-dataset planner test rejects elapsed time of 100 milliseconds or more.
Jira evidence records a failure in the full parallel `make test` run followed immediately
by an isolated pass at approximately 49 milliseconds. The test also passed at base commit
`b93cdb832510fea96494c72e0d214fc73e35ffaa`.

This evidence suggests contention sensitivity; it does not establish a production planner
defect or prove that every future timing failure is unrelated to planner performance.
The task must distinguish incidental contention from meaningful planner slowdown without
weakening functional coverage.

### Scope and constraints

- Implementation language: Python.
- Scope: the large-dataset planning performance check in
  `tests/test_collection_import_profile.py` and focused regression coverage of its signal.
- Preserve the existing functional coverage and representative workload.
- Keep execution bounded and failures reproducible.
- Production planner changes, unrelated performance tests, and broad test infrastructure
  redesign are outside scope.
- No new application security behavior or end-user configuration is required.

### Main entities

- Maintainer: relies on performance checks to identify regressions.
- Import workload: incoming collections, requests, and conflicts resolved by three decisions.
- Import plan: the collections and requests resulting from the conflict decisions.
- Performance signal: accepts healthy planning and rejects meaningful planner slowdown.
- Test execution environment: may introduce delays unrelated to planner work.

### Scenarios

1. The healthy planner processes the representative workload during a parallel test run;
   unrelated CPU contention does not turn this into a false planner regression.
2. A reproducible scenario introduces contention effects while planner work stays healthy;
   verification accepts the performance signal and preserves functional assertions.
3. A reproducible scenario makes the planner meaningfully slow; verification rejects it
   with useful failure context.

## Q&A

- Why is this needed? The Jira evidence shows inconsistent suite and isolated outcomes,
  reducing trust in the responsiveness guard and requiring avoidable maintainer triage.
- Must the fix force real host contention? No. A controlled reproducible scenario may model
  the distinction without relying on incidental machine load.
- Can the test simply use a larger budget or retry until it passes? No. The task requires a
  reliable regression signal and explicitly excludes those approaches.
