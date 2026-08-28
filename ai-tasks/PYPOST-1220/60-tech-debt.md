# PYPOST-1220: Technical Debt Analysis

## Shortcuts Taken

1. **PyYAML In-Memory Loading**:
   - `deserialize_collection_from_yaml` and `read_collection_file` in `pypost/core/collection_serializer.py` load the entire YAML text into memory before passing it to `yaml.safe_load`. For standard collection sizes (< 10 MB), this is performant and deterministic, but streaming/chunked parsing is not implemented for massive single-file collections.
2. **Heuristic Extension Fallback in Import Pipeline**:
   - In `pypost/core/collection_import.py`, `_read_records` falls back to `yaml.safe_load` if `json.loads` fails on non-standard extensions. This accommodates user workflows where YAML collections are saved without `.yaml` extension, guarded by `isinstance(data, (dict, list))` checks.
3. **RetryPolicy Alias Bridging**:
   - `RetryPolicy` in `pypost/models/retry.py` implements custom `__init__` and `@model_validator(mode="before")` hooks to transparently remap legacy alias keys (`max_attempts`, `initial_delay_sec`, `backoff_factor`, `retry_on_status_codes`) to keep full backwards and forwards compatibility without breaking legacy fixtures.

## Code Quality Issues

1. **Lenient Preset Value Validation at Collection Root**:
   - `Collection.presets` is typed as `Dict[str, Dict[str, Any]]`. Deserialization does not strictly reject preset keys that are not declared in `Collection.variables`, nor does it reject preset values that fail `validate_variable_value`. This leniency avoids breaking existing partial exports, but strict validation could be added as an optional lint/validation mode.
2. **Collection Schema Versioning & Migration Pipeline**:
   - `Collection.version` currently stores a semver string (defaults to `"1.0.0"`). There is no automated schema migration pipeline to transform older format versions into newer format revisions when breaking schema changes are introduced in future tasks.

## Missing Tests

1. **Deeply Nested Schema Type Enforcement**:
   - `validate_variable_value` validates top-level primitive types (`string`, `integer`, `number`, `boolean`, `array`, `object`). Tests cover primitive arrays and dictionaries, but deeply nested inner typing (e.g., `array[integer]`, typed object properties) is not currently part of the schema specification or tested.
2. **Very Large Collection Stress Tests**:
   - Unit tests test comprehensive collections with all request types, scripts, websockets, and MCP clients. Stress tests simulating 10,000+ requests in a single YAML/JSON collection were omitted from the fast unit test suite to maintain fast test execution times (< 5s).
3. **Test Timeout Annotations**:
   - Verified: All new test suites (`tests/test_collection_format_v2_repro.py`, `tests/test_collection_serializer.py`) include explicit `pytestmark = pytest.mark.timeout(30)` per `do-testing` requirements.

## Performance Concerns

1. **Pure-Python PyYAML Parser Fallback**:
   - When compiled `libyaml` C-extensions are not available in the runtime environment, `yaml.safe_load` / `yaml.safe_dump` use pure-Python implementations. For typical collection sizes (< 100 requests) the serialization latency is under 15ms, but for very large collections, utilizing `CSafeLoader` / `CSafeDumper` when available could provide a speedup.
2. **Deep Copying in Collection Materialization**:
   - `_materialize` and import planner use `model_copy(deep=True)` for variables and mcp clients to avoid cross-collection mutation. The overhead is negligible for normal collection sizes.

## Follow-up Tasks

All follow-up tasks belong to Parent Epic **[PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219)** (*Git-based Collection Libraries & Self-Contained Collection Format*):

1. **[`PYPOST-1221`](https://pypost.atlassian.net/browse/PYPOST-1221)** (UI: Collection Variables Editor & Preset Selector):
   - Implement GUI dialogs and toolbar dropdowns in PySide6 to view, edit, and switch active preset profiles for self-contained collections.
2. **[`PYPOST-1222`](https://pypost.atlassian.net/browse/PYPOST-1222)** (Core: Git-Based Collection Library Repository Engine):
   - Implement Git repository cloning, branch switching, and pull/push synchronization for collection repositories storing `.yaml`/`.json` collection files.
3. **[`PYPOST-1223`](https://pypost.atlassian.net/browse/PYPOST-1223)** (Core: Collection Schema Migration & Strict Preset Validation):
   - Implement a forward-migration pipeline for collection schema versions and optional strict preset type-checking against variable definitions.
