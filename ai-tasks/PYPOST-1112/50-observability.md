# PYPOST-1112: Observability Implementation

## Logging Implementation

### Added Logs

- **DEBUG**: `pypost/core/key_sources/env.py:38` - `logger.debug("env_keys_file_load_failed path=%s reason=%s", path, exc)` (file I/O / JSON decoding failure)
- **DEBUG**: `pypost/core/key_sources/env.py:41` - `logger.debug("env_keys_file_invalid path=%s", path)` (non-dict payload or invalid keys dict)
- **DEBUG**: `pypost/core/key_sources/env.py:47` - `logger.debug("env_keys_file_active_key_invalid path=%s", path)` (active key missing or invalid in keys mapping)
- **DEBUG**: `pypost/core/key_sources/env.py:57` - `logger.debug("env_keys_file_missing path=%s", path)` (configured registry file does not exist)

### Log Structure

- Structured logs: yes (key=value formatted log messages)
- Includes context: yes (file paths, reason codes)
- Log levels: `DEBUG` (consistent with quiet failure / fallback semantics in key source resolution)

## Metrics Implementation (if applicable)

N/A — Key source resolution operates during startup and configuration loading; metrics are handled by the higher-level key provider and OTel metrics pipeline.

## Monitoring Integration

- [x] Standard application logging via standard library `logging.getLogger(__name__)`

## Validation Results

- [x] Logs are correctly formatted
- [x] Logging works in error scenarios (verified with unit tests)
- [x] Large data structures are not logged (key materials are never logged; only path and key IDs where safe)

## Notes

All key source logs maintain secret safety: key material values are never included in log strings.
