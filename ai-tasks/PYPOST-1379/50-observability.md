# PYPOST-1379: Observability Implementation

## Logging Implementation

### Added Logs

The following structured log events are implemented and maintained across GUI components for interactive click-to-reveal response masking:

- **EMERG**: None (not applicable for GUI presentation components).
- **ALERT**: None (not applicable for GUI presentation components).
- **CRIT**: None (critical runtime errors handled by standard top-level application error boundaries).
- **ERR**: None (unparseable JSON bodies or unexpected AST failures gracefully fall back to raw text display without throwing unhandled exceptions).
- **WARNING**: None (non-JSON payloads or responses without matching selectors are expected operational paths, not warnings).
- **NOTICE**: None (syslog NOTICE mapped to standard Python logging INFO).
- **INFO**:
  - `pypost/ui/widgets/response_view.py`: `display_response_skip_pretty_print body_chars=<chars> threshold=<threshold>` - logged when response body exceeds `LARGE_DOC_CHAR_THRESHOLD` (100 KB), bypassing AST formatting.
  - `pypost/ui/widgets/response_view.py`: `response_view_displayed status=<status> size=<size> format=<format>` - logged upon displaying response metadata.
- **DEBUG**:
  - `pypost/ui/widgets/response_view.py`: `response_masking_initialized span_count=<count> selectors_count=<count>` - logged when response masking is initialized in GUI `ResponseView`. Emits integer span count and configured selector count, strictly excluding sensitive values.
  - `pypost/ui/widgets/response_view.py`: `response_masking_large_doc_fallback payload_size=<bytes> threshold=<bytes>` - logged when a response with hidden fields exceeds the 100 KB threshold and bypasses token span masking. Only integer sizes are logged.
  - `pypost/ui/widgets/response_view.py`: `response_masking_failed` - logged when JSON parsing or masking throws an unexpected exception during formatting. Raw payload content is not logged.
  - `pypost/ui/widgets/response_mask_controller.py`: `response_masking_spans_updated span_count=<count>` - logged when token span coordinates are loaded and updated in `ResponseMaskController`.
  - `pypost/ui/widgets/response_mask_controller.py`: `click_to_reveal_toggle path=<path> revealed=<boolean>` - logged when a user clicks on a masked token span to reveal or re-mask a field. Logs only the field selector path (e.g. `auth.token`, `api_key`) and the boolean toggle state (`revealed=True/False`), strictly omitting raw secret values and masked replacement tokens.

### Log Structure

Log format used:
- Structured logs: **Yes** (`snake_case_event key=value ...` formatting following project standard).
- Includes context: **Yes** (includes `span_count`, `selectors_count`, `path`, `revealed`, `payload_size`, `threshold`).
- Log levels: `DEBUG`, `INFO`.
- **Zero Secret Leakage Invariant**:
  - Sensitive payload values, unmasked secrets, authorization headers, passwords, and user PII are strictly excluded from all log records across all log levels.
  - Toggle events log only the selector path and boolean reveal state.
  - Large-document fallback logs only integer character and threshold counts.
  - Verified by automated unit tests `test_masking_observability_logging_and_metrics` and `test_masking_observability_large_doc_fallback_logs`.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Execution elapsed time recorded via `ResponseData.elapsed_time` and displayed in GUI header.
- **Throughput**: UI interaction events processed asynchronously in Qt main thread without event loop blocking.
- **Error rate**: Zero UI thread crashes; syntax errors during parsing caught gracefully with fallback to raw body.

### Business Metrics

- **Hidden Value Masking Applied Counter**:
  - `hidden_value_masks_applied_total`: Prometheus / OpenTelemetry counter tracking secret masking operations across PyPost surfaces.
    - **Metric Name**: `hidden_value_masks_applied_total`
    - **Surface Label**: `surface="gui_response"` (alongside existing surfaces `"history"`, `"mcp"`, and `"websocket"`).
    - **Trigger**: Incremented in `ResponseView.display_response` whenever an incoming response has `hidden_fields` configured and one or more masked token spans are identified.
    - **Low Cardinality**: Carries strictly static low-cardinality metadata (`surface="gui_response"`). No secret values, request URLs, or field paths are embedded in metric labels.

### System Health Metrics

System health metrics:
- **Resource usage**: Large document threshold (100 KB) safeguards Qt document memory and CPU layout overhead by bypassing token span indexing on oversized payloads.
- **Component status**: `ResponseMaskController` lifecycle bound to `FoldableCodeView` and `ResponseView` parents; cleared upon tab teardown or new response display.

## UI Interaction Telemetry & Security Audit Boundaries

1. **Telemetry & Interaction Bounds**:
   - UI mask events recorded via `track_hidden_value_mask_applied(surface="gui_response")`.
   - Reveal toggles logged at `DEBUG` with bounded field path and state, adhering to low cardinality.
   - Raw tokens are never sent to external telemetry collectors.

2. **In-Memory and Model Immutability**:
   - The underlying `ResponseData.body` string/bytes in memory remains 100% authentic and unmutated throughout GUI reveal and re-mask toggling.
   - Click-to-reveal modifications occur purely within the presentation buffer (`QTextDocument`).
   - Audit logs, local history records, and exported curl commands retain accurate response data.

3. **Fail-Closed Fallback Handling**:
   - If response text is non-JSON or malformed, the system falls back to displaying raw text without crashing.
   - Oversized documents (>100 KB) skip AST tokenization to prevent UI thread freezing.
   - Text heuristics (`sanitize_text`) continue to protect sensitive values in non-JSON formats.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`hidden_value_masks_applied_total{surface="gui_response"}`)
- [x] OpenTelemetry metrics (`hidden_value_masks_applied_total` in `MetricsOTel`)
- [ ] Grafana dashboards (Configured centrally via standard PyPost Prometheus dashboards)
- [ ] Alerting rules (Alert on abnormal spike in response parsing errors)
- [x] Log aggregation (ELK, Loki, syslog-compatible structured log format)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`snake_case_event key=value ...`)
- [x] Metrics are collected correctly (`self._metrics.track_hidden_value_mask_applied("gui_response")` asserted in unit tests)
- [x] Logging works in error and edge-case scenarios (large-document fallback, invalid JSON)
- [x] Large data structures and sensitive payload values are not logged (only integer counts and selector paths emitted)
- [x] Metrics are available for monitoring via `MetricsRegistry` and `MetricsOTel`

## Notes

- All changes maintain 100% backward compatibility with existing `ResponseView` consumers and metrics protocols.
- Logging levels adhere strictly to syslog/Python conventions (`DEBUG` for interactive click toggles and span counts, `INFO` for large-document bypasses and display lifecycle).
- STEP 6 status remains `[/]` in `ai-tasks/PYPOST-1379/00-roadmap.md` awaiting acceptance review by the orchestrator.
