# PYPOST-1290: Observability Implementation

## Logging Implementation

### Added Logs

- **WARNING**: `pypost/ui/hotkeys.py` (`_on_shortcut_ambiguous`) — Emits `hotkey_ambiguous key=<key>` when Qt's `QShortcut.activatedAmbiguously` signal fires, alerting operators and developers that a shortcut key sequence has multiple conflicting active listeners in the current window context.

### Log Structure

Log format used:
- Structured logs: yes (`hotkey_ambiguous key=%s` format matching PyPost's logging conventions such as `hotkey_routed key=...`).
- Includes context: yes (key sequence identification).
- Log levels: WARNING.

## Metrics Implementation (if applicable)

### Performance Metrics

Not applicable: this task introduces collision detection and ambiguous activation warnings; no new request/timer metrics are involved.

### Business Metrics

Not applicable: UI hotkey routing does not emit business throughput metrics.

### System Health Metrics

Not applicable.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (not applicable)
- [ ] Grafana dashboards (not applicable)
- [ ] Alerting rules (not applicable)
- [x] Log aggregation (ELK, Loki, standard file loggers capture WARNING level events)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (verified in `TestHotkeyAmbiguousLogging`).
- [x] Metrics are collected correctly (N/A).
- [x] Logging works in error scenarios (tested by emitting `activatedAmbiguously`).
- [x] Large data structures are not logged (only the concise key sequence string is emitted).
- [x] Metrics are available for monitoring (N/A).

## Notes

- This structured warning resolves the complete absence of diagnostic feedback when Qt suppresses conflicting shortcuts.
- Combined with the automated build-time invariant check (`collect_live_shortcuts`), hotkey collisions are now protected both statically and at runtime.
