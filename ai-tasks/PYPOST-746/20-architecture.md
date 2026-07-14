# PYPOST-746 — Architecture

## Approach

Pure extract-method refactor inside `MetricsRegistry`. No new types or modules.

## Domain Mapping

| Helper | Metrics |
| --- | --- |
| `_init_gui_metrics` | All `gui_*` counters (11) |
| `_init_http_metrics` | Request/history/template/retry/masking counters (14) |
| `_init_mcp_metrics` | MCP counters, gauge, histogram (5) |
| `_init_encryption_metrics` | Environment encryption counters (3) |

## Call Flow

```text
__init__ → _init_metrics
              ├── _init_gui_metrics
              ├── _init_http_metrics
              ├── _init_mcp_metrics
              └── _init_encryption_metrics
```

## Verification

- `tests/test_metrics_registry.py` — scrape assertions unchanged
- `tests/test_metrics_server_endpoint.py` — endpoint integration unchanged
