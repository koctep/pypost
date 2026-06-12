# PYPOST-684: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/architecture_audit.md` | **Created** — boundary audit summary and recommendations |
| `doc/dev/architecture.md` | Refreshed directory tree; MCP, encryption, history, presenters |
| `doc/dev/README.md` | Added table-of-contents entry for boundary audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer-facing summary: [doc/dev/architecture_audit.md](../../doc/dev/architecture_audit.md)
- R-P2-005 (stale `architecture.md` tree) addressed in this step
- P1/P2/P3 remediation tickets tracked in [60-tech-debt.md](60-tech-debt.md)

## Boundary Rules (Quick Reference)

```text
main.py  →  ui/, core/
ui/      →  core/, models/
core/    →  models/          (exception: style_manager.py → ui/)
models/  →  (stdlib only)
```

## Related Capability Docs (Verified Aligned)

- [request_execution.md](../../doc/dev/request_execution.md)
- [mcp_integration.md](../../doc/dev/mcp_integration.md)
- [template_service.md](../../doc/dev/template_service.md)
- [testability.md](../../doc/dev/testability.md) — composition-root table omits MainWindow services
