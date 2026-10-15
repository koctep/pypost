# PYPOST-1370: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging added across background folding worker, controller, and format scanners:
- **EMERG**: N/A - no unrecoverable system crashes or kernel faults in editor folding subsystem.
- **ALERT**: N/A - no immediate operator interventions required for local UI document parsing.
- **CRIT**: N/A - no critical daemon failures in UI folding logic.
- **ERR**:
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_error generation=%d format=%s duration=%.4fs error=%s` - unexpected AST parsing failure during worker execution.
- **WARNING**:
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_failed generation=%d error=%s` - worker failure delivered to controller; resets regions cleanly.
- **NOTICE**: N/A
- **INFO**: N/A - high-frequency document parsing operations use DEBUG to prevent log pollution.
- **DEBUG**:
  - `pypost/ui/widgets/fold/fold_controller.py`: `synchronous_fold_scan_dispatched size_bytes=%d format=%s` - synchronous fast-path AST scan for documents below 500 KB threshold.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_dispatched generation=%d size_bytes=%d format=%s` - background `FoldScanWorker` spawned for documents >= 500 KB threshold.
  - `pypost/ui/widgets/fold/fold_controller.py`: `superseding_active_fold_worker next_generation=%d` - cooperative cancellation requested for obsolete in-flight worker on new edit.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_stale_discarded generation=%d current_generation=%d` - results from superseded generation safely ignored.
  - `pypost/ui/widgets/fold/fold_controller.py`: `background_fold_scan_stale_error_discarded generation=%d current_generation=%d` - error from superseded generation safely ignored.
  - `pypost/ui/widgets/fold/fold_controller.py`: `cleaning_up_fold_worker` - cancellation and wait for background worker when editor is destroyed.
  - `pypost/ui/widgets/fold/fold_controller.py`: `fold_scan_completed format=%s regions=%d collapsed=%d` - fold regions successfully mapped and applied to editor viewport.
  - `pypost/ui/widgets/fold/fold_controller.py`: `fold_region_toggled region_id=%s collapsed=%s` - individual fold region toggle state change.
  - `pypost/ui/widgets/fold/fold_controller.py`: `fold_all_expanded previously_collapsed=%d` - all regions expanded.
  - `pypost/ui/widgets/fold/fold_controller.py`: `fold_all_collapsed total_regions=%d` - all regions collapsed.
  - `pypost/ui/widgets/fold/fold_controller.py`: `fold_block_revealed block=%d revealed_regions=%s` - fold region expanded to reveal cursor block.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_interruption_requested generation=%d format=%s` - cooperative interruption triggered on worker thread.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_cancelled generation=%d format=%s duration=%.4fs` - worker cancelled before or during parsing; logs duration.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_completed generation=%d format=%s regions=%d duration=%.4fs` - worker completed AST scan; logs region count and duration.
  - `pypost/ui/widgets/fold/fold_worker.py`: `fold_scan_worker_failed generation=%d format=%s duration=%.4fs error=%s` - worker caught parsing exception; logs duration and error message without payload.
  - `pypost/ui/widgets/fold/json_structure_scanner.py`: `json_scan_parse_skipped line=%d col=%d msg=%s` - syntax error during JSON parse, skipped fold region generation.
  - `pypost/ui/widgets/fold/yaml_structure_scanner.py`: `yaml_scan_parse_skipped error=%s` - syntax error during YAML parse, skipped fold region generation.
  - `pypost/ui/widgets/fold/xml_structure_scanner.py`: `xml_scan_parse_skipped error=%s` - syntax error during XML parse, skipped fold region generation.

### Log Structure

Log format used:
- Structured logs: yes
- Includes context: yes (generation counter, byte size, format, duration, region counts, error strings)
- Log levels: DEBUG, WARNING, ERROR

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Worker AST scan duration measured via `time.monotonic()` and logged with millisecond precision in `duration=%.4fs`.
- **Throughput**: Document size tracking in bytes (`size_bytes=%d`) on dispatch.
- **Error rate**: Parse error occurrences logged via `fold_scan_worker_failed` and `background_fold_scan_failed`.

### Business Metrics

Business metrics:
- `regions`: Count of detected fold regions per document format.
- `collapsed`: Count of currently active collapsed regions preserved across document revisions.

### System Health Metrics

System health metrics:
- **Resource usage**: Heavy AST parsing offloaded from main UI thread to `FoldScanWorker` background QThread when size >= 500 KB, preserving UI fluidity and 60 FPS responsiveness.
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
- [x] Metrics are collected correctly (duration, byte size, region count)
- [x] Logging works in error scenarios (synthetic exception test in `tests/test_background_fold_scanner.py`)
- [x] Large data structures are not logged (verified by assertion ensuring no payload text leaks into logs)
- [x] Metrics are available for monitoring

## Notes

- All fold scanner and controller logging strictly guarantees that raw document content and AST nodes are never dumped to log files. Only document metadata, sizes, elapsed durations, and error descriptions are logged.
