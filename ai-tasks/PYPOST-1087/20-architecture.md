# Architecture: PYPOST-1087

## Allowlist Rule Disposition

### Mechanism Analysis
- `unittest._log._AssertLogsContext` replaces handlers and sets `logger.propagate = False` on the targeted logger.
- Therefore, `assertLogs` blocks will never leak records into root logging handlers configured with `--log-file`.
- Any integration test or runner without `assertLogs` will propagate ERROR logs to the root handler.
- Maintaining the rule in `tests/expected_log_allowlist.yaml` ensures that if `mcp_server_start_failed_ui` is ever emitted during test executions outside `assertLogs`, the CI guardrail recognizes it as an approved error rather than failing the build.

### Proposed Annotation
Update comment in `tests/expected_log_allowlist.yaml` to explain the forward-looking status and interaction with `assertLogs`.
