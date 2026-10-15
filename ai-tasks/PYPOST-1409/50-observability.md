# PYPOST-1409: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging and diagnostics have been reviewed and enhanced across the collection-scoped variable architecture:

- **WARNING**:
  - `pypost/core/library_manifest.py` — `legacy_manifest_variables_detected` (path): Emits warning log and `DeprecationWarning` when deprecated library-level `variables` are ingested in `LibraryManifest`.
  - `pypost/core/library_manifest.py` — `legacy_manifest_presets_detected` (path): Emits warning log and `DeprecationWarning` when deprecated library-level `presets` are ingested in `LibraryManifest`.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_missing_required_variables` (count, missing_names): Logs missing required non-secret variables before raising `ValueError("profile_invalid: required library variables are missing")`.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_variable_validation_failed` (error_count, errors): Logs variable schema validation failures before raising `ValueError("profile_invalid: library variables are invalid")`.
  - `pypost/core/variable_resolver.py` — `variable_resolution_missing_required` (missing_count, missing_names): Warns when required variables are not satisfied across all layers.
  - `pypost/core/variable_resolver.py` — `variable_resolution_validation_failed` (error_count, errors): Warns on variable type mismatches, safely redacting secret values as `[REDACTED]`.

- **INFO**:
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_runtime_validation_started` (library_id, manifest_id): Logs start of runtime row preparation.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_runtime_validation_completed` (duration_seconds, request_count, variable_count): Logs successful runtime resolution metrics.

- **DEBUG**:
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_profile_resolved` (profile_id, active_profile, environment_id): Logs profile selection source and ID.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_secret_masking_applied` (hidden_keys_count, overridable_keys_count): Logs secret masking counts without leaking secret values or key contents.
  - `pypost/core/variable_resolver.py` — `variable_resolution_completed` (total_resolved, default_count, profile_count, override_count, secret_count, missing_required_count, error_count): Structured resolution summary with layer provenance breakdown.
  - `pypost/core/variable_resolver.py` — `variable_resolution_detailed_completed` (total, secrets_count): Logs detailed resolution completion and secret variable count.
  - `pypost/core/library_manifest.py` — `manifest_deserialized_dict` (id, name, collections_count, variables_count): Manifest deserialization trace.

### Log Structure

Log format used:
- Structured logs: yes (key=value syslog-style attributes).
- Includes context: yes (library_id, manifest_id, profile_id, counts, durations, and safe non-secret diagnostic lists).
- Log levels: WARNING, INFO, DEBUG.
- Secret masking: Secrets and sensitive values are never logged; type validation mismatches redact secret values to `[REDACTED]`, and `hidden_keys` masking ensures non-secret variable validation checks do not leak secrets.

## Provenance Tracking & Diagnostics

- **VariableProvenance**:
  - `DEFAULT`: Layer 1 collection defaults (fallback to manifest defaults for backwards compatibility).
  - `PROFILE`: Layer 2 collection presets / active profiles (fallback to manifest presets).
  - `LOCAL_OVERRIDE`: Layer 3 local overlay overrides.
  - `LOCAL_SECRET`: Layer 3 local overlay secrets.
- **ManifestDiagnosticError**:
  - `MANIFEST_INVALID_ROOT`: Root element is not a dict.
  - `MANIFEST_VALIDATION_ERROR`: Schema validation errors with line/column and json path locator.
  - `MISSING_REQUIRED_SECRET`: Unfulfilled required variables under strict resolution mode.
  - `TYPE_MISMATCH`: Variable type validation failures under strict resolution mode.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Validation latency**: Tracked via `time.monotonic()` in `LibraryRuntimeResolver.resolve` and logged in `duration_seconds` for both success and failure paths.

### Business Metrics

- **Validation outcome**: Tracked via `MetricsTrackerProtocol.track_mcp_library_validation(category)`:
  - Recorded with `"success"` upon successful resolution.
  - Recorded with error category (e.g., `"library_invalid"`, `"manifest_invalid"`, `"profile_missing"`, `"profile_invalid"`) upon failure.

### System Health Metrics

- Maintained through existing MCP service metrics tracker protocol (`resolve_metrics`).

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`track_mcp_library_validation` category counters).
- [ ] Grafana dashboards.
- [ ] Alerting rules.
- [x] Log aggregation (ELK, Loki) via structured key=value format.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (verified with `tests/test_library_manifest_observability.py`).
- [x] Metrics are collected correctly (validated via `_metrics.track_mcp_library_validation`).
- [x] Logging works in error scenarios (legacy deprecation warnings, missing required variables, secret type validation failures).
- [x] Large data structures are not logged (only metadata, counts, and identifier keys).
- [x] Secrets are strictly redacted in error strings and logs.
- [x] Quality gates pass: `make lint`, `make typecheck`, `make verify-ai-tasks`, `make test`.

## Notes

- Deprecation warnings (`DeprecationWarning`) alert consumers to migrate manifest-level variables and presets into individual collections without breaking legacy workflows.
- Secret masking contracts are strictly enforced across overlay, variable resolution, and runtime preparation boundaries.
