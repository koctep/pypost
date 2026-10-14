# PYPOST-1378: Observability Implementation

## Logging Implementation

### Added Logs

The following structured log events are implemented and maintained across PyPost core components for permanent MCP response masking:

- **EMERG**: None (not applicable for response sanitization operations).
- **ALERT**: None (not applicable for response sanitization operations).
- **CRIT**: None (critical runtime errors handled by standard top-level error boundaries).
- **ERR**: None (execution failures recorded via execution result errors without exposing unredacted payload values).
- **WARNING**: None (regular non-JSON payloads or non-matching fields are safe expected states, not operational warnings).
- **NOTICE**: None (syslog NOTICE level mapped to standard Python logging INFO).
- **INFO**:
  - `pypost/core/mcp_server_impl.py`: `mcp_param_default_applied method=<method> param=<param> default_applied=true default_type=<type>` - logged when default tool parameters are applied during tool call argument merging.
  - `pypost/core/mcp_secrets_policy.py`: `mcp_env_override_applied key=<key>` - logged when permitted non-hidden environment variable override is applied.
- **DEBUG**:
  - `pypost/core/mcp_server_impl.py`: `mcp_response_masking_applied method=<method> tool=<tool> selector_count=<count>` - logged when an MCP tool invocation processes a request configured with `hidden_response_fields`. Emits tool name and number of configured selectors, strictly excluding secret values.
  - `pypost/core/sensitive_text_sanitizer.py`: `redact_json_response_fields_completed selectors_count=<count> masked_fields_count=<count>` - logged upon successful JSON traversal and redaction. Records the count of active selectors and total number of field occurrences masked with `***`, omitting sensitive key names and payload values.
  - `pypost/core/sensitive_text_sanitizer.py`: `redact_json_response_fields_skipped_non_json reason=<exception_type>` - logged when body text is non-JSON or malformed (e.g. `JSONDecodeError`). Emits only the exception class name without echoing the malformed body text, preventing secret leakage from malformed responses.
  - `pypost/core/sensitive_text_sanitizer.py`: `redact_json_response_fields_skipped_non_container type=<type_name>` - logged when parsed JSON is a primitive rather than a dictionary or list container.
  - `pypost/core/mcp_server_impl.py`: `mcp_execution_variables_merged env_var_count=<n> hidden_key_count=<n> mcp_arg_count=<n> defaults_applied_count=<n>` - logged prior to tool execution with integer diagnostic counts only.

### Log Structure

Log format used:
- Structured logs: **Yes** (`snake_case_event key=value ...` formatting following project standard).
- Includes context: **Yes** (includes `method`, `tool`, `selector_count`, `selectors_count`, `masked_fields_count`, `reason`, `type`).
- Log levels: `DEBUG`, `INFO`.
- **Zero Secret Leakage Invariant**:
  - Sensitive payload values, unmasked tokens, authorization headers, passwords, and user PII are strictly excluded from all log records across all log levels.
  - On malformed or non-JSON responses, the error exception type (e.g. `reason=JSONDecodeError`) is logged without the raw invalid payload string.
  - Verified by automated unit test `test_mcp_masking_observability_metrics_and_logs` and `test_mcp_masking_observability_malformed_json_fallback_logs`.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: `mcp_tool_call_duration_seconds{method, outcome}` (tracked in `pypost/core/mcp_observability.py:35` and `pypost/core/metrics_registry.py`).
- **Throughput**: `mcp_requests_received_total{method}` and `mcp_responses_sent_total{method, status}` (tracked via `MetricsTrackerProtocol`).
- **Error rate**: `mcp_responses_sent_total{method="tools/call", status="error"}` and `mcp_argument_validation_failures_total`.

### Business Metrics

- **Permanent Masking Counter**:
  - `hidden_value_masks_applied_total`: Prometheus / OpenTelemetry counter tracking secret masking operations across PyPost surfaces.
    - **Metric Name**: `hidden_value_masks_applied_total`
    - **Surface Label**: `surface="mcp"` (alongside existing surfaces `"history"` and `"websocket"`).
    - **Trigger**: Incremented in `MCPServerImpl._call_tool_inner` whenever an executed request specifies `hidden_response_fields`.
    - **Low Cardinality**: Carries strictly static low-cardinality metadata (`surface="mcp"`). No secret values, request URLs, or field paths are embedded in metric labels.

### System Health Metrics

System health metrics:
- **Resource usage**: Handled by host-level telemetry and process monitoring.
- **Component status**: `mcp_server_up` gauge (1 = running, 0 = stopped) via `MetricsTrackerProtocol.set_mcp_server_up`.

## OpenTelemetry Trace & Span Propagation

For environments configured with OpenTelemetry (`pypost/core/metrics_otel.py`):
- MCP tool call execution runs within OpenTelemetry tracer scopes when active.
- Tool call span attributes record safe execution metadata:
  - `mcp.tool.name`: Name of the invoked tool (e.g. `get_customer_secret`).
  - `mcp.outcome`: Outcome status (`success` or `error`).
  - `mcp.masking.applied`: Boolean flag or surface indicator (`mcp`) when response masking was evaluated.
- In accordance with the zero-leakage security boundary, raw response bodies, unmasked secrets, and sensitive field contents are never attached as span attributes or OpenTelemetry span events.

## Security Audit & Fail-Closed Boundaries

1. **Fail-Closed Malformed Payload Handling**:
   - If upstream API responses return non-JSON, invalid JSON, or partial JSON fragments, `sensitive_text_sanitizer.redact_json_response_fields` safely catches `(json.JSONDecodeError, TypeError, ValueError)` without crashing the server.
   - Text heuristics (`sanitize_text`) continue to redact environment variable secrets, Bearer tokens, and sensitive headers.
   - Diagnostic debug logs record only the exception type (`reason=JSONDecodeError`), guaranteeing no partial token strings are dumped into log files.
2. **In-Memory and Audit Log Immutability**:
   - Masking operates strictly during external output serialization for the MCP TextContent envelope.
   - Internal `ExecutionResult` and in-memory `ResponseData` remain authentic and unmutated.
   - Audit logs and local history entries retain pristine response data for human desktop inspection, ensuring compliance and forensic auditability.
3. **Irreversible MCP Security Boundary**:
   - MCP tool input schemas expose zero unmask parameters (`unmask`, `reveal`, `show_hidden`, `raw`).
   - MCPServerImpl registers zero unmask tools.
   - Any malicious arguments passed by AI agents are ignored, and output remains permanently masked with `'***'`.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`hidden_value_masks_applied_total{surface="mcp"}`, `mcp_requests_received_total`, `mcp_responses_sent_total`, `mcp_tool_call_duration_seconds`)
- [x] OpenTelemetry metrics (`hidden_value_masks_applied_total` in `MetricsOTel`)
- [ ] Grafana dashboards (Configured centrally via standard PyPost Prometheus dashboards)
- [ ] Alerting rules (Alert on abnormal spike in MCP error outcomes or sudden drop in `mcp_server_up`)
- [x] Log aggregation (ELK, Loki, syslog-compatible structured log format)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`snake_case_event key=value ...`)
- [x] Metrics are collected correctly (`self._metrics.track_hidden_value_mask_applied("mcp")` asserted in unit tests)
- [x] Logging works in error and edge-case scenarios (malformed JSON, non-container JSON, empty bodies)
- [x] Large data structures and sensitive payload values are not logged (only selector counts and masked field counts are emitted)
- [x] Metrics are available for monitoring via `MetricsRegistry` and `MetricsOTel`

## Notes

- All changes maintain 100% backward compatibility with existing MCP client contracts and internal metrics tracking protocols.
- Logging levels adhere strictly to syslog/Python conventions (`DEBUG` for high-frequency field/selector inspection counts, `INFO` for operational lifecycle events).
- STEP 6 status remains `[/]` in `ai-tasks/PYPOST-1378/00-roadmap.md` awaiting final acceptance review by the orchestrator.
