# PYPOST-1263: Observability Implementation

## Scope Decision

The change is test-only. `git diff` touches only
`tests/test_collection_import_profile.py`, and the new regression module
`tests/test_collection_import_profile_clock.py` is test code. No production module, runtime
path, or configuration changed (AC-8). There is no new production behavior to log or measure,
so this step adds **no production logging and no production metrics**.

Adding timing logs or metrics to `plan_collection_import` would change production code, which
AC-8 and the Step 2 architecture rule out. The requirements do not call for runtime planner
telemetry.

## Logging Implementation

### Added Logs

None. No production code changed, so no log levels from EMERG through DEBUG apply.

### Existing Production Logs (unchanged, for context)

`pypost/core/collection_import.py` already logs the planner outcome:

- **INFO**: `plan_collection_import` emits `collection_import_plan_created` with
  added/updated/skipped/renamed counts plus request and websocket totals. These are scalar
  fields only, with no large structures.
- **INFO / WARNING**: candidate loading logs `collection_import_file_parsed` and its
  read or parse failures.

This task does not touch these logs. They already cover functional planner outcomes.

### Log Structure

- Structured logs: N/A (no logs added)
- Includes context: N/A
- Log levels: N/A

## Test-Level Diagnostics (AC-7)

The relevant diagnostic surface is the benchmark's assertion message, which is a maintainer
signal and not production telemetry:

- `tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`
  gates on current-thread CPU time (`time.thread_time()`). It is rejected when the CPU time is
  100ms or more. The failure message is:
  `plan_collection_import used <cpu>ms thread CPU, exceeding 100ms CPU budget
  (wall elapsed: <wall>ms)`.
- Reporting CPU and wall time together lets a maintainer tell real planner work (high CPU)
  from scheduling or contention delay (wall time much higher than CPU time). It does this
  without adding any data to the logs.
- The message only reports two scalar timings. It does not dump fixture or plan data.
- `tests/test_collection_import_profile_clock.py` checks this message. It matches the CPU
  attribution in the rejection cases (`excess-planner-work`, `strict-cpu-boundary`,
  `synthetic-low-wall-high-cpu`). It also checks that wall-only delay
  (`external-descheduling`) is accepted.

## Metrics Implementation (if applicable)

Not applicable. The change is test-only, and the project has no metrics pipeline covering
import planning that would apply here.

### Performance Metrics

None added.

### Business Metrics

None added.

### System Health Metrics

None added.

## Monitoring Integration

- [ ] Prometheus metrics: N/A
- [ ] Grafana dashboards: N/A
- [ ] Alerting rules: N/A
- [ ] Log aggregation (ELK, Loki, etc.): N/A

## Validation Results

- [x] Logs are correctly formatted: no logs added; existing planner logs are unchanged
- [ ] Metrics are collected correctly: N/A (no metrics)
- [x] Logging works in error scenarios: the rejection message is covered by the clock tests
- [x] Large data structures are not logged: the message has two scalar timings only
- [ ] Metrics are available for monitoring: N/A

`make verify-ai-tasks` was run on 2026-10-08 after this artifact was written. It passed (exit 0)
and printed "ai-tasks artifacts baseline OK (394 completed tasks; 2 grandfathered legacy gaps)".
The result is recorded under STEP 6 in `00-roadmap.md`.

## Notes

If a later task wants runtime planner latency telemetry (for example, CPU and wall timing in
`collection_import_plan_created`), it needs its own Jira ticket. This task's scope excludes
production changes.
