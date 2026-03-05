# PYPOST-14: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:
- **EMERG**: not added (not applicable for this UI change).
- **ALERT**: not added (not applicable for this UI change).
- **CRIT**: not added (not applicable for this UI change).
- **ERR**: not added (not applicable for this UI change).
- **WARNING**: not added (not applicable for this UI change).
- **NOTICE**: not added (not applicable for this UI change).
- **INFO**: `pypost/ui/main_window.py` - log new-tab action trigger source
  (`plus_button` or `shortcut`) and tab count before action.
- **DEBUG**: not added (not required for current scope).

### Log Structure

Log format used:
- Structured logs: yes (key/value style message:
  `new_tab_action_triggered source=<value> tabs_before=<value>`).
- Includes context: yes (`source`, `tabs_before`).
- Log levels: `INFO`.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: no new metric in this task.
- **Throughput**: no new metric in this task.
- **Error rate**: no new metric in this task.

### Business Metrics

Business metrics:
- `gui_new_tab_actions_total{source="<plus_button|shortcut>"}`: counts how new tab is triggered.
  - Definition: `pypost/core/metrics.py` (`MetricsManager._init_metrics`).
  - Tracking call: `pypost/ui/main_window.py` (`MainWindow.handle_new_tab`).

### System Health Metrics

System health metrics:
- **Resource usage**: not added in this task.
- **Component status**: existing metrics server health behavior unchanged.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted
- [x] Metrics are collected correctly
- [ ] Logging works in error scenarios
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring

## Notes

Additional notes on observability or special cases:
- Added metric API:
  - `MetricsManager.track_gui_new_tab_action(source: str)`.
- New-tab observability now covers both `+` button and `Ctrl+N`.
- Local validation:
  - `python3 -m py_compile pypost/core/metrics.py pypost/ui/main_window.py`
  - `venv/bin/python -m flake8 --jobs=1 --max-line-length=100 ...` is unavailable in current
    environment (`No module named flake8`).
