# PYPOST-1060: Observability Implementation

## Logging Implementation

### Context and Observability Analysis

In PYPOST-1060, a plaintext in-memory `deserialize_environment_records` helper method was added to the test double `FakeStorageManager` (`tests/helpers/__init__.py`), aligning it with the `StorageInterface` protocol defined in `pypost/core/storage_interface.py` and matching the signature of `StorageManager.deserialize_environment_records` in `pypost/core/storage.py`.

Observability across environment record deserialization is partitioned between production execution and test execution:

1. **Production Storage Deserialization (`pypost/core/storage.py::StorageManager.deserialize_environment_records`)**:
   - Handles envelope decryption (via `_env_adapter`) and Pydantic model validation.
   - Emits structured error logs on unexpected deserialization errors:
     - `ERROR`: `deserialize_environment_records_item_failed name=%s error=%s` (with exception traceback via `logger.exception`).
   - Collects and returns structured `EnvironmentLoadFailure(name, environment_id, reason)` tuples for all failed items (`EnvironmentEncryptionError`, `ValidationError`, unexpected exceptions).
   - This production logging behavior is completely preserved and untouched.

2. **Test Double Deserialization (`tests/helpers/__init__.py::FakeStorageManager.deserialize_environment_records`)**:
   - Operates in-memory on raw dictionaries and `Environment` instances without requiring cryptography keys or filesystem interaction.
   - For invalid records (non-mapping items, missing required fields, `ValidationError`, generic exceptions), it constructs and returns structured `EnvironmentLoadFailure(name, environment_id, reason)` tuples without writing noisy exception logs to stdout/stderr.
   - This keeps unit and presenter test outputs clean and free from intentional failure log noise while giving tests deterministic access to failure metadata.

### Added Logs

No new production logging statements were required for this task as `FakeStorageManager` is a test helper located in `tests/helpers/__init__.py`.

Existing preserved production logs in `pypost/core/storage.py`:
- **ERR / ERROR**: `pypost/core/storage.py::deserialize_environment_records` - `deserialize_environment_records_item_failed name=%s error=%s`
- **ERR / ERROR**: `pypost/core/storage.py::load_environments` - `load_environments_failed file=%s error=%s`
- **ERR / ERROR**: `pypost/core/storage.py::save_environments` - `save_environments_replace_failed src=%s dst=%s error=%s`
- **INFO**: `pypost/core/storage.py::save_environments` - `save_environments_completed count=%d encrypted_count=%d reused_count=%d file=%s`

### Log Structure

Log format used in production storage module:
- Structured logs: Yes (`event_name key1=%s key2=%s`)
- Includes context: Yes (environment name, file path, exception messages)
- Log levels: `ERROR`, `INFO`

## Metrics Implementation (if applicable)

### Performance Metrics

Not applicable. `FakeStorageManager.deserialize_environment_records` is an in-memory test utility executing in sub-millisecond time.

### Business Metrics

Not applicable.

### System Health Metrics

Not applicable.

## Monitoring Integration

- [ ] Prometheus metrics (N/A)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [x] Log aggregation (ELK, Loki, syslog) — Production storage logs use structured key-value formats compatible with log aggregators.

## Validation Results

Validation results:
- [x] Logs are correctly formatted: Production `StorageManager` logs follow `event_name key=val` format.
- [ ] Metrics are collected correctly: N/A.
- [x] Logging works in error scenarios: Production error logging in `pypost/core/storage.py` is covered by existing storage test suites; `FakeStorageManager` error handling is verified by `tests/test_fake_storage_manager.py`.
- [x] Large data structures are not logged: Only environment name and error message are logged; full secret payloads or environment dictionaries are omitted.
- [ ] Metrics are available for monitoring: N/A.

## Notes

### Diagnostic Behavior of Test Double

`FakeStorageManager` deliberately does not call `logger.exception` or `logger.error` when encountering malformed records during testing:
- **Clean Test Execution**: In unit tests (e.g., `tests/test_env_presenter.py`, `tests/test_fake_storage_manager.py`), tests deliberately inject invalid payload dictionaries to verify failure handling. Emitting `logger.exception` would pollute test output and could cause false positives in test log scanners.
- **Strict Return Verification**: Callers receive the exact tuple of `EnvironmentLoadFailure` objects, enabling test assertions on failure reasons and names (`assert len(failures) == 1`, `assert failures[0].name == "bad_env"`).
