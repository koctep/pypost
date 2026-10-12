# PYPOST-1298: Observability Implementation

## Scope and Completion Criteria

This change affects Make integration fixture infrastructure and the parallel test runner.
It introduces no application request path or production service. Observability is complete
when preparation failures identify the failing operation and relevant deadline, rejected runs
retain actionable diagnostics and report failure before dispatch, and existing lifecycle events
allow a developer or CI operator to correlate the outcome with a run.

No additional logging or metrics code was necessary in Step 6. The accepted implementation
already provides the diagnostics below. Production application monitoring remains outside this
issue's scope; readiness for this step means usable test-runner and CI diagnostics.

## Logging Implementation

### Existing Helper Diagnostics

`tests/makefile_test_helpers.py::_get_shared_base_venv` raises explicit failures rather than
logging each lock poll or subprocess output:

- A deadline failure identifies the stage (`lock`, `creation`, `installation`, `validation`,
  or `publication`), shared environment path, and cumulative preparation budget.
- Failed bootstrap commands identify the stage, environment path, budget, subprocess failure,
  and captured stderr or stdout. Missing interpreter validation identifies its path.
- `_materialize_prewarmed_venv` identifies the failed destination and subprocess exception.
  Timeout exceptions include the command timeout; the copy command receives 20 seconds and
  one additional second for process termination. Failed partial copies are removed.
- Timeout and nonzero subprocess failures terminate the process group. A later attempt can
  recover under the lock without a falsely published readiness marker.

These exceptions surface through pytest failure diagnostics, or through the runner's rejected
preparation summary when initialization occurs before dispatch. They are diagnostics rather
than separate structured logging records. Successful cache reuse and lock polling remain quiet.

### Existing Runner Events

`scripts/run_parallel_tests.py::run_parallel_tests` converts failed pre-dispatch preparation
into a `RunnerValidationError` with code `fixture_preparation`. The result retains captured
stderr or stdout, returns a nonzero summary with zero scheduled units, and writes the requested
JSON report. Both normal and coverage runs take this fail-closed path.

The runner emits its existing structured events:

- **WARNING**: `parallel_test_validation_failed`, with `run_id`, phase, code, and worker count.
  Preparation failures use `phase=fixture_preparation` and `code=fixture_preparation`.
- **INFO**: `parallel_test_run_completed`, with the same `run_id`, outcome, scheduled units,
  file counts, elapsed and cumulative durations, coverage status, failure phase, and code.
- **INFO**: existing start, discovery, worker-pool, and successful-file lifecycle events.
- **ERROR**: existing failed-file events retain file, exit-code, and duration context.
- **NOTICE**: existing slowest-file events identify file and duration.

Structured records use scalar key/value fields. The validation event deliberately does not
repeat error text, subprocess output, target lists, or other large structures. Detailed captured
command output remains available in the failure result/report; it is not claimed to have a
new truncation limit. No log level or handler configuration changed in this step.

## Metrics and Monitoring Integration

New Prometheus instruments, Grafana dashboards, alert rules, business metrics, and application
health metrics are N/A: the affected code is local test infrastructure rather than a deployed
application component. Adding a monitoring dependency would exceed the ticket's scope.

Existing run/file durations, counts, scheduling totals, speedup, and coverage outcome are
available through runner events and its JSON report. They support diagnosing CI failures and
slow files without a new metrics backend. They do not measure individual preparation stages;
the explicit stage failures and configured budgets are the necessary diagnostic contract here.

## Validation Results

- Reviewed the helper deadline, bootstrap, interpreter validation, and materialization error
  branches, plus the runner's preparation rejection and terminal event paths.
- Step 6 `make lint` passed, including Markdown lint and relative documentation links.
- Reused Step 5's unchanged focused validation: 13 readiness cases and 60 runner cases passed
  through `make test PYTEST_ARGS='tests/test_makefile_shared_readiness.py
  tests/test_run_parallel_tests.py --tb=short'` (arguments form one line).
  Log: `/tmp/pypost-1298-step5-focused.log`; runner wall time was 18.22 seconds.
- The readiness tests cover stage-specific lock expiry, cumulative budgets, stale publication,
  timeout/nonzero recovery, bounded materialization retry, and real descendant termination.
- The preparation regression covers normal/coverage success and timeout/nonzero failure,
  zero dispatch after failure, a nonzero summary, and a nonpassing JSON report. It primarily
  asserts behavior rather than exact preparation log text; no new log assertion is claimed.
- Existing caplog tests cover failed-file ERROR context, scalar validation events, correlated
  terminal summaries, and lifecycle/coverage records. The preparation phase's exact event
  fields were verified by source inspection; the configuration and CLI validation caplog
  regressions exercise the shared event helpers.
- The focused-run log contains scalar discovery, file, worker-pool, and completion records,
  including counts and elapsed time; no full discovery structure is logged.

The prior full gate is baseline-relative: seven independently triaged failures remain as
recorded in `00-roadmap.md` and `40-code-cleanup.md`. This report does not claim a green full
suite. No implementation or tests changed in Step 6, so no full-suite rerun is justified.
The orchestrator owns independent review and acceptance; STEP 6 remains `[/]` until then.
