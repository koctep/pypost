# PYPOST-73: Code Cleanup

## Actions

- No trailing whitespace introduced in changed files.
- Imports updated: consumers import `MetricsTrackerProtocol` from `metrics_protocol`, not
  `MetricsManager` from `metrics`.
- `MetricsManager` import retained only in composition root (`main.py`, `MainWindow`).

## Verification

- Grep confirms no stray `MetricsManager` type hints outside facade/composition root.
