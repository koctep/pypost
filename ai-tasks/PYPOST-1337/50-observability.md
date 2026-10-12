# PYPOST-1337: Observability Implementation

## Logging Implementation

### Added Logs

The target component [scripts/check_mypy_baseline.py](file:///home/src/scripts/check_mypy_baseline.py) is a standalone developer and CI quality-gate CLI tool rather than a long-running service daemon. Logging and operational diagnostics are surfaced via process exit codes, structured standard streams (`stdout` vs. `stderr`), and human-readable diagnostic reports.

Summary of diagnostic logging levels mapped to standard streams:
- **EMERG**: N/A - Standalone developer/CI tool.
- **ALERT**: N/A - Standalone developer/CI tool.
- **CRIT**: [scripts/check_mypy_baseline.py:247-260](file:///home/src/scripts/check_mypy_baseline.py#L247-L260) - Process execution failures (mypy timeout, fatal crash returncode >= 2, or non-zero exit code with empty parsed error list). Emitted to `stderr` with raw subprocess stderr/stdout to ensure immediate diagnostic context in CI logs.
- **ERR**: [scripts/check_mypy_baseline.py:266-289](file:///home/src/scripts/check_mypy_baseline.py#L266-L289) - Quality gate check failures: missing baseline file, malformed baseline JSON, or detected differences (new unbaselined errors, resolved errors). Emitted to `stderr`.
- **WARNING**: N/A - All baseline diffs or execution failures are hard errors (fail-closed quality gate).
- **NOTICE**: [scripts/check_mypy_baseline.py:263](file:///home/src/scripts/check_mypy_baseline.py#L263) - Baseline update confirmation (`Updated mypy-baseline.json: X errors`). Emitted to `stdout`.
- **INFO**: [scripts/check_mypy_baseline.py:291](file:///home/src/scripts/check_mypy_baseline.py#L291) - Successful verification summary (`mypy baseline OK (X known errors in ...)`). Emitted to `stdout`.
- **DEBUG**: N/A - Detailed error breakdowns and per-error lines are formatted directly in diff reports on gate failure.

### Log Structure

Log format used:
- Structured logs: CLI standard streams (`stdout` for informational status / success; `stderr` for diagnostics, failures, and error diffs)
- Includes context: Yes (includes source file paths, error codes, error messages, and line numbers where applicable)
- Log levels: `CRIT` (process failure to `stderr`), `ERR` (gate mismatch / validation failure to `stderr`), `NOTICE` / `INFO` (clean status to `stdout`)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: N/A - Execution bounded by `MYPY_TIMEOUT_SECONDS = 60` with exit code 124 on timeout.
- **Throughput**: N/A - Ephemeral command-line invocation.
- **Error rate**: N/A - Communicated via process exit code (0 = success, 1 = failure).

### Business Metrics

Business metrics:
- **Baselined error count**: Count of frozen errors stored in `mypy-baseline.json` and reported on stdout/stderr.

### System Health Metrics

System health metrics:
- **Resource usage**: Managed by OS process lifecycle during CI / local test runs.
- **Component status**: Process exit status:
  - `0`: Baseline matches current codebase or baseline rewritten successfully.
  - `1`: Execution failure, missing/corrupted baseline, or baseline error count mismatch.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A - CLI quality gate)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A - CI build status / test runner exit code integration)
- [x] Log aggregation (Captured by CI runner stdout/stderr logs e.g. GitHub Actions / GitLab CI)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (standard CLI output conventions: diagnostics to `stderr`, success to `stdout`)
- [x] Metrics are collected correctly (N/A for standalone CLI tool)
- [x] Logging works in error scenarios (tested via `tests/test_mypy_baseline.py::TestMypyBaselineExecutionIntegrity`)
- [x] Large data structures are not logged (concise per-key reports, summaries of error counts)
- [x] Metrics are available for monitoring (CI job status reflects exit code)

## Notes

In PYPOST-1337, error stream observability was reinforced specifically for execution anomalies where mypy failed to run properly (e.g. missing mypy installation, fatal internal mypy syntax/typechecker crashes, or misconfigured invocation paths). Previously, non-zero exit codes with empty parsed errors could produce misleading results or allow `--update-baseline` to wipe out the baseline. With the changes in Step 4, unhandled non-zero exit codes immediately flush full raw subprocess stderr output to `sys.stderr` and exit with code 1.
