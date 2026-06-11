# PYPOST-548: `make test` hangs and never finishes

## Goals

Running `make test` currently stalls indefinitely and never returns a result. This blocks the
whole team: continuous integration cannot report pass or fail, automated agent runs get stuck,
and local developers lose the ability to validate their changes. The goal is to make the test
suite trustworthy again — it must always finish and produce a clear pass/fail outcome — and to
make the project's stated testing policy honest, so the documentation matches how the suite
actually behaves.

## User Stories

- As a developer, I want `make test` to always finish and tell me pass or fail, so I can know
  whether my change is safe to commit instead of waiting forever.
- As a CI maintainer, I want the automated test run to terminate on every build, so pipelines
  report a result instead of timing out at the job level or running until they are killed.
- As an automation/agent operator, I want autonomous runs that invoke the test suite to
  complete, so agent workflows do not get stuck waiting on a run that never ends.
- As a contributor reading the project docs, I want the documented testing policy to reflect
  what the project actually enforces, so I can rely on the documentation when writing tests.

## Definition of Done

- Running `make test` reliably completes and returns a pass/fail result (it no longer hangs
  indefinitely).
- No single test can stall the entire suite forever; a test that gets stuck fails fast and the
  rest of the run continues to a final result.
- The per-test timeout policy described in the project documentation is actually in force, so a
  test that exceeds its allotted time is reported as a failure rather than allowed to block the
  run.
- The testing documentation and the project's actual behavior agree: what the docs promise
  about timeouts is what the suite does.
- Tests that pass today continue to pass; this change does not introduce new failures or flap
  in the existing suite.

## Task Description

### Problem

`make test` hangs and never finishes. Because the run never returns, no one — CI, automated
agents, or developers — can obtain a pass/fail result for the project.

### Why it matters

- CI is blocked: builds cannot confirm whether the codebase is healthy.
- Automated/agent runs are blocked: workflows that depend on the test result cannot proceed.
- Local development is blocked: developers cannot validate changes before committing.

### Functional requirements

- The test suite must always terminate and produce a result; an end-to-end run of `make test`
  must not be able to hang indefinitely.
- A hung or excessively slow individual test must fail fast rather than block the whole run, so
  one stuck test cannot prevent the suite from reaching a final outcome.
- The project's documented per-test timeout policy must be genuinely enforced, not merely
  described — the documentation and the actual suite behavior must agree.

### Non-functional requirements

- Reliability: the outcome of `make test` must be deterministic with respect to termination —
  it always reaches a verdict and never depends on someone manually killing the run.
- Maintainability/trust: project documentation about testing must remain accurate so
  contributors can rely on it.
- No regressions: turnaround time and results for the currently passing tests must not be
  degraded by the change.

### Constraints and assumptions

- This is a bug fix; the expected, previously working behavior is a test suite that always
  finishes.
- Scope is the project's own test execution via `make test`; production application behavior is
  out of scope.
- The relevant testing policy and its documentation already exist in the project and are the
  reference for the intended behavior; the gap is that the promised behavior is not yet
  guaranteed in practice.
- Solution design (how termination is guaranteed and how the policy is enforced) is
  intentionally deferred to later steps and is not decided here.

## Q&A

- **Q:** What is the observed symptom? **A:** `make test` hangs and never finishes, so no
  pass/fail result is produced.
- **Q:** Who is affected? **A:** CI, automated/agent runs, and local developers — all are
  blocked from getting a result.
- **Q:** What does "done" look like in business terms? **A:** `make test` always completes with
  a verdict, no single test can stall the suite forever, and the documented timeout policy is
  actually enforced.
- **Q:** Is there an existing policy that should already prevent this? **A:** Yes. The project
  documentation describes a mandatory per-test timeout policy, but that policy is not currently
  guaranteed in practice; closing that gap is part of this task.
- **Q:** Is the fix approach (specific tools, configuration, code) decided here? **A:** No.
  Step 1 captures business requirements only; the technical approach is defined in later steps.
