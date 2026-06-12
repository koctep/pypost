# PYPOST-688: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/observability_audit.md` | **Created** — observability and logging audit summary |
| `doc/dev/README.md` | Added table-of-contents entry for observability audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer summary: [doc/dev/observability_audit.md](../../doc/dev/observability_audit.md)
- Scale: 331 logger calls, 47 modules; 31 Prometheus metrics; MCP activity ring buffer (100)
- **P1:** Resolved URLs in http_client ERROR logs; print() in config/style managers
- CI: `log_cli=false`, `--log-file=pytest.log`, allowlist baseline 72 ERROR + margin 5
- P1/P2/P3 follow-ups in [60-tech-debt.md](60-tech-debt.md) (12 items, no Jira links)

## Related Docs

- [security_audit.md](../../doc/dev/security_audit.md) — secrets in logs (PYPOST-685)
- [testing.md](../../doc/dev/testing.md) — log_cli and CI guardrails
- [mcp_integration.md](../../doc/dev/mcp_integration.md) — MCP activity log UI
- [maintainability_audit.md](../../doc/dev/maintainability_audit.md) — error handling (PYPOST-687)
