# PYPOST-74 — Developer Documentation

> Parent: [PYPOST-74](https://pypost.atlassian.net/browse/PYPOST-74)

## What Changed and Why

Optional metrics injection no longer uses `None` guards at call sites. Consumers normalize
injection via `resolve_metrics()` and default to `NULL_METRICS` (PYPOST-44 TD-2).

| Module | Role |
| --- | --- |
| `pypost/core/metrics_protocol.py` | `NullMetrics`, `NULL_METRICS`, `resolve_metrics()` |
| Consumers | `self._metrics = resolve_metrics(metrics)`; direct `track_*` calls |

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | NullMetrics pattern; removed future-ticket row |

## Usage

### Consumer injection

```python
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics

class RequestService:
    def __init__(self, metrics: MetricsTrackerProtocol | None = None):
        self._metrics = resolve_metrics(metrics)

    def _track_send(self, method: str) -> None:
        self._metrics.track_request_sent(method)
```

### Test without metrics

Omit `metrics` or pass `None` — tracking is silently discarded via `NULL_METRICS`.

### Test with mock

```python
from unittest.mock import MagicMock
from pypost.core.metrics_protocol import MetricsTrackerProtocol

metrics = MagicMock(spec=MetricsTrackerProtocol)
service = RequestService(metrics=metrics)
```

## Related Tests

```bash
.venv/bin/python -m pytest tests/test_metrics_protocol.py -v
```
