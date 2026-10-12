# PYPOST-1303: Observability Implementation

## Logging Implementation

### Diagnostic Boundary

This change is a local developer/CI quality gate. Its observability contract is actionable
CLI feedback and a nonzero exit status on failure; no application service or production
request path changes. Existing validated diagnostics satisfy the task without new logging.

The checker writes findings, baseline-maintenance instructions, and success summaries to
stdout. Tool, source, and baseline validation failures go to stderr with the prefix
`Test lint failed:`. Make propagates a failed checker result through the normal quality gate.

### Output Structure

| Outcome | Feedback | Checker exit |
| --- | --- | ---: |
| New finding | Live `path:row:column: code message` for each new occurrence | 1 |
| Resolved allowance | File, code, fixed count, and `make lint-tests-prune` guidance | 1 |
| Successful scan | `Test lint OK (N accepted legacy occurrences).` | 0 |
| Successful explicit prune | Summary of the remaining accepted occurrences | 0 |
| Invalid baseline/source/tool result | Specific reason prefixed with `Test lint failed:` | 2 |
| Timeout or launch failure | Subprocess error with the same failure prefix | 2 |

New diagnostic locations use the current flake8 row and column, even though baseline identity
deliberately excludes those unstable coordinates. Extra duplicate occurrences remain visible.
F401, E501, and T201 feedback identifies the affected private test file in the Make regressions.

Validation failures preserve their relevant context: invalid fields/paths or source rows,
JSON decoding details, missing-file paths, tool exit status and captured tool diagnostics,
or the subprocess timeout. The plugin requirement prevents a missing flake8-print installation
from silently losing T201 feedback.

These are deliberate CLI messages rather than syslog events or application ERROR logs.
No log-level mappings, background logger, or persistent audit stream were added.

## Metrics Implementation

Production metrics are N/A. The checker does not serve requests, process application data,
or introduce a long-running component requiring operational instrumentation. Adding telemetry
or dependencies would expand scope without helping the developer identify a lint defect.

The success line exposes the accepted legacy-occurrence count (currently 409); fixed allowance
messages expose resolved counts. Existing Make/parallel-runner summaries provide gate duration
and test results. No new metric collector is needed for this finite local command.

## Monitoring Integration

No Prometheus/Grafana integration, alerting rules, or log aggregation changes are required.
The existing developer and CI Make invocations consume stdout, stderr, and exit status.

## Validation Results

Reused accepted verification evidence; this step changed no runtime code or tests.

- Actual Make regressions in `tests/test_makefile_test_lint_gate.py` verify clean success,
  actionable new F401/E501/T201 feedback, and preserved production F401 failure.
  Green command: `make test PYTEST_ARGS='tests/test_makefile_test_lint_gate.py'`.
  Log: `/tmp/pypost-1303-step4-gate.log`.
- `tests/test_test_lint_baseline.py` verifies accepted-count summaries, duplicate feedback,
  stale-entry prune guidance, missing baseline errors, timeout/launch stderr, and failure
  behavior for invalid tool output, plugin absence, contradictory results, schemas, and source
  lookup/escape errors. Latest command:
  `make test PYTEST_ARGS='tests/test_test_lint_baseline.py'`.
  Log: `/tmp/pypost-1303-step5-tests.log`.
- `make lint` reports exactly `Test lint OK (409 accepted legacy occurrences).` before the
  unchanged production/docs checks. Log: `/tmp/pypost-1303-step5-lint.log`.
- Normal success does not print the baseline entries, source fragments, reason strings, or
  any large data structure. Failure output is limited to actionable current diagnostics,
  resolved identities/counts, and relevant execution errors.

## Notes

Production logging and metrics remain outside this developer-tool boundary. The accepted
full gate's tracked PYPOST-1363 reporter and PYPOST-1361 snapshot failures remain unchanged;
the checker surfaces tool failures rather than treating unavailable diagnostics as success.
