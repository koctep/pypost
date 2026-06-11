# PYPOST-73 — Developer Documentation

> Parent: [PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73)

## What Changed and Why

Consumers of metrics tracking now depend on `MetricsTrackerProtocol` instead of the concrete
`MetricsManager` facade (PYPOST-44 TD-1).

| Module | Role |
| --- | --- |
| `pypost/core/metrics_protocol.py` | `@runtime_checkable` protocol for all `track_*` methods |
| `pypost/core/metrics.py` | `MetricsManager` — still the composition-root facade |
| Consumers (services, workers, UI) | Type-hint `MetricsTrackerProtocol \| None` |

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | Protocol injection pattern for metrics |

## Usage

### Consumer injection

```python
from pypost.core.metrics_protocol import MetricsTrackerProtocol

class RequestService:
    def __init__(self, metrics: MetricsTrackerProtocol | None = None):
        self._metrics = metrics
```

### Test double

```python
from unittest.mock import MagicMock
from pypost.core.metrics_protocol import MetricsTrackerProtocol

metrics = MagicMock(spec=MetricsTrackerProtocol)
```

### Composition root (unchanged)

```python
from pypost.core.metrics import MetricsManager

metrics = MetricsManager()  # satisfies MetricsTrackerProtocol
MainWindow(metrics=metrics, ...)
```

## Related Tests

```bash
.venv/bin/python -m pytest tests/test_metrics_protocol.py tests/test_metrics_manager.py -v
```
