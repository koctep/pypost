# PYPOST-787: Observability

## Scope

Dependency-only change. No runtime logging or metrics instrumentation added.

## OTel test coverage

Existing tests remain authoritative:

- `tests/test_metrics_otel.py` — OTel tracker protocol and instrument assertions
- CI and `make test` install `requirements-otel.txt` so these tests keep running

## Production default

Prometheus (`prometheus_client`) remains the default metrics backend in `requirements.txt`.
OpenTelemetry is opt-in via overlay install or `pip install -e ".[otel]"`.
