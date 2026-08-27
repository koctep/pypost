# PYPOST-1192: Orchestrator waits for workers at most TIMEOUT seconds

## Goals

Developers and CI depend on the parallel test orchestrator (from PYPOST-1149)
to finish every `make test` / `make test-cov` run in bounded time. Today the
orchestrator can wait indefinitely for a worker that never responds (hang,
deadlock, or stuck subprocess). That turns a single bad file into an unbounded
stall of the whole quality gate.

This task requires the orchestrator to wait for each worker’s completion or
response for no longer than a configurable **TIMEOUT** (default **30**
seconds). When the bound is exceeded, that worker is treated as failed/timed
out, operators get a clear structured signal, and the run finishes without
hanging forever.

**Business goal**: Protect local and CI test cycles from indefinite hangs by
enforcing a hard upper bound on how long the orchestrator waits for any one
worker.

**Implementation language**: Python (parallel test runner orchestrator and its
tests/docs in the existing Python suite; no new runtime language).

## User Stories

- As a **developer running `make test`**, I want a hung worker to fail within
  TIMEOUT seconds so my local suite does not stall forever waiting for one
  file.
- As a **CI / quality-gate operator**, I want the orchestrator to finish every
  run with a definitive pass/fail outcome, even when a worker never responds,
  so pipelines cannot hang open indefinitely.
- As a **maintainer diagnosing timeouts**, I want a clear structured timeout
  message for the affected worker so I can tell timeout apart from a normal
  test failure.
- As an **operator of slow or long suites**, I want TIMEOUT to be configurable
  (CLI and/or environment) so legitimate longer waits remain possible without
  changing the default of 30 seconds.

## Definition of Done

- When the orchestrator starts workers, each wait for worker completion or
  response is bounded by TIMEOUT seconds (hard upper bound).
- Default TIMEOUT is **30** seconds when the operator does not override it.
- TIMEOUT is configurable via CLI flag and/or environment variable; the chosen
  names are documented for operators (runner contract / developer docs).
- On timeout, the affected worker is treated as failed/timed out (not as
  success or indefinite wait).
- On timeout, the orchestrator emits a clear structured log/message that
  identifies the timeout condition for that worker.
- After a worker timeout, the orchestrator run completes without hanging
  indefinitely.
- Automated tests cover the timeout path (worker exceeds TIMEOUT → failed/
  timed-out outcome and observable timeout signal).
- If the runner operator contract changes, `doc/dev/parallel_test_runner.md` is
  updated accordingly.
- Out of scope items below remain untouched.

## Task Description

### Problem

The parallel test orchestrator launches workers and waits for each to finish.
Those waits currently have no wall-clock upper bound. A worker that never
returns (hang, deadlock, stuck child) can block the orchestrator—and thus
`make test` / CI—without end. PYPOST-1149 deferred per-file orchestrator
wall-clock timeout; that gap is tracked among maintainability debt in
[PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153) (item: optional
per-file orchestrator wall-clock timeout). This story delivers that bound with
an explicit default of 30 seconds.

### Business need

Quality gates must always terminate. Unbounded worker waits destroy trust in
CI and waste engineer time. A default 30-second cap, with an escape hatch to
raise TIMEOUT for slower workloads, balances fast failure against flexibility.

### Scope

**In scope**

- Hard upper bound (TIMEOUT seconds) on orchestrator wait for each worker’s
  completion or response.
- Default TIMEOUT = 30.
- Operator configurability of TIMEOUT (CLI and/or env); document chosen names.
- Timeout outcome: worker counted as failed/timed out; clear structured
  message; run finishes without indefinite hang.
- Automated coverage of the timeout path.
- Developer-doc update when the runner contract changes
  (`doc/dev/parallel_test_runner.md`).

**Out of scope**

- Changing pytest-timeout markers inside individual test modules, except if
  strictly required to align with the orchestrator default (prefer not to
  churn module markers).
- Unrelated PYPOST-1153 maintainability items (argparse migration, Makefile
  recipe tests, cov-fail-under wiring, dead API cleanup, invalid-worker CLI
  tests, coverage-threshold integration test, and similar).
- Redesigning worker concurrency policy, discovery, coverage combine, or JSON
  report schema beyond what timeout status reporting requires.
- Non-orchestrator test entry points that still call pytest directly
  (`test-slow`, agent/MCP e2e targets, and similar).

### Constraints and assumptions

- Surface of change is the parallel test runner orchestrator introduced in
  PYPOST-1149 (operator-facing contract documented in
  `doc/dev/parallel_test_runner.md`).
- TIMEOUT applies to the orchestrator’s wait for each worker response/
  completion, not as a redesign of in-module pytest timeout markers.
- Default 30 seconds is the mandated product default; operators who need longer
  waits must raise TIMEOUT via the documented configuration.
- “Structured message” means an operator-visible, machine-friendly timeout
  signal consistent with the runner’s existing observability style—not a
  vague free-form note.
- Related debt context only: the wall-clock timeout follow-up called out under
  PYPOST-1153 / `ai-tasks/PYPOST-1149/60-tech-debt.md`; other 1153 items stay
  out of scope.

## Non-Functional Requirements

- **Boundedness**: No indefinite orchestrator wait for a single worker; every
  wait ends by success, normal failure, or TIMEOUT.
- **Fail-fast clarity**: Timeout is distinguishable from ordinary test failure
  in logs/reporting so operators can act.
- **Configurability**: Default remains 30; overrides must be discoverable via
  documented CLI and/or environment names.
- **Reliability of the gate**: After timeout handling, the overall run still
  terminates with a definitive outcome suitable for CI.
- **Scope discipline**: Only the worker-wait timeout behavior and its tests/
  docs; no drive-by PYPOST-1153 maintainability work.

## Main Entities

- **Orchestrator**: Coordinates discovery, starts workers, collects outcomes,
  and produces the run summary for `make test` / `make test-cov`.
- **Worker**: One unit of work the orchestrator starts and waits on (typically
  one test-file subprocess in the parallel runner model).
- **TIMEOUT**: Maximum seconds the orchestrator may wait for a given worker’s
  completion or response; default 30; operator-configurable.
- **Timed-out worker outcome**: Failure classification used when the wait
  bound is exceeded before the worker responds.
- **Operator configuration**: CLI and/or environment means to set TIMEOUT;
  names must be documented for operators.
- **Runner contract docs**: Developer-facing description of orchestrator
  behavior and flags (`doc/dev/parallel_test_runner.md`).

## User Scenarios

1. **Default run, healthy workers**: Operator runs `make test` with no TIMEOUT
   override; workers finish within 30 seconds; suite completes as today aside
   from the new bound being in force.
2. **Hung worker under default TIMEOUT**: A worker never responds; within 30
   seconds the orchestrator marks that worker failed/timed out, logs a clear
   structured timeout message, and the overall run finishes (does not hang).
3. **Raised TIMEOUT for slow workload**: Operator sets a higher TIMEOUT via
   documented CLI and/or env; a worker that finishes after 30 seconds but
   before the raised bound is not treated as timed out.
4. **Regression protection**: Automated tests demonstrate that exceeding
   TIMEOUT yields the timed-out/failed outcome and the structured timeout
   signal, without relying on a real multi-minute hang in CI.
5. **Contract documentation**: After delivery, an operator reading
   `doc/dev/parallel_test_runner.md` can learn the default, how to override
   TIMEOUT, and what happens on timeout.

## Q&A

**Why bound the orchestrator wait at all?**
Without a wall-clock cap, one hung worker can stall the entire quality gate
indefinitely—unacceptable for CI and for local developer loops.

**Why is the business default 30 seconds?**
The product requirement (Jira PYPOST-1192) mandates default TIMEOUT = 30.
Operators who need longer per-worker waits raise TIMEOUT via configuration.

**Is this the same as pytest-timeout markers in each test module?**
No. Those markers bound individual tests inside a worker. This task bounds how
long the **orchestrator** waits for a **worker** to respond. Changing module
markers is out of scope unless strictly needed to align with the default.

**How does this relate to PYPOST-1153?**
PYPOST-1153 bundles several PYPOST-1149 maintainability follow-ups, including
optional per-file orchestrator wall-clock timeout. This story delivers that
timeout behavior only; argparse, Makefile tests, cov-fail-under, and other
1153 items remain out of scope.

**What must operators see on timeout?**
A clear structured message that the wait for that worker exceeded TIMEOUT, plus
a failed/timed-out classification so the run is not mistaken for success.

**Must both CLI and environment configuration exist?**
The requirement is that TIMEOUT is configurable via CLI flag and/or
environment variable, with chosen names documented. Architecture/docs decide
the exact names and whether one or both mechanisms ship; at least one
operator-facing override path is mandatory, and documentation must match.

**Does a timed-out worker fail the overall run?**
Yes. A timed-out worker is treated as failed/timed out; it must not be counted
as success, and it must not leave the orchestrator waiting forever.
