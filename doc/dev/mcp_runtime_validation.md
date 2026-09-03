# MCP Runtime Validation and Observability

## Overview

PyPost validates arguments for inbound MCP request tools at runtime. The published
tool schema remains strict for discovery, while the application boundary produces
safe, parameter-specific diagnostics for invalid calls.

This guide covers the implementation delivered by PYPOST-1100. General server
transport and lifecycle details remain in [MCP Integration](mcp_integration.md).

The proxy lifecycle refactor delivered by PYPOST-1102 routes tool, prompt, and
resource forwarding through one `_dispatch_proxy_operation` boundary. The public
methods retain their existing signatures and result shapes; the shared boundary
owns header resolution, upstream cleanup, timeout/network mapping, timing,
metrics, activity entries, and safe completion logs. It does not add connection
pooling, so per-request upstream initialization remains the PYPOST-1101 scope.

## Architecture

The call flow has one application-owned validation boundary:

1. `MCPServerImpl` looks up the request or WebSocket-backed tool.
2. It resolves complete parameter declarations and the agent-visible declarations.
3. It checks required names and supplied values before dispatch.
4. HTTP request execution checks effective values again after defaults are applied.
5. The MCP SDK converts the safe application exception to an `isError` result.

`Server.call_tool(validate_input=False)` is intentional. It lets the application
adapter replace generic SDK schema errors, which can expose raw values or omit the
affected parameter name. `list_tools` still publishes the strict JSON Schema.

The main components are:

- `pypost/core/mcp_tool_contract.py` owns the runtime predicates and safe exception.
- `pypost/core/mcp_server_impl.py` owns resolution, validation, and dispatch.
- `pypost/core/websocket_mcp_tools.py` supplies WebSocket parameter declarations.
- `pypost/core/mcp_observability.py` records safe validation outcomes.
- `metrics_registry.py` and `metrics_otel.py` expose the monitoring surfaces.

## Validation Contract

Runtime values are accepted exactly when they match their declared type. Values are
never coerced, and `None` remains the existing default-application signal.

The supported declarations are:

| Declared type | Accepted runtime values |
| --- | --- |
| `string` | `str`, excluding `bool` because `bool` is not a string |
| `integer` | `int`, excluding `bool` |
| `number` | `int` or `float`, excluding `bool` |
| `boolean` | `bool` |
| `object` | `dict` |
| `array` | `list` |
| `integer_or_string` | `int` or a signed decimal string such as `-7` or `+007` |

For `integer_or_string`, decimal, exponent, and arbitrary strings are rejected.
Accepted values are passed onward unchanged. For example, `+007` remains the
string `+007`; it is not converted to the integer `7`.

Missing required names retain the existing application-level required-argument
behavior. Hidden environment-backed parameters are excluded from the visible
required set, but declared values are still checked against the complete set.

Legacy persisted defaults continue through the model's compatibility validation.
When an optional default is applied at execution time, the effective non-null value
is checked by the strict runtime predicate. An invalid legacy default therefore
fails safely instead of being silently coerced.

## Transport Behavior

Streamable HTTP and legacy SSE both reach the same registered `call_tool` handler.
An invalid call returns an MCP `CallToolResult` with `isError: true`. Its text names
the parameter and expected type without including the rejected raw value.

WebSocket-backed tools use the same preflight validation before
`execute_websocket_probe`. An invalid value never starts the probe. The optional
`stop_when` probe parameter is declared as a string and follows the same runtime
validation rules.

Upstream HTTP response status codes are not treated as argument-validation errors.
The existing structured response result continues to report those upstream results;
only application validation failures use the `validation_error` outcome.

## Safe Observability

Validation failures produce low-cardinality operational signals:

- The `mcp_argument_validation_failed` log records stage, transport, tool, parameter,
  and declared type. It never records supplied values, defaults, or payloads.
- The activity entry uses `outcome=validation_error` and records safe context only.
- Response and duration metrics use the `validation_error` outcome.
- `mcp_argument_validation_failures_total` is labeled by `stage`, `transport`, and
  `declared_type`.

The failure stages are `preflight` and `execution_boundary`. Prometheus, OpenTelemetry,
the null tracker, and Qt metric delegation expose the same counter contract.
The activity log remains bounded by its existing implementation.

Default application logs only the method, parameter, `default_applied=true`, and
declared type. Do not add raw values or large structures to validation logs.

## API and Usage

Declare a parameter on an exposed request or WebSocket tool with `McpToolParam`:

```python
McpToolParam(
    type="integer_or_string",
    description="The upstream identifier",
    required=True,
)
```

When adding a type, update the authoritative contract whitelist, runtime predicate,
published schema mapping, and contract tests together. Keep accepted values unchanged
through the request template and probe layers.

Run the focused validation tests through the repository Make target:

```sh
make test PYTEST_ARGS="tests/test_mcp_tool_contract.py \
tests/test_mcp_server_impl.py tests/test_mcp_server_integration.py \
tests/test_websocket_mcp_probe_repro.py tests/test_mcp_validation_observability.py"
```

## Configuration

PYPOST-1100 adds no settings or environment variables. Existing MCP bind and trust
choices remain documented in [MCP Trust Model](mcp_trust_model.md). Keep inbound MCP
on loopback unless an authenticated network boundary is provided.

## Troubleshooting

### The client shows generic SDK validation text

Confirm the registered handler uses `validate_input=False` and that the application
validator is reached. The published schema should remain strict; disabling the SDK
pre-handler check is limited to the registered application handler.

### The raw invalid value appears in a diagnostic

Treat this as a security defect. Check the `McpArgumentValidationError` message and
the validation logger first. Log parameter names and declared types only; never log
the argument mapping, default representation, or an exception containing the value.

### A WebSocket probe starts for a bad argument

Check that the tool uses `resolve_websocket_mcp_call_specs` before dispatch and that
`stop_when` is present in the complete runtime specification map. The probe must be
called only after required-name and value validation succeeds.

### An accepted value changes type or formatting

Inspect the request-template or probe boundary for implicit conversion. Runtime
validation is non-coercing; signed identifier strings such as `+007` must remain
strings all the way to the consumer.

### Validation metrics are missing

Check the tracker injection path and the metric surface being scraped. The counter
name is `mcp_argument_validation_failures_total`; use only its bounded stage,
transport, and declared-type labels.

## Related Artifacts

- [Requirements](../../ai-tasks/PYPOST-1100/10-requirements.md)
- [Architecture](../../ai-tasks/PYPOST-1100/20-architecture.md)
- [Cleanup report](../../ai-tasks/PYPOST-1100/40-code-cleanup.md)
- [Observability report](../../ai-tasks/PYPOST-1100/50-observability.md)
- [Technical debt](../../ai-tasks/PYPOST-1100/60-tech-debt.md)
