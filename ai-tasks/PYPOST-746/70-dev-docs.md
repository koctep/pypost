# PYPOST-746 — Developer Documentation

> Parent: [PYPOST-746](https://pypost.atlassian.net/browse/PYPOST-746)

## What Changed

`MetricsRegistry._init_metrics` now delegates to four domain-specific private helpers:

| Helper | Domain |
| --- | --- |
| `_init_gui_metrics` | GUI interaction counters |
| `_init_http_metrics` | HTTP request, history, template, retry, masking |
| `_init_mcp_metrics` | MCP server counters, gauge, histogram |
| `_init_encryption_metrics` | Environment encryption counters |

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/maintainability_audit.md` | Removed resolved `_init_metrics` hotspot |
| `doc/dev/mcp_integration.md` | Notes domain-split init helpers on `MetricsRegistry` |

## Adding a New Metric

1. Pick the domain helper matching the metric surface (GUI, HTTP, MCP, encryption).
2. Register the Counter/Gauge/Histogram in that helper.
3. Add a public `track_*` method on `MetricsRegistry` if needed.
4. Extend `tests/test_metrics_registry.py` with a scrape assertion.
