# PYPOST-1299: Observability Implementation

## Logging Implementation

### Existing Diagnostics

The task changes isolated missing-runner test preparation. Production application code,
Make recipes, and monitoring behavior are unchanged. No additional logs are needed.

The real `test` and `test-cov` Make guards emit
`parallel runner unavailable: scripts/run_parallel_tests.py is missing` on stderr and
exit unsuccessfully. Both original checks capture stdout/stderr and assert the diagnostic
alongside a nonzero return code. They also verify root coverage-fragment removal and
preservation of the base file and nested fragment, so diagnostics alone cannot mask
incorrect cleanup.

The offline repro adds contextual assertions for an unexpected preparation subprocess,
missing interpreter or readiness stamps, and stale stamps that would trigger installation.
It requires exactly one real Make target invocation and rejects installation/venv creation
output. These are test-failure diagnostics, not production log events.

### Diagnostic Structure

- Make diagnostics are plain stderr text with the missing runner path; no structured
  logging format or syslog severity is introduced.
- Assertion messages identify the violated preparation or coverage contract. An unexpected
  preparation command is shown; no application payload or large data structure is logged.
- Both original target subprocesses retain 60-second bounds. The offline repro caps real
  subprocess execution at 10 seconds and declares a 20-second module timeout.

## Metrics Implementation

Production performance, business, and system-health metrics are N/A. This change prepares
temporary test workspaces with local interpreter links and readiness stamps; it does not
create a production execution path or monitoring component.

The repro's monotonic elapsed-time assertion checks completion within 10 seconds. This is
a bounded regression assertion, not an exported performance metric.

## Monitoring Integration

No Prometheus collectors, dashboards, alerting rules, or log-aggregation integration are
required for the fixture correction. Existing application monitoring remains outside this
ticket's scope.

## Validation Results

- Accepted Step 4 focused verification passed the original exit-policy module, both offline
  repro cases, timeout-budget contracts, and adjacent follow-up regressions in 22.84 seconds.
- Under the ordinary full-gate worker load, the original module passed in 8.22 seconds and
  the offline repro in 2.26 seconds, preserving the real missing-runner error diagnostics.
- The full gate still reported five previously tracked failures: PYPOST-1363 reporter
  errors and PYPOST-1361 audit-snapshot drift. It was not wholly green.
- Step 5 `make lint` passed. No executable code changed in Step 6, so accepted behavioral
  evidence was reused without repeating tests.
- There are no new production ERROR log paths requiring a `caplog` assertion; the Make
  stderr failure path is directly asserted by the original tests.

## Notes

This report documents sufficient existing diagnostics and the new repro's assertion
context. It does not claim that logs or production metrics were added.
