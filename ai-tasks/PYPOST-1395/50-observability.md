# PYPOST-1395: Observability Implementation

## Logging Implementation

### Added Logs

The expansion of `hidden_response_fields` to bundled reference collections (`examples/collections/github_mcp.json`, `examples/collections/gitlab_mcp.json`, `examples/collections/jira_mcp.json`) leverages PyPost's dual-surface response field masking architecture. The observability and logging events across collection deserialization, MCP agent tool execution, and desktop GUI response rendering operate as follows:

- **EMERG**: None (not applicable for response field masking and collection parsing operations).
- **ALERT**: None (not applicable for response field masking and collection parsing operations).
- **CRIT**: None (critical runtime errors handled by standard top-level application error boundaries).
- **ERR**: None (unparseable bodies, invalid JSON payloads, or non-matching selector paths safely fall back to unmasked raw text display or standard pass-through without generating error-level exceptions).
- **WARNING**:
  - `pypost/core/collection_serializer.py`: `collection_file_read_failed path=<path> reason=<exc>` - logged if a collection file cannot be accessed or read from disk.
  - `pypost/core/collection_serializer.py`: `collection_json_parse_failed reason=<exc>` - logged if collection file JSON syntax is corrupt.
  - `pypost/core/collection_serializer.py`: `collection_deserialization_failed reason=<exc>` - logged if collection schema fails Pydantic validation.
- **NOTICE**: None (syslog NOTICE level mapped to standard Python logging INFO).
- **INFO**:
  - `pypost/core/collection_serializer.py`: `collection_file_read path=<path> format=<format> requests=<count> variables=<count> presets=<count>` - logged upon successfully loading and deserializing reference collections from disk. Emits file path, format, and child entity counts without dumping payload contents or collection secrets.
  - `pypost/ui/widgets/response_view.py`: `display_response_skip_pretty_print body_chars=<chars> threshold=<threshold>` - logged when a response body exceeds `LARGE_DOC_CHAR_THRESHOLD` (500,000 characters), safely bypassing AST formatting.
  - `pypost/ui/widgets/response_view.py`: `response_view_displayed status=<status> size=<size> format=<format>` - logged upon displaying response metadata in desktop GUI.
  - `pypost/core/mcp_server_impl.py`: `mcp_param_default_applied method=<method> param=<param> default_applied=true default_type=<type>` - logged when default tool parameters are applied during tool argument resolution.
- **DEBUG**:
  - `pypost/core/mcp_server_impl.py`: `mcp_response_masking_applied method=<method> tool=<tool> selector_count=<count>` - logged when an MCP tool invocation processes a request configured with `hidden_response_fields`. Emits tool method, tool name, and integer count of configured selectors, strictly excluding sensitive response values.
  - `pypost/core/sensitive_text_sanitizer.py`: `redact_json_response_fields_completed selectors_count=<count> masked_fields_count=<count>` - logged upon successful JSON traversal and redaction. Records the count of active selectors and total number of field occurrences masked with `***`, omitting sensitive key names and payload values.
  - `pypost/core/sensitive_text_sanitizer.py`: `redact_json_response_fields_skipped_non_json reason=<exception_type>` - logged when response body is non-JSON or malformed (e.g. `JSONDecodeError`). Emits only the exception class name without echoing the malformed body text, preventing secret leakage from malformed responses.
  - `pypost/core/sensitive_text_sanitizer.py`: `redact_json_response_fields_skipped_non_container type=<type_name>` - logged when parsed JSON is a primitive rather than a dictionary or list container.
  - `pypost/core/mcp_server_impl.py`: `mcp_execution_variables_merged env_var_count=<n> hidden_key_count=<n> mcp_arg_count=<n> defaults_applied_count=<n>` - logged prior to tool execution with integer diagnostic counts only.
  - `pypost/ui/widgets/response_view.py`: `response_masking_initialized span_count=<count> selectors_count=<count>` - logged when response masking is initialized in GUI `ResponseView`. Emits integer span count and configured selector count, strictly excluding sensitive values.
  - `pypost/ui/widgets/response_view.py`: `response_masking_large_doc_fallback payload_size=<bytes> threshold=<bytes>` - logged when a response with hidden fields exceeds the 500 KB threshold and bypasses token span indexing. Only integer sizes are logged.
  - `pypost/ui/widgets/response_view.py`: `response_masking_failed` - logged when JSON parsing or masking throws an unexpected exception during formatting. Raw payload content is omitted.
  - `pypost/ui/widgets/response_mask_controller.py`: `response_masking_spans_updated span_count=<count>` - logged when token span coordinates are loaded and updated in `ResponseMaskController`.
  - `pypost/ui/widgets/response_mask_controller.py`: `click_to_reveal_toggle path=<path> revealed=<boolean>` - logged when a user clicks on a masked token span to reveal or re-mask a field. Logs only the field selector path (e.g. `email`, `plan.name`, `accountId`) and the boolean toggle state (`revealed=True/False`), strictly omitting raw secret values and masked replacement tokens.

### Log Structure

Log format used:
- Structured logs: **Yes** (`snake_case_event key=value ...` formatting following project standard).
- Includes context: **Yes** (includes `path`, `format`, `requests`, `variables`, `presets`, `method`, `tool`, `selector_count`, `selectors_count`, `masked_fields_count`, `reason`, `type`, `span_count`, `revealed`, `payload_size`, `threshold`).
- Log levels: `DEBUG`, `INFO`, `WARNING`.
- **Zero Sensitive Data Leakage Invariant**:
  - Sensitive payload values, unmasked tokens, authorization headers, passwords, and user PII (such as GitHub emails/2FA flags, GitLab commit emails, and Jira Cloud account IDs/email addresses) are strictly excluded from all log records across all log levels.
  - On malformed or non-JSON responses, the error exception type (e.g. `reason=JSONDecodeError`) is logged without the raw invalid payload string.
  - Toggle events log only the selector path and boolean reveal state.
  - Large-document fallback logs only integer character and threshold counts.
  - Verified across automated tests in `tests/test_reference_collection_masking_contract.py`, `tests/test_mcp_hidden_response_fields_masking.py`, and `tests/test_gui_response_view_click_to_reveal.py`.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: `mcp_tool_call_duration_seconds{method, outcome}` (tracked in `pypost/core/mcp_observability.py` and `pypost/core/metrics_registry.py`), plus in-memory elapsed time recorded in `ResponseData.elapsed_time`.
- **Throughput**: `mcp_requests_received_total{method}` and `mcp_responses_sent_total{method, status}`. Desktop GUI interactions (clicks, cursor updates, formatting) execute within the Qt main thread with AST span caching to prevent UI stutter.
- **Error rate**: `mcp_responses_sent_total{method="tools/call", status="error"}` and `mcp_argument_validation_failures_total`.

### Business Metrics

- **Hidden Value Masking Applied Counter**:
  - `hidden_value_masks_applied_total`: Prometheus / OpenTelemetry counter tracking secret masking operations across all PyPost consumption surfaces.
    - **Metric Name**: `hidden_value_masks_applied_total`
    - **Surface Labels**:
      - `surface="mcp"`: Incremented in `MCPServerImpl._call_tool_inner` whenever an executed request specifies `hidden_response_fields` (e.g. `github-get-authenticated-user`, `gitlab-get-current-user`, `jira-get-current-user`, `jira-search-assignable-users`).
      - `surface="gui_response"`: Incremented in `ResponseView.display_response` whenever an incoming response has `hidden_fields` configured and one or more masked token spans are detected and formatted.
      - Existing surfaces: `surface="history"` (RequestService history records) and `surface="websocket"` (WebSocket message logging).
    - **Low Cardinality Guarantee**: Carries strictly static low-cardinality metadata (`surface`). No secret values, request URLs, parameter names, or field paths are embedded in metric labels.

### System Health Metrics

System health metrics:
- **Resource usage**: Large document threshold (500 KB / `LARGE_DOC_CHAR_THRESHOLD`) safeguards Qt document memory and CPU layout overhead by bypassing token span indexing on oversized payloads.
- **Component status**: `mcp_server_up` gauge (1 = running, 0 = stopped) via `MetricsTrackerProtocol.set_mcp_server_up`. `ResponseMaskController` lifecycle bound to `FoldableCodeView` and `ResponseView` parents; garbage-collected upon widget cleanup.

## OpenTelemetry Trace & Span Propagation

For environments configured with OpenTelemetry (`pypost/core/metrics_otel.py`):
- MCP tool call execution runs within OpenTelemetry tracer scopes when active.
- Tool call span attributes record safe execution metadata:
  - `mcp.tool.name`: Name of the invoked tool (e.g. `github_get_authenticated_user`, `gitlab_get_current_user`, `jira_get_current_user`, `jira_search_assignable_users`).
  - `mcp.outcome`: Outcome status (`success` or `error`).
  - `mcp.masking.applied`: Boolean flag or surface indicator when response masking was evaluated.
- In accordance with the zero-leakage security boundary, raw response bodies, unmasked secrets, and sensitive field contents are never attached as span attributes or OpenTelemetry span events.

## Security Audit & Privacy Boundary Verification

1. **Fail-Closed Malformed Payload & Non-JSON Handling**:
   - If an upstream API returns non-JSON, invalid JSON, or partial JSON fragments (e.g. HTML 500 error pages, XML responses, plain text logs), `sensitive_text_sanitizer.redact_json_response_fields` safely catches `(json.JSONDecodeError, TypeError, ValueError)` without crashing.
   - Text heuristics (`sanitize_text`) continue to redact environment variable secrets, Bearer tokens, and sensitive headers.
   - Diagnostic debug logs record only the exception type (`reason=JSONDecodeError`), guaranteeing no partial token strings are dumped into log files.
2. **In-Memory and Audit Log Immutability**:
   - Masking operates strictly during external output serialization for the MCP TextContent envelope or within the GUI `QTextDocument` presentation buffer.
   - Internal `ExecutionResult` and in-memory `ResponseData` remain authentic and unmutated.
   - Audit logs, curl generation, and local history entries retain pristine response data for human desktop inspection, ensuring compliance and forensic auditability.
3. **Irreversible MCP Security Boundary**:
   - MCP tool input schemas expose zero unmask parameters (`unmask`, `reveal`, `show_hidden`, `raw`).
   - MCPServerImpl registers zero unmask tools.
   - Any malicious arguments passed by AI agents are ignored, and output remains permanently masked with `'***'`.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`hidden_value_masks_applied_total{surface="mcp"}`, `hidden_value_masks_applied_total{surface="gui_response"}`)
- [x] OpenTelemetry metrics (`hidden_value_masks_applied_total` in `MetricsOTel`)
- [ ] Grafana dashboards (Centrally configured via standard PyPost Prometheus dashboards)
- [ ] Alerting rules (Alert on abnormal spike in MCP error outcomes or sudden drop in `mcp_server_up`)
- [x] Log aggregation (ELK, Loki, syslog-compatible structured log format)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`snake_case_event key=value ...`)
- [x] Metrics are collected correctly (`track_hidden_value_mask_applied` verified across MCP and GUI surfaces in contract tests)
- [x] Logging works in error and edge-case scenarios (malformed JSON, non-container JSON, empty bodies, large documents)
- [x] Large data structures and sensitive payload values are not logged (only selector counts, masked field counts, and safe paths emitted)
- [x] Metrics are available for monitoring via `MetricsRegistry` and `MetricsOTel`

## Notes

- All changes maintain 100% backward compatibility with existing MCP client contracts, GUI presentation workflows, and internal metrics tracking protocols.
- Logging levels adhere strictly to syslog/Python conventions (`DEBUG` for high-frequency field/selector inspection counts, `INFO` for operational lifecycle events).
- STEP 6 status remains `[/]` in `ai-tasks/PYPOST-1395/00-roadmap.md` awaiting final acceptance review by the orchestrator.
