# PYPOST-1497: Observability Implementation

## Logging Implementation

### Scope and Gap Analysis

Cooperative cancellation and lifecycle teardown span:
- `pypost/ui/presenters/library_presenter.py` (`cancel_operation`, `cancel_all_operations`, `_worker_cancelled`, `_operation_cancelled`, `teardown`, `close`)
- `pypost/ui/dialogs/library_dialogs.py` (`LibraryManagerDialog.closeEvent`, `LibraryManagerDialog.reject`)
- `pypost/core/qt/library_operation_worker.py` (`cancel`, `run`)

Prior to this task, cancelling an operation left admission stuck and produced no presenter-level lifecycle telemetry. Dialog close abandoned background workers with zero logging. This implementation introduces structured operational logs covering every phase of cooperative cancellation, bulk teardown, and metric recording.

### Added Logs

- **INFO**: `pypost/ui/presenters/library_presenter.py` (`cancel_operation` / `cancel_all_operations`) —
  `library_presenter_operation_cancelling library_id=%s operation=%s`
  Logged when cooperative cancellation is requested for an active background worker.
- **INFO**: `pypost/ui/presenters/library_presenter.py` (`_operation_cancelled`) —
  `library_presenter_operation_cancelled library_id=%s operation=%s`
  Logged upon receipt of worker `operation_cancelled` signal, confirming clean cooperative abortion and admission lock release.
- **INFO**: `pypost/ui/presenters/library_presenter.py` (`teardown`) —
  `library_presenter_teardown_started timeout_ms=%d active_ops=%d`
  Logged at the beginning of presenter teardown with timeout configuration and in-flight operation count.
- **INFO**: `pypost/ui/presenters/library_presenter.py` (`teardown`) —
  `library_presenter_teardown_completed`
  Logged after all workers have been joined or timed out, and admission/tracking collections are purged.
- **DEBUG**: `pypost/core/qt/library_operation_worker.py` (`cancel`) —
  `library_operation_worker_cancelled`
  Worker-local CTS token cancellation event.
- **Suppression of Failure Logs**:
  When operations are cancelled or the presenter is in `_torn_down` state, `_worker_failed` suppresses view-facing signals and avoids logging `library_operation_failed` at `ERROR` level, preventing spurious error reports and false alert noise during normal window dismissal.
- **EMERG / ALERT / CRIT / ERR / NOTICE**:
  None added. Cooperative cancellation and panel teardown are standard lifecycle paths handled without raising unhandled errors.

### Context Sanitization and Privacy

- `library_id` is passed through `self._safe_operation_id(library_id)`. If the identifier resembles a remote URL or file path, a SHA-256 opaque hash (`opaque-<digest>`) is emitted instead of raw text.
- No repository credentials, tokens, payloads, file contents, or commit objects are included in log statements.

### Log Structure

- Structured logs: yes (`event key=value` format with `%`-style lazy interpolation)
- Includes context: yes (`library_id`, `operation`, `timeout_ms`, `active_ops`)
- Log levels: INFO, DEBUG
- High-volume data structures: strictly excluded

---

## Metrics Implementation

### Business and Operational Metrics

- **Metric**: `gui_library_operations_total` (Prometheus Counter)
  - **Labels**: `operation=<op>`, `outcome="cancelled"`
  - **Location**: `LibraryPresenter._operation_cancelled` via `self._metrics.track_gui_library_operation(operation, "cancelled")`.
  - **Purpose**: Distinguishes cooperative user/teardown cancellation from normal completion (`success`), domain failures (`failure`), and admission guards (`rejected`, `blocked`). Outcome `"cancelled"` is an allowlisted outcome in `pypost/core/metrics_registry.py`.

### Performance Metrics

- **Teardown bounded wait**:
  `timeout_ms` parameter logged on `library_presenter_teardown_started` indicates the allocated joining budget. Idle presenters exit immediately (< 100ms) without burning timeout budget.

### System Health Metrics

- **Component status**:
  `is_torn_down` property reflects lifecycle disposal state; active operations count logged on teardown.

---

## Monitoring Integration

- [x] Prometheus metrics: `gui_library_operations_total{outcome="cancelled"}` recorded on cooperative worker cancellation.
- [ ] Grafana dashboards: existing GUI operations panels can filter by `outcome="cancelled"`.
- [ ] Alerting rules: none added (cancellation is expected user-driven behavior).
- [ ] Log aggregation: greppable `library_presenter_*` event tokens for log ingestion systems.

---

## Automated Test Contracts (`do-testing` Compliance)

In accordance with `do-testing` rules C1 and C5, caplog contracts are verified in `tests/test_library_presenter_cancel_repro.py`:

1. **`test_presenter_cancel_operation_logging_and_metrics_contract`**:
   - Asserts `caplog.at_level(logging.INFO, logger="pypost.ui.presenters.library_presenter")`.
   - Verifies `library_presenter_operation_cancelling` emitted with `library_id` and `operation`.
   - Verifies `library_presenter_operation_cancelled` emitted with `library_id` and `operation`.
   - Verifies suppression of `ERROR` logs (`len(error_records) == 0`).
   - Verifies `_metrics.track_gui_library_operation("pull", "cancelled")` is called.

2. **`test_presenter_teardown_logging_and_suppression_contract`**:
   - Asserts `caplog.at_level(logging.INFO, logger="pypost.ui.presenters.library_presenter")`.
   - Verifies `library_presenter_teardown_started` emitted with `timeout_ms=1000` and `active_ops=1`.
   - Verifies `library_presenter_teardown_completed` emitted upon teardown completion.
   - Verifies suppression of late worker failures after teardown (no `ERROR` logs).

---

## Validation Results

- [x] Logs are correctly formatted (`library_presenter_*` prefix, structured `key=value`).
- [x] Metrics are collected correctly (`track_gui_library_operation(operation, "cancelled")`).
- [x] Logging works in error scenarios (spurious `ERROR` logs suppressed on cancel/teardown).
- [x] Large data structures are not logged (sanitized `library_id` and `operation` only).
- [x] Metrics are available for monitoring via `MetricsRegistry`.
- [x] Automated test contracts pass cleanly under `make test`.
