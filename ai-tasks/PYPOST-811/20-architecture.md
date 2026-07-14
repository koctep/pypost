# PYPOST-811: Lazy-import metrics_otel architecture

## Problem

`pypost/core/metrics_otel.py` imported OpenTelemetry at module load time. After PYPOST-787 moved
OTel to an optional overlay, any unconditional import of the module failed on production-only
installs even though the default app path never loads it.

## Approach

Mirror the optional-dependency guard in `pypost/core/environment_secrets_codec.py`:

```
try:
    from opentelemetry import ...
except ImportError:
    metrics = None
    Meter / Observation / MeterProvider = Any stubs

def _ensure_otel_available() -> None:
    if metrics is None:
        raise ImportError(...)

class OtelMetricsTracker:
    def __init__(...):
        _ensure_otel_available()
        ...
```

## Components

| Component | Role |
| --- | --- |
| `pypost/core/metrics_otel.py` | Optional import guard + runtime availability check |
| `tests/test_metrics_otel_import.py` | Block OTel in `sys.modules`, reload module, assert import + runtime errors |
| `tests/test_metrics_otel.py` | Unchanged functional coverage when OTel overlay is installed |

## Import vs runtime behavior

| OTel installed | `import metrics_otel` | `OtelMetricsTracker()` |
| --- | --- | --- |
| Yes | Success | Success |
| No | Success | `ImportError` with install hint |

## Test strategy

1. Save and remove `pypost.core.metrics_otel` and `opentelemetry.*` from `sys.modules`.
2. Patch `sys.modules` so OTel top-level resolves to `None` (forces import failure).
3. `importlib.import_module("pypost.core.metrics_otel")` — must succeed.
4. Assert tracker factory calls raise `ImportError`.
5. Restore saved modules so subsequent OTel functional tests are unaffected.
