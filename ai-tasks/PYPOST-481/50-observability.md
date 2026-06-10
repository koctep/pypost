# PYPOST-481: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:
- **INFO**: `pypost/core/storage.py` — `storage_encryption_config_applied` when settings are applied
  to storage (enabled flag, key source, policy source: settings vs env fallback).
- **INFO**: `pypost/ui/main_window.py` — extended `settings_applied` log with
  `env_encryption_enabled` and `env_encryption_key_source`.
- **WARNING**: `pypost/core/encryption_config.py` — `encryption_key_source_unsupported` when
  persisted key source is not yet implemented (falls back to environment).

Existing PYPOST-447 encryption logs and metrics remain unchanged for save/load crypto operations.

### Log Structure

Log format used:
- Structured logs: yes (key=value fields)
- Includes context: yes (enabled, key_source, policy_source)
- Log levels: INFO, WARNING (new); existing ERR/DEBUG from key provider unchanged

## Metrics Implementation (if applicable)

No new metrics. Existing counters continue to track encrypt/decrypt/error paths:
- `environment_value_encryptions_total`
- `environment_value_decryptions_total`
- `environment_encryption_errors_total{stage,reason}`

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (no new metrics this task)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:
- [x] Logs are correctly formatted
- [x] Metrics are collected correctly (unchanged behavior verified by storage tests)
- [x] Logging works in error scenarios (inherits PYPOST-447 coverage)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring

## Notes

Policy application is logged once per `apply_encryption_settings` call (startup and settings save),
not on every environment read/write.
