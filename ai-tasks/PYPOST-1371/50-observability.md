# PYPOST-1371: Observability Implementation

## Logging Implementation

### Added Logs

Structured warning and diagnostics logging implemented across folding scanners, controller, and background worker for stress and edge-case payload scenarios:
- **EMERG**: N/A - no unrecoverable system crashes or kernel faults in editor folding subsystem.
- **ALERT**: N/A - no immediate operator interventions required for local UI document parsing.
- **CRIT**: N/A - no critical daemon failures in UI folding logic.
- **ERR**:
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_error generation=%d format=%s duration=%.4fs error=%s` - unexpected AST parsing failure during worker execution.
- **WARNING**:
  - `pypost/ui/widgets/fold/json_structure_scanner.py`: `json_scan_parse_skipped error_type=%s length=%d` - syntax error, recursion limit, or value error during JSON parse; logs error type and text length without leaking payload data.
  - `pypost/ui/widgets/fold/yaml_structure_scanner.py`: `yaml_scan_parse_skipped error_type=%s length=%d` - YAML parsing failure or recursion limit; logs error type and text length without leaking payload data.
  - `pypost/ui/widgets/fold/xml_structure_scanner.py`: `xml_scan_parse_skipped error_type=%s length=%d` - XML parsing failure or recursion limit; logs error type and text length without leaking payload data.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_failed generation=%d error=%s` - worker failure delivered to controller; safely resets regions to empty.
- **NOTICE**: N/A
- **INFO**: N/A - high-frequency document parsing operations use DEBUG to prevent log pollution.
- **DEBUG**:
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_interruption_requested generation=%d format=%s` - cooperative interruption triggered on worker thread.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_cancelled generation=%d format=%s duration=%.4fs` - worker cancelled before or during parsing; logs duration.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_completed generation=%d format=%s regions=%d duration=%.4fs` - worker completed AST scan; logs region count and duration.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_failed generation=%d format=%s duration=%.4fs error=%s` - worker caught parsing exception; logs duration and error message without payload.
  - `pypost/ui/widgets/fold/fold_controller.py`: `synchronous_fold_scan_dispatched size_bytes=%d format=%s` - synchronous fast-path AST scan for documents below 500 KB threshold.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_dispatched generation=%d size_bytes=%d format=%s` - background `FoldScanWorker` spawned for oversized documents (>= 500 KB and > 10 MB).
  - `pypost/ui/widgets/fold/fold_controller.py`: `superseding_active_fold_worker next_generation=%d` - cooperative cancellation requested for obsolete in-flight worker on new edit.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_stale_discarded generation=%d current_generation=%d` - results from superseded generation safely ignored.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_stale_error_discarded generation=%d current_generation=%d` - error from superseded generation safely ignored.
  - `pypost/ui/widgets/fold/fold_controller.py`: `cleaning_up_fold_worker` - cancellation and wait for background worker when editor is destroyed.
  - `pypost/ui/widgets/fold/format_detector.py`: `detect_body_format detected=%s source=heuristic length=%d` - format detection telemetry.

### Log Structure

Log format used:
- Structured logs: yes
- Includes context: yes (generation counter, byte size, format, duration, region counts, error_type, length)
- Log levels: DEBUG, WARNING, ERROR

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Worker AST scan duration measured via `time.monotonic()` and logged with millisecond precision in `duration=%.4fs`.
- **Throughput**: Document size tracking in bytes (`size_bytes=%d`, `length=%d`) on dispatch and format scan skips.
- **Error rate**: Parse error occurrences logged via `fold_scan_worker_failed` and `*_scan_parse_skipped`.

### Business Metrics

Business metrics:
- `regions`: Count of detected fold regions per document format.
- `collapsed`: Count of currently active collapsed regions preserved across document revisions.

### System Health Metrics

System health metrics:
- **Resource usage**: Heavy AST parsing offloaded from main UI thread to `FoldScanWorker` background QThread for oversized payloads (> 10 MB), keeping main UI thread responsive without blocking or lag.
- **Component status**: Worker lifecycle tracked via `_LIVE_WORKERS` registry, cooperative interruption flags, and editor destruction cleanup hooks.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted
- [x] Metrics are collected correctly
- [x] Logging works in error scenarios
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring

## Notes

- All fold scanners (`JsonStructureScanner`, `YamlStructureScanner`, `XmlStructureScanner`) strictly guarantee that raw document content and syntax snippets are never dumped into log files.
- Truncated and malformed payloads log structured warnings with `error_type` and `length` only, preventing sensitive credential/payload data leaks.
- Verified comprehensively in `tests/test_folding_stress_and_edge_cases.py` (`TestObservabilityAndStructuredLogging`).
