# PYPOST-750 — Architecture

## Approach

Documentation-only deliverable. Expand the operator-facing Prometheus guide with a complete
inventory table derived from `pypost/core/metrics_registry.py`.

## Document Structure

| Section | Content |
| --- | --- |
| Endpoints / Quick check | Unchanged (scrape and MCP resource) |
| Metric inventory summary | Count by type; link to source file |
| GUI metrics | 11 counters |
| HTTP / request metrics | 13 counters |
| MCP metrics | 3 counters, 1 gauge, 1 histogram |
| Environment encryption | 3 counters |
| Scrape config / troubleshooting | Unchanged |
| Developer reference | Cross-link to `doc/dev/mcp_integration.md` |

## Source of Truth

- **Primary:** `pypost/core/metrics_registry.py` — `_init_gui_metrics`, `_init_http_metrics`,
  `_init_mcp_metrics`, `_init_encryption_metrics`
- **Label values:** inferred from `track_*` call sites and docstrings where helpful

## Verification

- `rg 'Counter\(|Histogram\(|Gauge\(' pypost/core/metrics_registry.py` — row count matches
  catalog
- `make check` — no runtime changes
