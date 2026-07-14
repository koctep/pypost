# PYPOST-799 — Developer Documentation

> Parent: [PYPOST-799](https://pypost.atlassian.net/browse/PYPOST-799) — Close optional-metrics guard debt (PYPOST-44 TD-2)

## What Changed and Why

Verification-only closure — no source edits. PYPOST-73/74 delivered
`MetricsTrackerProtocol`, `NullMetrics`, `NULL_METRICS`, and `resolve_metrics()`. This ticket
audited the tree and confirmed PYPOST-44 TD-2 acceptance outcomes:

| Check | Result |
| --- | --- |
| `rg 'if self\._metrics' pypost/` | 0 optional-injection guard matches |
| `resolve_metrics` normalization sites | 11 direct consumers |
| Consumer call sites | Unconditional `track_*` / `set_mcp_server_up` |
| Regression suite | **1587 passed**, 1 deselected, 61 subtests |

Developers record tracking events without branching on “was metrics injected?” — optional injection
is resolved once at construction; omitted metrics silently no-op via `NULL_METRICS`.

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | Added PYPOST-799 closure cross-reference under MetricsTrackerProtocol section (content already documented in PYPOST-73/74) |

No new `doc/dev/` file required — the Null Object pattern, protocol contract, and test doubles
are already covered in [testability.md](../../doc/dev/testability.md).

## Architecture

| Component | Role |
| --- | --- |
| `pypost/core/metrics_protocol.py` | `MetricsTrackerProtocol`, `NullMetrics`, `NULL_METRICS`, `resolve_metrics()` |
| Direct consumers | `self._metrics = resolve_metrics(metrics)` in `__init__` or mixin wiring |
| Leaf consumers | Receive non-optional `MetricsTrackerProtocol` from upstream (e.g. `TabsPresenter`) |
| Pass-through wrappers | Forward optional `metrics` to a downstream resolver (`RequestWorker` → `RequestService`) |
| Composition root | `main.py` injects `MetricsManager` (or callers omit metrics) |

See [20-architecture.md](20-architecture.md) for the full module diagram and consumer inventory.

## Usage

### Direct consumer (normalize once)

```python
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics

class RequestService:
    def __init__(self, metrics: MetricsTrackerProtocol | None = None) -> None:
        self._metrics = resolve_metrics(metrics)

    def _track_send(self, method: str) -> None:
        self._metrics.track_request_sent(method)  # no if self._metrics guard
```

### Leaf consumer (upstream-resolved)

```python
def __init__(self, metrics: MetricsTrackerProtocol) -> None:
    self._metrics = metrics  # TabsPresenter / MainWindow already called resolve_metrics
```

### Test without metrics

Omit `metrics` or pass `None` — `NULL_METRICS` absorbs all tracking calls silently.

### Test with mock

```python
from unittest.mock import MagicMock

from pypost.core.metrics_protocol import MetricsTrackerProtocol

metrics = MagicMock(spec=MetricsTrackerProtocol)
service = RequestService(metrics=metrics)
service.execute(...)
metrics.track_request_sent.assert_called_once()
```

## Configuration

No new configuration. Metrics remains optional at the composition root:

- **Injected:** `MetricsManager` from `main.py` — Prometheus counters and MCP scrape unchanged.
- **Omitted:** `resolve_metrics(None)` → shared `NULL_METRICS` singleton — zero registry side effects.

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `AttributeError` on `self._metrics.track_*` | Consumer skipped `resolve_metrics()` | Normalize in `__init__`: `self._metrics = resolve_metrics(metrics)` |
| Test asserts `track_*` never called when metrics omitted | Expected — `NULL_METRICS` is silent | Pass `MagicMock(spec=MetricsTrackerProtocol)` to assert calls |
| `if self._metrics` guard reintroduced | Regression of TD-2 pattern | Remove guard; rely on `resolve_metrics()` at construction |
| Leaf presenter requires metrics but gets `None` | Upstream did not resolve | Resolve at presenter boundary before passing to leaf classes |

### Audit commands

```bash
rg 'if self\._metrics' pypost/
rg 'resolve_metrics' pypost/
make test
```

## Related Tests

```bash
.venv/bin/python -m pytest tests/test_metrics_protocol.py -v
make test
```

## Related Documentation

- [doc/dev/testability.md](../../doc/dev/testability.md) — MetricsTrackerProtocol and NullMetrics
- [PYPOST-73 dev notes](../PYPOST-73/70-dev-docs.md) — protocol introduction
- [PYPOST-74 dev notes](../PYPOST-74/70-dev-docs.md) — NullMetrics and guard removal
