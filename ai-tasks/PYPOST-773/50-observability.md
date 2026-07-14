# PYPOST-773: Observability

**Verdict:** No observability code changes.

## Context

This task adds a TOC cross-link to the existing `doc/prometheus_monitoring.md` operator guide.
That document already covers:

- `/metrics` scrape endpoint and MCP `metrics://all` resource
- Settings for metrics server host/port
- Full Prometheus metric inventory by domain

## Logging / metrics

No new log events or Prometheus instruments. Discoverability improvement only.

## Related docs

- [doc/prometheus_monitoring.md](../../doc/prometheus_monitoring.md) — linked guide
- [doc/dev/observability_audit.md](../../doc/dev/observability_audit.md) — adjacent TOC entry
- [doc/dev/mcp_integration.md](../../doc/dev/mcp_integration.md) — references metric inventory
