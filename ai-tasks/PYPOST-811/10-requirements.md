# PYPOST-811: Lazy-import metrics_otel when OTel not installed

## Summary

Follow-up from [PYPOST-787](https://pypost.atlassian.net/browse/PYPOST-787) item **Lazy-import
metrics_otel when OTel not installed**. OpenTelemetry is an optional overlay dependency; importing
`pypost.core.metrics_otel` must not fail when OTel packages are absent.

## Acceptance Criteria

1. Top-level OpenTelemetry imports in `pypost/core/metrics_otel.py` are wrapped in an optional
   import guard following the `environment_secrets_codec.py` pattern.
2. Instantiating `OtelMetricsTracker` or calling `create_otel_metrics_tracker` without OTel
   installed raises a clear `ImportError` with install guidance.
3. `tests/test_metrics_otel_import.py` verifies the module is importable when OTel packages are
   blocked.
4. Existing `tests/test_metrics_otel.py` functional tests remain green with OTel overlay installed.
5. `make check` passes.

## Out of Scope

- Wiring `pip install -e ".[otel]"` as the primary Makefile install path (PYPOST-812).
- CI job validating editable OTel extra end-to-end.
- Changing default metrics backend (Prometheus remains default).

## User Stories

- As a **contributor** on a production-only venv, I can import `pypost.core.metrics_otel` without
  installing the OTel overlay unless I instantiate the tracker.
- As a **maintainer**, I want import-safety regression coverage so future call sites do not
  assume OTel is always present at import time.

## Q&A

| Question | Answer |
| --- | --- |
| Pattern to follow? | `environment_secrets_codec.py` try/except + `_ensure_*_available()` |
| Error type? | `ImportError` with message referencing `.[otel]` / `make venv-otel` |
| Where to test? | Dedicated import-safety module blocking `sys.modules` OTel entries |
