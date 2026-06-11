# PYPOST-540: Observability Implementation

## Logging Implementation

### Added Logs

- **INFO** — `encryption_migrate_command_started` now includes `config_dir=%s` alongside
  existing `command`, `json`, and `data_dir` fields in `scripts/encryption_migrate.py`.

### Unchanged Logs

- `encryption_migrate_command_completed` — no change (exit code and success already logged).
- `EncryptionMigrationService` logs — unaffected; service receives settings from caller.

## Metrics

No new metrics. Path overrides are operator CLI concerns; desktop app paths unchanged.

## Validation

Operators can confirm the intended config path from stderr when running with default logging:

```
encryption_migrate_command_started command=verify json=False data_dir=None config_dir=/path/to/restored-config
```
