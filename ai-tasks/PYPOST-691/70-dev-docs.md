# PYPOST-691: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/dependencies_audit.md` | **Created** — dependencies and supply chain audit summary |
| `doc/dev/README.md` | Added table-of-contents entry for dependencies audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer summary: [doc/dev/dependencies_audit.md](../../doc/dev/dependencies_audit.md)
- **15** direct production deps in `requirements.txt`; **1** lower-bound pin (`pydantic>=2.0`)
- **P1:** Unpinned graph + `mcp` v2 risk; no pip-audit in CI
- P1/P2/P3 follow-ups in [60-tech-debt.md](60-tech-debt.md) (12 items, no Jira links)

## Dependency Policy Quick Reference

```text
Production:  requirements.txt  →  make install
Dev tools:   Makefile venv-test + CI pip install (unpinned — gap)
Lock file:   none (gap)
CVE scan:    none in CI (gap)
Dependabot:  none (gap)
```

## Related Docs

- [mcp_integration.md](../../doc/dev/mcp_integration.md) — MCP server architecture
- [setup.md](../../doc/dev/setup.md) — install paths (partial dep list)
- [testing.md](../../doc/dev/testing.md) — CI pip cache (PYPOST-311)
- [security_audit.md](../../doc/dev/security_audit.md) — inbound network exposure (PYPOST-685)
