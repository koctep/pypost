# PYPOST-514: Observability Implementation

## Logging Implementation

### Added Logs

- **ERR**: `pypost/core/http_client.py` — `yaml_to_json_conversion_failed` when send-time YAML→JSON
  conversion fails before the HTTP request is sent. Logs `method`, rendered `url`, and converter
  `detail` (error message only; no body content).

No logging for checkbox toggle or successful conversion — checkbox is low-value UI state (per
architecture decision #7, consistent with PYPOST-513 format selector). Successful sends follow
existing `request_complete` DEBUG logging.

Existing error surfacing unchanged:
- **ERR**: `pypost/ui/presenters/tabs_presenter.py` — `request_error` with `category=body`,
  `message`, and `detail` when the user sees the BODY error dialog.

### Log Structure

Log format used:
- Structured logs: yes (key=value fields)
- Includes context: yes (method, url, detail on failure)
- Log levels: ERR (new); existing ERR/DEBUG on send path unchanged

## Metrics Implementation (if applicable)

No new metrics. Architecture decision #7: checkbox toggle is a low-value UI control (same as
PYPOST-513 format selector). Existing send metrics (`track_request_sent`, `track_response_received`)
are unchanged. BODY errors are non-retryable — no `track_retry_attempt` for this category.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — N/A (no new metrics)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted
- [x] Metrics are collected correctly (unchanged behavior)
- [x] Logging works in error scenarios (`test_http_client.py` BODY error path)
- [x] Large data structures are not logged (only converter detail string, never body text)
- [x] Metrics are available for monitoring (existing send counters)

## Notes

- Converter module (`yaml_json_converter.py`) stays log-free — pure function; failures are logged
  at the HTTP client boundary where `ExecutionError(BODY)` is raised.
- If conversion analytics become useful later, a counter (no body content) could be added via
  `MetricsManager`; not warranted for this task.
