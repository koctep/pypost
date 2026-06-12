# PYPOST-579: Dev Docs (Step 7)

## Updated

- `doc/dev/testability.md` — OTel adapter injection example.
- `doc/dev/mcp_integration.md` — metrics stack table includes `metrics_otel.py`.

## Operator / developer usage

```python
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from pypost.core.metrics_otel import create_otel_metrics_tracker

reader = PeriodicExportingMetricReader(OTLPMetricExporter())
provider = MeterProvider(metric_readers=[reader])
metrics = create_otel_metrics_tracker(meter_provider=provider)

# Inject into services the same way as MetricsManager tracking surface:
# RequestService(metrics=metrics)
```

## Tests

```bash
.venv/bin/python -m pytest tests/test_metrics_otel.py -v
```
