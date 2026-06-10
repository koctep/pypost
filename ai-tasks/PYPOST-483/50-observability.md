# PYPOST-483: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:
- **EMERG**: N/A for this task.
- **ALERT**: N/A for this task.
- **CRIT**: N/A for this task.
- **ERR**:
  - `encryption_key_unavailable` in `pypost/core/key_provider.py` — no source yields an active
    key (`reason=no_source_provided_active_key`).
  - `encryption_key_rotation_lookup_failed` in `pypost/core/key_provider.py` — historical
    `key_id` not found in any configured source during decrypt (`reason=no_source_provided_key`).
- **WARNING**:
  - `encryption_key_source_unsupported` in `pypost/core/encryption_config.py` — persisted source
    not supported; falls back to environment (PYPOST-481).
  - `key_source_chain_active_fallback` / `key_source_chain_by_id_fallback` in
    `pypost/core/key_sources/chain.py` — primary (or earlier) source unavailable; chain
    continues to next source (`failed_source`, `next_source`, optional `key_id`).
  - `secret_backend_chain_fallback` in `pypost/core/key_sources/secret_store.py` — secret-store
    backend unavailable; chain continues (`failed_type`, `next_type`).
- **NOTICE** (mapped to **INFO** — Python stdlib has no NOTICE level):
  - `key_source_chain_active_resolved_via_fallback` / `key_source_chain_by_id_resolved_via_fallback`
    in `pypost/core/key_sources/chain.py` — key resolved from a non-primary source after earlier
    sources were skipped (`source`, `key_id`, `skipped_sources`).
  - `secret_backend_chain_resolved_via_fallback` in `pypost/core/key_sources/secret_store.py` —
    registry loaded from a non-first backend (`backend_type`, `skipped_types`).
- **INFO**:
  - `encryption_key_provider_built` in `pypost/core/encryption_config.py` — provider factory
    wired with ordered `source_chain`.
  - `storage_encryption_config_applied` in `pypost/core/storage.py` — extended with
    `source_chain` alongside primary `key_source`, `enabled`, and `policy_source`.
  - `key_source_chain_active_attempt` / `key_source_chain_by_id_attempt` in
    `pypost/core/key_sources/chain.py` — chain resolution started (`sources`, optional `key_id`).
- **DEBUG**:
  - Per-source resolve/match events in `env.py`, `keyring.py`, `secret_store.py` (key material
    never logged; `key_id`, paths, and reasons only).
  - Per-source unavailable/resolution events in `pypost/core/key_sources/chain.py`.
  - Registry/spec/backend file load diagnostics in `env.py` and `secret_store.py`.

Existing PYPOST-447 encrypt/decrypt logs and metrics in `storage.py` remain unchanged.

### Log Structure

Log format used:
- Structured logs: yes (key=value fields)
- Includes context: yes (`source`, `key_id`, `source_chain`, `skipped_sources`, `reason`)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Secret safety: raw key material and Fernet strings are never logged

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
- [x] Metrics are collected correctly (unchanged behavior)
- [x] Logging works in error scenarios (key provider and chain tests)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring

## Notes

Key resolution is logged on each `get_current_key()` / `get_key_by_id()` call through the chain,
not on every environment variable read/write. Provider construction is logged once per
`build_key_provider()` / `apply_encryption_settings()` call. Fallback WARNING/INFO pairs help
operators distinguish misconfigured primary sources from expected multi-source rotation setups.
