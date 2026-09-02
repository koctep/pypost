# PYPOST-1251: Observability Implementation

## Diagnostic Observability Contract

The alert-reload crash boundary is observed by
`tests/test_main_window_alert_reload_crash_repro.py`, which runs the existing
alert-reload scenario in isolated child processes. The parent test treats the
operating-system process result as part of the test outcome, so assertions that
complete before a native failure cannot mask that failure.

Each child outcome is classified as exactly one of:

- `normal_exit` — the child returns zero.
- `nonzero_exit` — the child returns a positive non-zero exit code.
- `signal_exit` — the child is terminated by a signal (negative return code).
- `timeout` — the child exceeds the bounded 20-second subprocess timeout.

For every outcome, the diagnostic report records:

- the exact Python/pytest command;
- the configured `QT_QPA_PLATFORM=offscreen` and `PYTHONFAULTHANDLER=1`
  environment metadata;
- elapsed duration;
- the outcome classification; and
- bounded stdout and stderr tails when process output is available.

The child target is run once as a clean control and three additional times to
observe repeatability. A non-`normal_exit` result fails the parent test with
the command, configured environment, duration, classification, and output
evidence. The harness uses the subprocess return code internally to
distinguish `nonzero_exit` from `signal_exit`, but the report does not emit the
numeric return code or signal name. This keeps native crashes, assertion
failures, and hangs distinguishable for CI diagnosis without emitting large
process outputs.

## Logging and Metrics Decision

No production logging or metrics were added. The issue concerns a native test
process boundary, and the reviewed evidence does not identify a PyPost-owned
runtime failure requiring an application telemetry hook. Adding alert-service
logs, counters, or dashboards would expand the task beyond its crash
classification scope and would not improve detection of a child-process
signal or timeout.

The test harness's structured failure report is the appropriate diagnostic
observability for this task. Existing application alert behavior and telemetry
semantics remain unchanged.

## Monitoring Integration

No external monitoring integration is applicable to this test-only diagnostic
contract:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

- [x] Outcome classification covers normal exit, non-zero exit, signal exit, and timeout.
- [x] Reports include command, environment, duration, and bounded output evidence.
- [x] Clean control and repeated isolated alert-reload runs are covered.
- [x] Focused bounded tests pass in the available environment.
- [x] Repository lint passes.
- [x] AI-task artifact verification passes.
- [x] No large data structures or unbounded process output are logged.

## Verification Commands

```text
make lint
make test PYTEST_ARGS="tests/test_main_window_alert_reload_crash_repro.py -q -m 'slow or not slow'" WORKERS=1 WORKER_TIMEOUT=30
make verify-ai-tasks
```

The current evidence-backed classification remains N/A for reproducing the
reported native crash: bounded isolated attempts complete normally in the
available environment. This is documented as classification evidence, not as
proof that an unavailable runtime-specific failure has been fixed.
