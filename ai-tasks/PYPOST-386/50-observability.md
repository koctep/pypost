# PYPOST-386: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:
- **DEBUG**: `state_manager.py` — `state_manager_save_scheduled` when a debounced save is
  scheduled (includes `debounce_ms`).
- **DEBUG**: `state_manager.py` — `state_manager_save_debounced` when the timer fires and
  settings are written.
- **DEBUG**: `state_manager.py` — `state_manager_save_immediate` when `save()` or
  `flush_pending_save()` writes synchronously.

Existing logs unchanged:
- **INFO**: `main_window.py` — `main_window_exit_requested` on quit (flush happens before this
  path completes storage wait).

### Log Structure

Log format used:
- Structured logs: yes (key=value pairs in message)
- Includes context: yes (debounce interval on schedule)
- Log levels: DEBUG for save scheduling/persistence; INFO for exit flow

## Metrics Implementation (if applicable)

Not applicable — no new metrics. Existing settings revision counter in `ConfigManager` still
reflects each persisted write.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted
- [x] Metrics are collected correctly (N/A — unchanged)
- [x] Logging works in error scenarios (save errors still handled by `ConfigManager`)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (unchanged)

## Notes

Debouncing reduces log volume from rapid expand/collapse compared to immediate per-toggle saves.
Enable DEBUG on `pypost.core.state_manager` to trace save scheduling during development.
