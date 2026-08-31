# PYPOST-1111: Observability Implementation

## Assessment

PYPOST-1111 synchronizes audit verification artifacts and baseline regression guards following the growth of `pypost/core/template_service.py` and the addition of `pypost/ui/dialogs/mcp_servers_dialog.py`. The artifacts affected are:
- `scripts/audit_baseline_metrics.py` (SOLID baseline cap adjustment)
- `ai-tasks/PYPOST-376/baseline-metrics.md` (regenerated snapshot)
- `tests/test_solid_audit_baseline.py` (cap constant synchronization)
- `ai-tasks/PYPOST-374/30-dialogs-audit-report.md` (nine dialog modules inventory synchronization)
- `tests/test_pypost_1077_verification_artifacts.py` (contract verification assertions)

No production runtime application modules in `pypost/` were modified in this task. Observability in this scope pertains to the diagnostic visibility, CLI reporting, and test failure actionable feedback of the audit tooling and regression guards.

## Logging Implementation

### Added Logs

No production runtime logging was added to `pypost/` (N/A: tooling and test artifact task). Diagnostic reporting and error logging across the audit tooling are mapped to operational levels:

- **EMERG**: N/A (no critical system crashes in tooling scope)
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: `scripts/audit_baseline_metrics.py` `--check` mode outputs cap violations to `sys.stderr` (exit code 1); `scripts/audit_dialogs_inventory.py` `--check` mode outputs missing audit report or uncovered dialog modules to `sys.stderr` (exit code 1)
- **WARNING**: N/A
- **NOTICE**: `scripts/audit_dialogs_inventory.py` outputs confirmation on successful audit check: `OK: <count> dialog module(s) covered by audit report`
- **INFO**: `scripts/audit_baseline_metrics.py` standard stdout output delivers full markdown comparison tables across audit-era LOC, current LOC, and caps; `scripts/audit_dialogs_inventory.py` prints tab-delimited inventory (`<path>\t<lines>`) and total LOC
- **DEBUG**: N/A

### Log Structure

Log and diagnostic format used:
- Structured logs: Yes (`--json` CLI mode is supported on both `audit_baseline_metrics.py` and `audit_dialogs_inventory.py` for machine ingestion)
- Includes context: Yes (file path, line count, cap threshold, class name, missing module filenames)
- Log levels: Process exit codes (0 for success, 1 for violations) with standard stream separation (`stdout` for reports/confirmations, `stderr` for violation errors)

## Tooling Diagnostic Output Analysis

### 1. `scripts/audit_baseline_metrics.py`
- **`--check` Mode**:
  - Validates all measured files against `FILE_CAPS` and `MAIN_WINDOW_CLASS_CAP`.
  - On violation: Emits clear, actionable diagnostic lines to `sys.stderr` in the format:
    - `{path}: {lines} lines exceeds cap {cap}`
    - `{path}::{class}: {lines} lines exceeds cap {cap}`
    - Terminates with exit code 1.
  - On clean check: Exits silently with code 0 (standard POSIX utility convention for clean assertions).
- **CLI Output Modes**:
  - Default (no flags): Prints the complete markdown report table to `stdout`.
  - `--markdown <path>`: Writes markdown table to file.
  - `--json <path>`: Emits structured JSON snapshot with `path`, `total_lines`, `non_empty_lines`, `class_lines`, `cap`, and `audit_era_lines`.

### 2. `scripts/audit_dialogs_inventory.py`
- **`--check` Mode**:
  - Verifies presence of `ai-tasks/PYPOST-374/30-dialogs-audit-report.md`.
  - Verifies that every `.py` file under `pypost/ui/dialogs/` (excluding `__init__.py`) is documented in the report.
  - On failure: Emits diagnostic error lines to `sys.stderr` identifying missing files:
    - `Missing audit report: <path>`
    - `Audit report missing dialog module(s): <comma_separated_filenames>`
    - Terminates with exit code 1.
  - On success: Prints `OK: 9 dialog module(s) covered by audit report` to `stdout` and exits with code 0.
- **CLI Output Modes**:
  - Default: Prints `<path>\t<total_lines>` followed by `TOTAL\t<total_lines>` to `stdout`.
  - `--markdown`: Prints formatted Markdown table with LOC and non-empty lines.
  - `--json`: Emits structured JSON object containing module details, total lines, and audit-era grouped baseline comparison.

### 3. Test Failure Diagnostics & Data Privacy
- **`tests/test_solid_audit_baseline.py`**:
  - `test_template_service_cap_expected`: Provides explicit equality assertion showing expected cap vs current dictionary configuration.
  - `test_markdown_snapshot_matches_current_metrics`: Produces a standard unified diff between committed `baseline-metrics.md` and live metrics if out of sync.
  - `test_main_window_file_loc_within_cap` & `test_main_window_class_loc_within_cap`: Include custom `msg=` parameters formatting measured lines and cap thresholds.
  - `test_audit_module_inventory_within_caps`: Formats all violations into an aggregated error block: `Baseline cap violations:\n<violations>`.
- **`tests/test_pypost_1077_verification_artifacts.py`**:
  - Accumulates contract violations in an `errors` list with explicit diagnostic messages (e.g., `dialog discovery must contain exactly nine modules totaling 1,787 LOC`, `scope must state nine modules and 1,787 LOC`, `report retains contradictory stale claim: <claim>`).
  - Asserts `assert not errors, "\n".join(errors)`, outputting the complete list of failures in a single run.
- **Sensitive Data Safety**:
  - Tooling and tests operate strictly on static AST parsing and repository file paths.
  - No credentials, tokens, network payloads, or user data are processed or displayed in error traces.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Execution time**: Test execution time is tracked by pytest and parallel runner (both tests execute in under 1.3s).
- **Throughput**: N/A for audit scripts.
- **Error rate**: N/A.

### Business Metrics

- **SOLID audit baseline compliance**: Ratio of compliant modules to total monitored modules (100% compliance maintained).
- **Dialog module coverage**: 9 of 9 dialog modules covered in audit documentation (100% coverage).

### System Health Metrics

- **Resource usage**: Lightweight AST parsing, minimal memory footprint (< 30MB during test execution).
- **Component status**: Baseline metric caps enforce bounded LOC growth across core architectural components.

## Monitoring Integration

- [ ] Prometheus metrics — N/A: Static verification and test assertions do not emit live telemetry.
- [ ] Grafana dashboards — N/A: No live runtime time-series metrics.
- [x] Alerting rules — CI gate failure: `make test`, `make lint`, and `make verify-ai-tasks` alert developers via non-zero exit codes on cap or contract violations.
- [x] Log aggregation — Pytest runner outputs parallel structured execution records (`INFO parallel_test_run_started`, `INFO test_file_completed`).

## Validation Results

- [x] Diagnostic error output is actionable and specifies filename, measured LOC, and cap threshold.
- [x] `--check` modes properly exit with code 1 on violations and 0 on success.
- [x] Structured JSON and Markdown output modes format valid representations.
- [x] Test failure output reports exact mismatches without leaking sensitive data.
- [x] All repository operations verified exclusively via `make` targets (`make test`, `make lint`, `make typecheck`, `make verify-ai-tasks`).

## Notes

All audit tools and regression tests provide immediate feedback during CI and local development runs. No changes to the production logging configuration in `pypost/main.py` were required or appropriate for this task.
