# PYPOST-689: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/performance_audit.md` | **Created** — performance and scalability audit summary |
| `doc/dev/README.md` | Added table-of-contents entry for performance audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer summary: [doc/dev/performance_audit.md](../../doc/dev/performance_audit.md)
- Threading: 4 `QThread` workers (send, env, migration, paste JSON); 3 daemon threads (MCP,
  metrics, history save)
- Template: compile LRU (256), ~0.7 ms render per typical HTTP request (PYPOST-455)
- **P1:** Unbounded response buffering; synchronous collection load at startup
- P1/P2/P3 follow-ups in [60-tech-debt.md](60-tech-debt.md) (12 items, no Jira links)

## Related Docs

- [request_execution.md](../../doc/dev/request_execution.md) — execution pipeline
- [template_service.md](../../doc/dev/template_service.md) — compile cache (PYPOST-628)
- [environment_storage_async.md](../../doc/dev/environment_storage_async.md) — async env pattern
- [observability_audit.md](../../doc/dev/observability_audit.md) — metrics and logs (PYPOST-688)
