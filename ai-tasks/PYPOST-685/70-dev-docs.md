# PYPOST-685: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/security_audit.md` | **Created** — security and secrets audit summary and recommendations |
| `doc/dev/README.md` | Added table-of-contents entry for security audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer-facing summary: [doc/dev/security_audit.md](../../doc/dev/security_audit.md)
- Documented policies largely match code for hidden keys, MCP schema filtering, and GUI history
  masking; residual risk is agent-visible response bodies, network bind defaults, and
  non-hidden credential persistence
- P1/P2/P3 remediation tickets tracked in [60-tech-debt.md](60-tech-debt.md)

## Operator Responsibilities (Quick Reference)

- Mark sensitive environment keys as **hidden** for UI masking, at-rest encryption, and history
  redaction
- Treat MCP tool results as containing full upstream response bodies and post-script logs
- Bind metrics and MCP servers to localhost unless the network trust model is explicit
- `expose_as_mcp` on any request in any loaded collection registers a tool when `enable_mcp` is on

## Related Policy Docs (Verified Baseline)

- [mcp_secrets_policy.md](../../doc/dev/mcp_secrets_policy.md)
- [sensitive_data_masking_policy.md](../../doc/dev/sensitive_data_masking_policy.md)
- [environment_encryption_at_rest.md](../../doc/dev/environment_encryption_at_rest.md)
- [hidden_variables.md](../../doc/dev/hidden_variables.md)
- [mcp_integration.md](../../doc/dev/mcp_integration.md)
- [copy_curl.md](../../doc/dev/copy_curl.md)
- [request_execution.md](../../doc/dev/request_execution.md)
