# PYPOST-579: Architecture

## Components

| Component | Role |
| --- | --- |
| `pypost/core/metrics_otel.py` | `OtelMetricsTracker` + `create_otel_metrics_tracker` factory |
| `pypost/core/metrics_protocol.py` | Structural protocol (unchanged) |
| `pypost/core/metrics_registry.py` | Prometheus reference; label normalization reused |
| `tests/test_metrics_otel.py` | In-memory `MeterProvider` assertions |

## Data flow

```text
Composition root configures MeterProvider + OTLP exporter
        │
        ▼
create_otel_metrics_tracker(meter_provider) ──► OtelMetricsTracker
        │
        ▼
Consumers (RequestService, HTTPClient, presenters, …) call track_* unchanged
```

## Design decisions

| Decision | Rationale |
| --- | --- |
| Mirror Prometheus names/labels | Operators can migrate backends without renaming metrics |
| Reuse `_normalize_new_tab_source` | Identical label cardinality as `MetricsRegistry` |
| Observable gauge for `mcp_server_up` | Matches Prometheus gauge semantics (0/1 absolute) |
| Optional `MeterProvider` in factory | Exporter config stays at composition root |
| No change to `MetricsManager` default | Desktop app keeps embedded Prometheus server |

## Out of scope

- Wiring OTel into `main.py` by default
- Replacing `MetricsServer` / `/metrics` scrape endpoint
- Auto-discovery of OTLP endpoints from environment variables
