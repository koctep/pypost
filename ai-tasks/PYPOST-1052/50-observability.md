# PYPOST-1052: Observability Implementation

## Overview

Task PYPOST-1052 widened the parameter discovery regex in `pypost/core/mcp_secrets_policy.py` (`_MCP_REQUEST_VAR_PATTERN = re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")`) to detect `mcp.request.VAR` placeholders even when embedded within Jinja expressions, filter pipelines, string concatenations, or nested function calls.

This document evaluates the observability, logging safety, and metrics telemetry associated with MCP tool contract discovery and execution.

## Observability Requirements Analysis

| Component | Telemetry / Observability Role | Security / Privacy Constraints |
| --- | --- | --- |
| `McpSecretsPolicy` | Static parameter extraction & schema building (`extract_mcp_request_variables`, `build_agent_input_schema`, `safe_execution_log_fields`) | Must never log secret values, environment keys, or sensitive payload contents. Only aggregate diagnostic counts. |
| `MCPServerImpl` | MCP server runtime (`list_tools`, `call_tool`, `_build_execution_variables`) | Emits diagnostic debug logs on variable merge and tool execution; reports request/response metrics to `MetricsTrackerProtocol`. |
| `McpActivityLog` | In-memory operational activity audit log | Stores sanitized execution summaries (`mcp_arg_count`, `duration_ms`, `outcome`, `http_status`) without sensitive payload dump. |

## Logging Implementation

### Added Logs

The regex widening in `McpSecretsPolicy` is a pure, side-effect-free, in-memory string scanning operation. No new runtime log statements were required for parameter extraction.

Existing logging across the MCP server subsystem continues to provide comprehensive visibility:

- **EMERG**: N/A - no emergency system failure states.
- **ALERT**: N/A - no immediate operational action alerts.
- **CRIT**: N/A - no critical unrecoverable errors.
- **ERR**: `MCPServerImpl.call_tool` - logs execution exceptions or captures error details in structured responses.
- **WARNING**: N/A in normal discovery; emitted on unexpected transport disconnects or stale alert handler cleanup.
- **NOTICE**: N/A.
- **INFO**: `MCPServerImpl` lifecycle events and activity logging.
- **DEBUG**: `MCPServerImpl._build_execution_variables` - emits structured diagnostic counts (`mcp_execution_variables_merged env_var_count=%d hidden_key_count=%d mcp_arg_count=%d`) via `McpSecretsPolicy.safe_execution_log_fields`.
- **DEBUG**: `MCPServerImpl.__init__` - emits template service injection diagnostics (`MCPServerImpl: using injected TemplateService id=%d`).

### Log Structure

Log format used:
- Structured logs: **Yes** (key-value counts and structured JSON responses via `format_structured_tool_result`).
- Includes context: **Yes** (HTTP method, tool name, outcome, status code, argument count, duration).
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.

### Secret and Diagnostic Count Safety

`McpSecretsPolicy.safe_execution_log_fields` provides safe diagnostic count logging without exposing secret names, variable keys, or values:

```python
@staticmethod
def safe_execution_log_fields(
    env_var_count: int,
    hidden_key_count: int,
    mcp_arg_count: int,
) -> dict[str, int]:
    """Diagnostic counts only — no variable names or values."""
    return {
        "env_var_count": env_var_count,
        "hidden_key_count": hidden_key_count,
        "mcp_arg_count": mcp_arg_count,
    }
```

During execution, `MCPServerImpl` consumes these counts to produce safe debug log output:
`logger.debug("mcp_execution_variables_merged env_var_count=%d hidden_key_count=%d mcp_arg_count=%d", ...)`
ensuring that neither secret names nor runtime variable values leak into application logs.

## Metrics Implementation (if applicable)

### Performance Metrics

Standard MCP server metrics integrated via `MetricsTrackerProtocol`:
- **Response time**: `track_mcp_tool_call_duration(method, outcome, duration_sec)` — measured in `MCPServerImpl.call_tool`.
- **Throughput**: `track_mcp_request_received(method)` and `track_mcp_response_sent(method, outcome)` — recorded per tool invocation.
- **Error rate**: Error counts differentiated by `outcome="error"` and tracked against execution error categories.

### Business Metrics

- **Tool Call Activity**: `McpActivityLog` records `McpActivityEntry.new_call_tool(name, outcome, mcp_arg_count, http_status, detail, duration_ms)`.
- **Tool Listing Activity**: `McpActivityLog` records `McpActivityEntry.new_list_tools(tool_count)`.

### System Health Metrics

- **Concurrency Control**: Tool calls are bounded by `_call_tool_semaphore` (`DEFAULT_MAX_CONCURRENT_MCP_CALLS = 4`) preventing system exhaustion.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`MetricsTrackerProtocol` Prometheus implementation)
- [x] Grafana dashboards (standard PyPost metrics dashboard)
- [x] Alerting rules (PyPost alert manager / Prometheus alerts)
- [x] Log aggregation (ELK, Loki, syslog-compatible structured log output)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (Key-value pairs in debug logs, valid JSON in structured tool outputs)
- [x] Metrics are collected correctly (`track_mcp_request_received`, `track_mcp_response_sent`, `track_mcp_tool_call_duration`)
- [x] Logging works in error scenarios (Handled gracefully in `MCPServerImpl.call_tool` with sanitized detail messages)
- [x] Large data structures are not logged (Only integer counts returned by `safe_execution_log_fields`; response bodies sanitized)
- [x] Metrics are available for monitoring (Standard metrics protocol instrumentation)

## Notes

- MCP tool discovery and schema generation remain completely deterministic and CPU-efficient with zero new runtime logging overhead.
- All secrets and sensitive parameters remain masked across logs, activity entries, and agent schema outputs.
