# PYPOST-1009: Observability Implementation

## Scope

**N/A — no new production observability.** PYPOST-1009 is verification debt: it
adds `test_write_encrypted_export_file_round_trips_through_import` so Export
cannot write Hidden plaintext (or fail same-key import) unnoticed when
encryption at rest is on. No production modules were changed; existing export
and encryption logging remains sufficient.

## Logging Implementation

### Added Logs

No new log statements — this ticket only added a test lock.

Describe added logging:

- **EMERG**: none — no system-failure path was introduced
- **ALERT**: none — no paging condition was introduced
- **CRIT**: none — no critical production error path was introduced
- **ERR**: none — no new execution-error log
- **WARNING**: none — no new warning site
- **NOTICE**: none — Python logging has no project-level NOTICE mapping
- **INFO**: none added
- **DEBUG**: none added

Existing production observability relevant to the path under test
(unchanged):

Core export (`pypost/core/environment_export.py`):

- INFO `environment_export_payload_built count=… includes_hidden=…` in
  `build_export_payload` (counts and Hidden flag; not serialized records).
- INFO `environment_export_file_written path=…` in `write_export_file`.

Core import (`pypost/core/environment_import.py`):

- INFO `environment_import_file_parsed path=… candidate_count=…
  error_count=…` in `load_import_candidates`.

Encryption serialize / decrypt (`environment_variables_adapter.py`,
`environment_secrets_codec.py`, `encryption_config.py`):

- INFO `storage_encryption_config_applied enabled=… key_source=…
  source_chain=… policy_source=…` when settings are applied.
- INFO `encryption_key_provider_built source_chain=…`.
- INFO `environment_serialized env_name=… encryption_enabled=…
  encrypted_count=… reused_count=… total_variables=…`.
- INFO `environment_deserialized env_name=… decrypted_count=…
  total_variables=…`.
- ERR `environment_value_encrypt_failed env_name=… key=… error=…`.
- DEBUG `env_value_encrypted algorithm=… version=… key_id=…`.
- DEBUG `env_value_decrypt_attempt key_id=…` and
  `env_value_decrypted key_id=…`.
- ERR `env_value_decrypt_failed reason=invalid_token key_id=…`.

Widget Export (not exercised by this test; still the operator surface):

- WARNING `environment_export_no_selection scope=…` and
  `environment_export_failed reason=…`.
- INFO `environment_export_completed count=… includes_hidden=… path=…`.

The new test uses real `StorageManager` plus
`build_export_payload` → `write_export_file` → `load_import_candidates`.
It therefore hits core export/import and adapter/codec events. It does not
open the Environment Manager modal or widget Export, so widget
`environment_export_*` events are not asserted here. That is expected: this
ticket locks encrypted file round-trip, not UI I/O.

Existing events omit secret strings, ciphertext, and full variable maps.
`env_name` and variable *key* names may appear on encrypt-failure ERR;
plaintext values and `ct` are not logged.

### Log Structure

Log format used:

- Structured logs: unchanged (existing key=value events)
- Includes context: N/A (no new events)
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: none — no new runtime path
- **Throughput**: none — no new runtime path
- **Error rate**: none — no new runtime path

Existing adapter metrics (unchanged):
`track_environment_value_encryption` on each new Hidden encrypt, and
`track_environment_encryption_error` on encrypt/decrypt failure. The lock
does not add counters.

### Business Metrics

Business metrics:

- none — verification debt only; Export volume is unchanged

### System Health Metrics

System health metrics:

- **Resource usage**: CPU, memory, disk — unchanged
- **Component status**: unchanged

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (no change)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A (no new events)

## Validation Results

Validation results:

- [x] Logs are correctly formatted — N/A (none added)
- [x] Metrics are collected correctly — N/A (none added)
- [x] Logging works in error scenarios — N/A (no new error path)
- [x] Large data structures are not logged — N/A (none added);
  existing export/encrypt events already omit records, secrets, and `ct`
- [x] Metrics are available for monitoring — N/A (none added)

Git status for this task: production tree unchanged;
`tests/test_environment_export.py` gained the encrypted round-trip lock only.

## Notes

Architecture planned test-only delivery. Step 6 confirms no observability
gap was introduced by locking encrypted Export → file envelope → same-key
import. Operators diagnosing Export still use existing
`environment_export_*` / `environment_import_file_parsed` events and
adapter/codec encryption logs. Adding logs on the test seam would not
improve production diagnosis and risks logging envelopes or secrets.
