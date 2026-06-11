# PYPOST-144: Observability

## Existing Logging (unchanged)

| Component | Event | Level |
|-----------|-------|-------|
| `HTTPClient.__init__` | Injected `TemplateService` id | `DEBUG` |
| `HTTPClient.__init__` | Default `TemplateService` | `DEBUG` |
| `MCPServerImpl.__init__` | Injected `TemplateService` id | `DEBUG` |

## Changes

No new metrics or log lines. This ticket confirms injection paths already emit debug logs
when a `TemplateService` is provided, consistent with `RequestService` and
`MCPServerManager`.
