# PYPOST-792: Observability Implementation

## Logging Implementation

### Added Logs

- **WARNING**: `pypost/core/style_manager.py` — `styles_directory_missing` when the QSS
  directory is absent (previously returned `""` silently).
- **WARNING**: `pypost/core/style_manager.py` — `style_file_read_failed` when an individual
  `.qss` file cannot be read (replaces `print()` that bypassed log capture per PYPOST-688
  O-003).
- **WARNING**: `pypost/core/style_manager.py` — `styles_directory_scan_failed` when the
  styles directory glob fails (replaces `print()`).
- **DEBUG**: `pypost/core/style_manager.py` — `styles_loaded` with `file_count` and `bytes`
  after QSS assembly (no stylesheet content logged).
- **DEBUG**: `pypost/core/style_manager.py` — `theme_applied` with resolved `theme`,
  resulting `style` (`PyPostStyle` vs `Fusion`), and `requested` value (captures invalid
  theme fallback).

### No new logs in `PyPostStyle` (`custom_style.py`)

Rationale:

- `pixelMetric` is invoked by Qt for every layout pass; logging there would flood logs and
  add measurable overhead with no diagnostic value now that `close_button_size` defaults to
  `None` and production never calls `set_close_button_size`.
- The tab-layout defect is a deterministic stylesheet/metric configuration issue, not a
  runtime failure mode. Regression tests (`tests/test_tab_layout_regression.py`) and the QSS
  guard are the correct observability for recurrence prevention.
- `MainWindow.apply_settings` already logs `apply_settings_start` with `font_size`; theme
  resolution is now covered by `StyleManager.apply_theme` DEBUG events.

### Log Structure

Log format used:
- Structured logs: yes (key=value event names and scalar fields)
- Includes context: yes (paths, theme names, file counts — no QSS body)
- Log levels: DEBUG, WARNING

## Metrics Implementation (if applicable)

### Performance Metrics

None. Stylesheet loading is synchronous, runs once per settings change, and is not a throughput
or latency bottleneck worth instrumenting.

### Business Metrics

None. This is a visual layout correction with no user-action counters.

### System Health Metrics

None. No new health probes; existing `MetricsManager` stack is unchanged.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

Not applicable for this task. New WARNING logs surface through the existing
`logging.basicConfig(level=INFO)` pipeline and CI `pytest.log` capture at WARNING+.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (key=value convention matches project modules)
- [x] Metrics are collected correctly (N/A — no metrics added)
- [x] Logging works in error scenarios (`print()` bypass removed; warnings use `logger`)
- [x] Large data structures are not logged (only file count and byte length)
- [x] Metrics are available for monitoring (unchanged baseline)

## Notes

- The only production code change in this step is `pypost/core/style_manager.py`. No changes
  to `custom_style.py`, `main.qss`, or regression tests.
- Pre-existing `print()` calls in `pypost/core/config_manager.py` remain out of scope
  (tracked separately in PYPOST-688 tech debt).
- To see `theme_applied` / `styles_loaded` in local runs, set log level to DEBUG for
  `pypost.core.style_manager`.
