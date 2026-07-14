# PYPOST-733: Observability

## Changes

- `deserialize_environment_records` now uses `logger.exception` for unexpected per-item failures,
  preserving stack traces in logs for operator diagnosis.
- All other log event names and levels unchanged — behaviour-preserving refactor.

## No New Metrics

Exception narrowing does not alter metric emission paths.
