# PYPOST-704: Default metrics bind to localhost

## Definition of Done

- `AppSettings.metrics_host` defaults to `127.0.0.1` (aligned with `mcp_host`).
- Starting metrics server on a non-loopback address logs a security warning.
- Tests cover default and warning behavior.
