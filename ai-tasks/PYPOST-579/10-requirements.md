# PYPOST-579: OpenTelemetry adapter for MetricsTrackerProtocol

## Goals

Production deployments may prefer OpenTelemetry export over the embedded Prometheus
scrape endpoint. Consumers already depend on `MetricsTrackerProtocol` ([PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73)); they must be able to receive an OTel-backed tracker without API changes at call sites.

## User Stories

- As an **operator**, I want to wire an OTel `MeterProvider` (OTLP, Prometheus remote write,
  etc.) so application counters flow into my observability backend.
- As a **developer**, I want a drop-in tracker that mirrors existing Prometheus metric names
  and labels so dashboards and alerts stay comparable during migration.
- As a **test author**, I want unit tests that validate OTel recording without a live exporter.

## Definition of Done

- [x] `OtelMetricsTracker` implements every `MetricsTrackerProtocol` method.
- [x] Metric names and label keys match `MetricsRegistry` / Prometheus definitions.
- [x] Factory helper accepts an optional `MeterProvider` for composition-root wiring.
- [x] Automated tests cover protocol compliance and representative counter/histogram/gauge paths.
- [x] Developer documentation describes when and how to use the adapter.
- [x] Full test suite passes.

## Task Description

Follow-up from [PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73) tech debt:
"No OpenTelemetry adapter — future work once protocol exists."

## Q&A

- **Q:** Does this replace `MetricsManager` in the desktop app?
  **A:** No — default remains Prometheus + local scrape. OTel is an optional adapter for
  production injection at the composition root.
- **Q:** Does this add OTLP export configuration?
  **A:** No — callers configure exporters on the `MeterProvider` they pass in.
