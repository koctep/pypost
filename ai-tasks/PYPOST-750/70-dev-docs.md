# PYPOST-750 — Developer Documentation

> Parent: [PYPOST-750](https://pypost.atlassian.net/browse/PYPOST-750)

## What Changed

Published a complete operator-facing Prometheus metrics inventory sourced from
`metrics_registry.py`.

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/prometheus_monitoring.md` | Full inventory tables by domain; corrected type summary |
| `doc/dev/mcp_integration.md` | Link to operator metrics catalog |

## For Maintainers

When adding or renaming a metric in `metrics_registry.py`, update the matching row in
`doc/prometheus_monitoring.md` and verify the registration count with:

```bash
rg 'Counter\(|Histogram\(|Gauge\(' pypost/core/metrics_registry.py | wc -l
```
