# PYPOST-530: Observability

## Logging

- `encryption_migrate_command_started` now logs `json=` and `data_dir=` for operator traceability.
- `encryption_migrate_command_completed` unchanged (command, exit_code, success).
- Service-layer inventory and migration logs unchanged.

## Metrics

No new metrics; CLI is operator-facing and low frequency.

## JSON mode

Structured stdout is the observability surface for CI; stderr retains log lines when logging is
enabled.
