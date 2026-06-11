# PYPOST-382: Observability

## New debug logs

| Location | Message | When |
| --- | --- | --- |
| `RequestService.__init__` | `using injected HTTPClient id=%d` | `http_client` provided |
| `RequestService.__init__` | `using injected MCPClientService id=%d` | `mcp_client` provided |
| `HTTPClient.__init__` | `using injected requests.Session id=%d` | `session` provided |

These follow the existing injection-tracing pattern from PYPOST-378 (`TemplateService id=%d`).

## Metrics

No new Prometheus counters. Transport and MCP mocks in unit tests bypass metrics paths unless
explicitly asserted.

## Verification

Set log level to `DEBUG` and construct services with injected dependencies in a REPL or test
breakpoint to confirm log lines appear once per injected instance.
