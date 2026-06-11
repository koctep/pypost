# PYPOST-487: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: N/A for this task.
- **ALERT**: N/A for this task.
- **CRIT**: N/A for this task.
- **ERR**:
  - `encryption_migration_decrypt_failed` in `pypost/core/encryption_migration.py` —
    decrypt failure during verify or rewrite (`error_count`, per-environment `detail`).
  - `encryption_migration_missing_kids` in `pypost/core/encryption_migration.py` —
    historical `kid` values with no resolvable key material (`count`).
- **WARNING**:
  - `encryption_migration_verify_completed success=false` — verify finished with errors
    (`error_count`).
  - `encryption_migration_operation_skipped reason=encryption_disabled` — rewrite blocked
    because encryption policy is off.
  - `encryption_migration_operation_completed success=false` — rewrite aborted after missing
    keys or decrypt errors (`operation`, `error_count`).
- **NOTICE** (mapped to **INFO** — Python stdlib has no NOTICE level):
  - N/A; significant lifecycle events use INFO below.
- **INFO**:
  - `environments_backup_created` — timestamped backup before write (`path`).
  - `encryption_migration_inventory_built` — inventory summary after scan
    (`environment_count`, `hidden_value_count`, `encrypted_envelope_count`,
    `plaintext_hidden_count`, `missing_kid_count`).
  - `encryption_migration_verify_started` / `encryption_migration_verify_completed success=true`.
  - `encryption_migration_operation_started` — rewrite entry (`operation`, `dry_run`,
    `backup`).
  - `encryption_migration_operation_skipped reason=no_plaintext_hidden` — encrypt-plaintext
    no-op.
  - `encryption_migration_dry_run_completed` — projected post-rewrite counts (`operation`,
    `projected_encrypted_count`, `active_kid`).
  - `encryption_migration_save_completed` — environments persisted (`operation`,
    `backup_path`, `environment_count`).
  - `encryption_migration_operation_completed success=true` — successful rewrite.
  - `encryption_migrate_command_started` / `encryption_migrate_command_completed` in
    `scripts/encryption_migrate.py` — CLI lifecycle (`command`, `exit_code`, `success`).
- **DEBUG**: N/A added in this step.

Existing `StorageManager` and `EnvironmentVariablesAdapter` logs (`save_environments_completed`,
`environment_serialized`, `environment_value_encrypt_failed`, etc.) continue to emit during
bulk save and load inside migration flows.

### Log Structure

Log format used:

- Structured logs: yes (key=value fields)
- Includes context: yes (`operation`, counts, `backup_path`, `active_kid`; no secret values
  or ciphertext)
- Log levels: INFO, WARNING, ERROR

## Metrics Implementation (if applicable)

No Prometheus metrics. `encryption_migrate.py` is an operator CLI that runs outside the
desktop metrics server; it does not register or expose counters or histograms.

**Monitoring surface for operators:**

- Structured logs on stderr (redirect to a log collector when automating runs).
- CLI exit code (`0` success, `1` failure) from `encryption_migrate_command_completed`.
- Human-readable inventory on stdout (not a metrics feed).

`StorageManager.save_environments` may emit existing storage encryption counters when the
desktop app saves environments, but that path is separate from this CLI and is not part of
migration observability.

### Performance Metrics

Added performance metrics:

- **Response time**: not added (operator CLI; no latency SLO).
- **Throughput**: not added.
- **Error rate**: not exported; failures appear in logs and exit code.

### Business Metrics

Business metrics:

- Inventory and outcome counts are logged only (not exported as Prometheus series) because the
  CLI is an infrequent operator tool.

### System Health Metrics

System health metrics:

- **Resource usage**: not added.
- **Component status**: migration success/failure surfaced via CLI exit code and logs.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics (CLI does not expose metrics)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.) — operators may pipe stderr to their collector

## Validation Results

Validation results:

- [x] Logs are correctly formatted
- [ ] Metrics are collected correctly (N/A — no CLI metrics)
- [x] Logging works in error scenarios (caplog tests for missing-kid and decrypt-failure paths)
- [x] Large data structures are not logged (counts and identifiers only)
- [ ] Metrics are available for monitoring (N/A — logs and exit code only)

Validation commands:

- `python3 -m py_compile pypost/core/encryption_migration.py scripts/encryption_migrate.py`
- `pytest tests/test_encryption_migration.py tests/test_encryption_migrate_cli.py -q`

## Notes

Operators should direct stderr to their log collector when running `encryption_migrate.py`; stdout
remains the human-readable inventory report. Secret values and key material are never logged.
