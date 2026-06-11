# PYPOST-75 — Developer Documentation

> Parent: [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75)

## What Changed and Why

`MetricsManager` was split into focused modules (PYPOST-44 TD-3 / PYPOST-49):

| Module | Class | Role |
| --- | --- | --- |
| `pypost/core/metrics_registry.py` | `MetricsRegistry` | Prometheus counters + `track_*` (no I/O) |
| `pypost/core/metrics_server.py` | `MetricsServer` | MCP `metrics://all`, uvicorn lifecycle |
| `pypost/core/metrics.py` | `MetricsManager` | Facade — unchanged public API for injection |

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/mcp_integration.md` | Metrics section documents three-module layout |
| `doc/dev/testability.md` | Composition root table notes registry vs server split |

## Usage

### Counter-only tests

```python
from pypost.core.metrics_registry import MetricsRegistry

registry = MetricsRegistry()
registry.track_request_sent("GET")
```

### Full app wiring (unchanged)

```python
from pypost.core.metrics import MetricsManager

metrics = MetricsManager()
metrics.start_server(host, port)
metrics.track_gui_send_click()
metrics.stop_server()
```

### Scraping registry

```python
from prometheus_client import generate_latest

mm = MetricsManager()
text = generate_latest(mm.registry).decode("utf-8")
```

## Related Tests

```bash
.venv/bin/python -m pytest tests/test_metrics_manager.py -v
```
