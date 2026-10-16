# Collection-Scoped Variables Integration Suite and Compatibility Matrix (PYPOST-1412)

## Overview

Developer documentation decisions and records for [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) (COLVAR-4: Integration test suite, compatibility matrix, and developer documentation under parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) and architectural decomposition [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)).

This step consolidates the architectural developer documentation across all epic components: catalog discovery, standalone MCP server execution, workspace collection import, and request template substitution. It formalizes the 4-quadrant backward compatibility matrix, secret safety contracts, and the integration test harness.

## Documentation Updates

1. **Updated Developer Guide**:
   - [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md)
     - Documented the comprehensive multi-subsystem architecture connecting catalog discovery ([`LibraryManagerService`](file:///home/src/pypost/core/library_manager_service.py)), standalone MCP server execution ([`MCPServerRegistry`](file:///home/src/pypost/core/mcp_server_registry.py) and [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py)), workspace collection import ([`import_collection_variables_to_environment`](file:///home/src/pypost/core/collection_variable_import.py)), and request template substitution ([`TemplateService`](file:///home/src/pypost/core/template_service.py)).
     - Added the formal 4-quadrant backward compatibility matrix table spanning modern v2 catalog manifests and legacy v1 manifests against modern v2 collections and legacy v1 collections.
     - Documented 3-tier precedence resolution hierarchy, legacy fallback rules, and non-fatal deprecation notices (`legacy_manifest_variables_detected`, `legacy_manifest_presets_detected`, `DeprecationWarning`).
     - Documented secret safety and diagnostic boundaries: comprehensive secret masking in `hidden_keys`, zero plaintext leaks in error traces/logs/summaries (`[REDACTED]`), and differentiated missing variable handling (fatal for non-secret, tolerated for secret during initialization).
     - Documented the integration test harness ([`CollectionVariablesIntegrationHarness`](file:///home/src/tests/test_collection_scoped_variables_integration.py)) in `tests/test_collection_scoped_variables_integration.py`.
     - Updated Child Task Execution Sequence and Phased Roadmap marking all four child stories (PYPOST-1409, PYPOST-1410, PYPOST-1411, PYPOST-1412) as completed.
2. **Updated Documentation Index**:
   - [`doc/dev/README.md`](../../doc/dev/README.md)
     - Updated line 66 under "Collections and environments" to cover PYPOST-1407–1412.

## Architecture

- **Catalog Discovery Layer ([`LibraryManagerService`](file:///home/src/pypost/core/library_manager_service.py))**: Indexes and loads `pypost-library.json` catalog files purely as collection indices, decoupling collection schemas from root manifest structures.
- **Standalone MCP Server Subsystem ([`MCPServerRegistry`](file:///home/src/pypost/core/mcp_server_registry.py), [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py))**: Runs standalone MCP server processes without workspace environments (`environment_id=None`), resolving parameters directly from self-contained collection presets and local overlays (`0o600`).
- **Workspace Environment Subsystem ([`import_collection_variables_to_environment`](file:///home/src/pypost/core/collection_variable_import.py), [`EnvironmentVariablesWidget`](file:///home/src/pypost/ui/widgets/environments/environment_variables_widget.py))**: Imports collection variables into workspace environments, enforcing conflict resolution policies (`SKIP` vs `OVERWRITE`) and automatically mapping `secret=True` variables to `Environment.hidden_keys`.
- **Request Templating Layer ([`TemplateService`](file:///home/src/pypost/core/template_service.py))**: Interpolates mustache-style `{{ variable }}` expressions across request URLs, authentication headers, and request payloads using the imported environment variables.
- **Integration Test Harness ([`CollectionVariablesIntegrationHarness`](file:///home/src/tests/test_collection_scoped_variables_integration.py))**: Encapsulates isolated temporary directories, services, and configuration stores for reproducible end-to-end multi-subsystem workflow and compatibility verification.

[Link to Architecture Specification](../../ai-tasks/PYPOST-1412/20-architecture.md)

## API / Usage

### `CollectionVariablesIntegrationHarness(tmp_path: Path)`

Test harness encapsulating isolated filesystem roots, storage managers, connection stores, overlay managers, and service instances.

#### `create_library(manifest_id, is_legacy_manifest, collections_data, manifest_variables, manifest_presets) -> Path`

Synthesizes an isolated library directory under `tmp_path/libraries/<manifest_id>` containing catalog or legacy manifests and connects it to `LibraryManagerService`.
- **manifest_id**: Unique identifier for the library.
- **is_legacy_manifest**: If `True`, emits v1 manifest with root `variables` and `presets`; otherwise v2 catalog index.
- **collections_data**: Mapping of filename to collection dictionary.
- **Returns**: `Path` to created library directory.

#### `create_workspace_environment(name="Test Env", variables=None, hidden_keys=None) -> Environment`

Creates and persists an isolated workspace environment under `tmp_path/workspace/environments/`.
- **name**: Human-readable environment name.
- **variables**: Key-value mapping of environment variables.
- **hidden_keys**: Set of variable names to treat as sensitive secrets.
- **Returns**: Persisted [`Environment`](file:///home/src/pypost/models/models.py) instance.

#### `run_unified_lifecycle(...) -> UnifiedLifecycleResult`

Executes the complete multi-subsystem integration lifecycle: catalog discovery → standalone server startup → collection copy → workspace import → request template substitution.
- **manifest_id**: Library identifier to load.
- **collection_data**: Collection dictionary defining requests, variables, and presets.
- **active_profile**: Preset profile name to activate.
- **overlay_secrets**: Key-value mapping of machine-local secrets.
- **workspace_env_name**: Target workspace environment name.
- **conflict_strategy**: `ConflictStrategy.SKIP` or `ConflictStrategy.OVERWRITE`.
- **Returns**: [`UnifiedLifecycleResult`](file:///home/src/tests/test_collection_scoped_variables_integration.py) containing server status, imported variable summary, and rendered request URL, headers, and body.

## Configuration & Compatibility

### 4-Quadrant Compatibility Matrix

| Quadrant | Manifest Variant | Collection Variant | Variable Precedence | Deprecation Notice |
| :---: | :--- | :--- | :--- | :--- |
| **Q1** | Modern Catalog (v2) | Modern Collection (v2) | Collection defaults → Collection preset → Local overlay | None (Golden Standard) |
| **Q2** | Legacy Manifest (v1) | Modern Collection (v2) | Collection wins for overlapping keys; Manifest fallback for omitted keys | `logger.warning("legacy_manifest_variables_detected")` |
| **Q3** | Legacy Manifest (v1) | Legacy Collection (v1) | Manifest fallback defaults and presets | `logger.warning("legacy_manifest_variables_detected")` |
| **Q4** | Modern Catalog (v2) | Legacy Collection (v1) | Empty resolution (`{}`); required variables flag diagnostic error | None |

## Troubleshooting

### Issue: Legacy Manifest Warning Logs Emitted
- **Symptom**: `legacy_manifest_variables_detected` or `legacy_manifest_presets_detected` warning logs appear during library connection.
- **Cause**: The library manifest (`pypost-library.json` or `pypost-library.yaml`) declares root-level `variables` or `presets` fields.
- **Solution**: Migrate variables and presets into the respective `collection.json` files and remove the root fields from the manifest.

### Issue: Missing Required Variable in Standalone MCP Server
- **Symptom**: `ValueError: profile_invalid: required library variables are missing: ['...']`.
- **Cause**: A non-secret variable marked `required=True` lacks a default value and was not supplied in the active preset or overlay.
- **Solution**: Provide a default value in the collection, add it to the preset in `collection.presets`, or specify an override in the local overlay.

### Issue: Secret Plaintext Display in UI / Logs
- **Symptom**: Secret value appears unmasked in variable tables or diagnostic summaries.
- **Cause**: Variable was declared without `secret=True` or imported with a custom mapping.
- **Solution**: Ensure `secret: True` is set on the `CollectionVariable`. The import helper automatically registers all `secret=True` variables in `Environment.hidden_keys`.
