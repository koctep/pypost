# PYPOST-1278: Observability Implementation

## Logging Implementation

### Added Logs

- **ERR**: `pypost.ui.presenters.library_presenter` records failed worker operations with
  the library stable ID, operation name, and exception type.
- **WARNING**: rejected duplicate operation admissions are recorded with the library stable
  ID and operation name.
- **INFO**: admitted operations record start, completion, or an explicit safety block.

### Log Structure

- Structured logs: yes; messages use stable event names and key-value fields.
- Includes context: yes; library stable ID, operation, outcome, and error type where useful.
- Log levels: INFO, WARNING, and ERROR.
- Privacy: no Git URLs, credentials, auth configuration, file contents, or local paths are
  logged. Stable IDs are bounded application identifiers and are used only as operation
  context.

## Metrics Implementation

### Performance Metrics

- No duration metric was added because the current worker boundary does not expose a
  monotonic operation timer and introducing one would duplicate the existing lifecycle
  instrumentation. Operation outcome counts provide the useful current health signal.

### Business Metrics

- `gui_library_operations_total{operation,outcome}` counts Library Manager operations by a
  fixed operation vocabulary and outcome (`started`, `success`, `failure`, `blocked`, or
  `rejected`). It is implemented by the existing Prometheus `MetricsRegistry` and the
  OpenTelemetry tracker.

### System Health Metrics

- No new resource-usage gauge was added. Library operations already expose status and
  failure logs, while resource metrics are outside this task's UI-management boundary.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics
- [x] OpenTelemetry metrics parity
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

- [x] Logs are correctly formatted — focused tests assert stable event names and context.
- [x] Metrics are collected correctly — focused tests assert Prometheus counters and bounded
  unknown-label normalization.
- [x] Logging avoids large data structures and sensitive Git/auth values.
- [x] Metric labels are normalized to bounded vocabularies.

Make validation:

- `make lint` — passed flake8, Markdown lint, and relative-link checks.
- `make typecheck` — passed the repository baseline gate; 180 known baseline errors remain.
- `make test PYTEST_ARGS='tests/test_ui_library_manager_pypost_1278_repro.py
  tests/test_ui_library_manager.py tests/test_ui_library_manager_repro.py -q'` — 3 files
  passed, 0 failed, 0 skipped.
- The observability regression test also verifies that a local directory path is never
  emitted as an operation identifier and that sensitive metric labels normalize to `unknown`.

## Notes

The no-op metrics implementation remains the default for isolated presenters and tests.
The application composition root passes the configured metrics manager into the Library
Manager dialog, so production Prometheus/OpenTelemetry collection is used when enabled.
