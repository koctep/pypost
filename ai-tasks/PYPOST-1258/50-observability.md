# PYPOST-1258: Observability Implementation

## Logging Implementation

### Added Logs

No production runtime logging was added to core PyPost application modules. This task introduces
dedicated unit tests for audit script CLI argument parsing and error handling. Observability for
these CLI tools and their test harness is characterized by standard stream routing, exit codes,
and stream interception:

- **EMERG**: N/A — no critical system failures.
- **ALERT**: N/A — no urgent operational conditions requiring immediate intervention.
- **CRIT**: N/A — no critical runtime error paths in CLI tooling.
- **ERR**:
  - `scripts/audit_baseline_metrics.py`: writes line cap violations to `sys.stderr` on `--check`
    failure (e.g., `f"{path}: {total_lines} lines exceeds cap {cap}"`) and exits with code 1.
  - `scripts/audit_dialogs_inventory.py`: writes missing report errors and missing dialog entries
    to `sys.stderr` on `--check` failure and exits with code 1.
  - `argparse` syntax and usage errors: both scripts write unrecognized arguments and missing
    options to `sys.stderr` and raise `SystemExit(2)`.
- **WARNING**: N/A — scripts emit deterministic binary compliance results without warnings.
- **NOTICE**:
  - `scripts/audit_dialogs_inventory.py`: writes confirmation message to `sys.stdout` when
    `--check` passes cleanly (e.g., `OK: N dialog module(s) covered by audit report`).
- **INFO**:
  - `scripts/audit_baseline_metrics.py`: writes markdown audit summary table to `sys.stdout`
    when invoked without export flags.
  - `scripts/audit_dialogs_inventory.py`: writes default TSV inventory or formatted Markdown
    table (`--markdown`) to `sys.stdout`.
  - Pytest test runner: emits test execution outcomes, timings, and pass/fail status.
- **DEBUG**: N/A — verbose debug diagnostics are not emitted; scripts operate quietly.

### Log Structure

Log format used:

- Structured logs: yes — both scripts produce structured JSON payloads (`--json`), structured
  tabular text (TSV / Markdown tables), and structured test reporting via pytest.
- Includes context: yes — error diagnostics include module path, line counts, configured cap
  limits, missing file identifiers, and argument syntax details.
- Log levels: mapped to process exit codes (0 = OK/INFO, 1 = ERR/violation, 2 = ERR/usage)
  and stream separation (stdout for reports, stderr for error diagnostics).

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: test case execution time monitored via pytest, with a 30s timeout
  per test enforced by `@pytest.mark.timeout(30)`.
- **Throughput**: N/A — developer tooling executed on-demand in CI or local development.
- **Error rate**: test failure counts and CLI exit code rates in CI quality gates.

### Business Metrics

Business metrics (codebase quality metrics tracked by audit scripts):

- `total_lines`: total lines of code per tracked module and aggregate dialog inventory.
- `non_empty_lines`: non-blank lines of code per tracked module.
- `class_lines`: line count of guarded classes (e.g., `MainWindow` bounded by 460 lines).
- `cap`: target ceiling for architectural boundaries and regression prevention.
- `audit_era_lines`: historical baseline lines for legacy comparison.

### System Health Metrics

System health metrics:

- **Resource usage**: minimal CPU and memory consumption during AST parsing and file inspection.
- **Component status**: codebase compliance status (pass/fail) integrated into CI quality gates.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A; audit scripts and unit tests run in batch CI pipelines.
- [ ] Grafana dashboards — N/A; metrics exported as JSON/Markdown files rather than time-series.
- [x] Alerting rules — CI quality gates fail on non-zero exit codes (1 for check, 2 for syntax).
- [x] Log aggregation (ELK, Loki, etc.) — CI runner log capture aggregates stdout and stderr.

## Validation Results

Validation results:

- [x] Logs are correctly formatted — standard stream separation adheres to CLI standards.
- [x] Metrics are collected correctly — JSON snapshots and Markdown reports validate accurately.
- [x] Logging works in error scenarios — stderr diagnostics tested for syntax and cap violations.
- [x] Large data structures are not logged — output bounded to summary tables or file exports.
- [x] Metrics are available for monitoring — exit codes and reports available to CI runners.

## Notes

The test suite in `tests/test_audit_scripts_cli.py` verifies observability contracts directly:
- Uses pytest fixture `capsys` to capture and verify `sys.stdout` and `sys.stderr` independently.
- Verifies exit code 0 on clean runs and successful exports.
- Verifies exit code 1 with stderr output on check violations.
- Verifies exit code 2 with stderr usage messages on syntax and argument errors.
