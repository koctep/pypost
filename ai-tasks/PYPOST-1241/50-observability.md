# PYPOST-1241: Observability Implementation

## Scope Note

PYPOST-1241 encompasses two primary technical domains:
1. **Static Typechecking Quality Gate Architecture & Ratchet Enforcement**:
   - `scripts/check_mypy_baseline.py`: Command-line interface and CI quality gate verifying error counts and exact `(path, code, message)` multiset diffs.
   - `mypy-baseline.json`: Frozen machine-readable baseline (version 2 schema).
   - `tests/test_mypy_baseline_live.py`: Automated regression guard running mypy and validating ratchet stability.
2. **Save Orchestration & Stream Export Alignment**:
   - `RequestSaveOrchestrator`, `WebSocketSaveOrchestrator`, `McpClientSaveOrchestrator`: Multi-format persistence coordinators with overwrite guards, stale detection, and GUI metrics tracking.
   - `websocket_stream_export.py` & `websocket_stream_export_worker.py`: Background worker and disk writers for stream transcript serialization.
   - Presenter integration in `tabs_presenter.py`, dialogs, and actions.

"Observability" for this task covers both runtime operational telemetry (structured application logging, GUI action metrics) and CI quality-gate observability (machine-readable baseline diff reporting, deterministic non-zero exit codes).

## Logging Implementation

### Added Logs

During Step 6, existing logging across all touched modules was audited. Save cancellation diagnostics were enhanced in the newly-aligned generic save orchestrators to eliminate silent returns when new item save dialogs are dismissed:

- **EMERG**: None (not applicable to client application persistence/linting components).
- **ALERT**: None.
- **CRIT**: None.
- **ERR**:
  - `pypost/ui/presenters/tabs_presenter.py:916,968,1017` — `save_request_overwrite_failed reason=missing_snapshot request_id=%s`, `ws_save_overwrite_failed reason=missing_snapshot ws_id=%s`, `mcp_client_save_overwrite_failed reason=missing_snapshot profile_id=%s` (pre-existing, verified).
  - `pypost/core/qt/websocket_stream_export_worker.py:78` — `websocket_stream_export_worker_failed format=%s path=%s error=%s` with `exc_info=True` (pre-existing, verified).
- **WARNING**:
  - `pypost/ui/request_save_orchestrator.py:103,182` — `save_as_flow_failed reason=missing_target_collection`, `save_request_failed reason=missing_target_collection` (pre-existing, verified).
  - `pypost/ui/websocket_save_orchestrator.py:83,168` — `ws_save_as_flow_failed reason=missing_target_collection`, `ws_save_failed reason=missing_target_collection` (pre-existing, verified).
  - `pypost/ui/mcp_client_save_orchestrator.py:85,175` — `mcp_client_save_as_flow_failed reason=missing_target_collection`, `mcp_client_save_failed reason=missing_target_collection` (pre-existing, verified).
- **NOTICE**: None (standard Python stdlib logging does not define syslog NOTICE level).
- **INFO**:
  - `pypost/ui/request_save_orchestrator.py:176` — `save_request_new_cancelled request_id=%s` (**added this step**).
  - `pypost/ui/websocket_save_orchestrator.py:162` — `ws_save_new_cancelled ws_id=%s` (**added this step**).
  - `pypost/ui/mcp_client_save_orchestrator.py:169` — `mcp_client_save_new_cancelled profile_id=%s` (**added this step**).
  - Pre-existing verified operational events:
    - Save as lifecycle: `*_save_as_flow_started`, `*_save_as_flow_cancelled`, `*_save_as_flow_completed`.
    - Overwrite flow: `*_save_overwrite_cancelled`, `*_save_stale_cancelled`, `*_save_overwrite_succeeded`.
    - New save flow: `*_save_new_succeeded`.
    - Transcript export: `websocket_stream_json_exported`, `websocket_stream_text_exported`.
- **DEBUG**:
  - `pypost/core/qt/websocket_stream_export_worker.py:48,70` — `websocket_stream_export_worker_started format=%s path=%s entries_count=%d`, `websocket_stream_export_worker_completed format=%s path=%s` (pre-existing, verified).
  - `pypost/ui/presenters/tabs_presenter.py:157` — `TabsPresenter: alert_manager_injected=%s` (pre-existing, verified).

### Log Structure

- **Structured logs**: Yes. Operational messages follow the repository standard `event_name key1=value1 key2=value2` key-value token format.
- **Includes context**: Yes. Logs include entity IDs (`request_id`, `ws_id`, `profile_id`), target collections (`target_collection_id`), entry counts (`entries_count`), and drop accounting (`capacity_dropped`, `memory_budget_dropped`).
- **Large data structures omitted**: Confirmed. Sensitive payloads, request bodies, auth tokens, and full JSON transcript trees are never logged; only IDs, counts, file paths, and failure reasons are emitted.
- **Log levels used**: `DEBUG`, `INFO`, `WARNING`, `ERROR`.

## CI Quality Gate Observability (scripts/check_mypy_baseline.py)

The quality gate script provides structured console diagnostics for both interactive developer feedback and automated CI monitoring:

- **Regression Detection (Exit code 1)**:
  - Header: `New mypy errors (not in baseline):`
  - Per-item diff: `  + <path>: <message> [<error-code>]`
  - Line numbers: `    lines: <line1>, <line2> (<new_count> new of <total> total)`
- **Ratchet Enforcement (Exit code 1)**:
  - Header: `Resolved baseline errors (update baseline):`
  - Per-item diff: `  - <path>: <message> [<error-code>] (<fixed_count> of <total> baselined)`
- **Summary Count**:
  - `Baseline: <N> errors; current: <M> errors`
- **Clean Baseline Gate (Exit code 0)**:
  - `mypy baseline OK (<N> known errors in pypost/core, pypost/models, pypost/ui)`

## Metrics Implementation (if applicable)

### Performance Metrics

- **Quality Gate Execution**:
  - `scripts/check_mypy_baseline.py` wall-clock duration: ~1.9s in `tests/test_mypy_baseline_live.py`.
  - Parallel runner duration tracked in Makefile test summary.

### Business & User Interaction Metrics

- **GUI Save Action Telemetry**:
  - Tracked via `MetricsTrackerProtocol.track_gui_save_action(action: str)`:
    - `self._metrics.track_gui_save_action("overwrite")` on successful overwrite save.
    - `self._metrics.track_gui_save_action("new")` on successful new request/profile save.
  - Implemented and invoked in all three save orchestrators (`RequestSaveOrchestrator`, `WebSocketSaveOrchestrator`, `McpClientSaveOrchestrator`).

### System Health Metrics

- **Drop Accounting & Stream Health**:
  - Stream export tracks and records dropped messages:
    - `capacity_dropped`: messages dropped due to maximum retained entry buffer saturation.
    - `memory_budget_dropped`: messages dropped due to byte memory budget threshold.
  - Included in both exported transcript metadata headers and operational info logs.

## Monitoring Integration

- [x] **CI/CD Quality Gate**: `make typecheck` runs `scripts/check_mypy_baseline.py` on pull requests and CI pipelines. Non-zero exit code fails build if any untracked error is introduced or resolved error remains uncommitted.
- [x] **Live Regression Guard**: `tests/test_mypy_baseline_live.py` executes under `make test` as a continuous regression guard.
- [x] **Log Aggregation**: Python stdlib `logging` messages route through standard application log handlers with syslog level parity.
- [ ] **Prometheus / Grafana**: N/A for desktop client UI components (telemetry routes through internal `MetricsTrackerProtocol` where configured).

## Validation Results

- [x] Logs are correctly formatted: Verified key-value format and valid level assignments.
- [x] Metrics are collected correctly: `track_gui_save_action` verified in save integration flows.
- [x] Logging works in error scenarios: Missing collection warnings and cancellation info logs tested.
- [x] Large data structures are not logged: Only IDs, error codes, counts, and paths logged.
- [x] Metrics are available for monitoring: CI gate outputs structured error diffs with exit code 1/0.

Validation commands executed:
```bash
make lint
make typecheck
make test PYTEST_ARGS="tests/test_mypy_baseline_live.py tests/test_save_flow_integration.py tests/test_websocket_save_flow_integration.py"
```
All targets exited code 0 with zero lint or typecheck errors.

## Notes

- The baseline error count is preserved at 189 known errors with 0 regressions.
- Symmetrical cancellation logging is now present across all save orchestrators for both `save_as` and `save_new` dialog dismissal.
