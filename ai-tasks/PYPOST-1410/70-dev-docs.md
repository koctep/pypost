# PYPOST-1410: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) (Feature / COLVAR-2: Standalone MCP server configuration and execution without workspace environment under parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) and architectural decomposition [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)).

## Documentation Updates

1. **Updated Developer Guide**:
   - [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md)
     - Documented the completed implementation of standalone MCP server configuration and execution ([PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410)).
     - Documented `McpServerConfiguration.environment_id: Optional[str] = None` and the Pydantic root validator `validate_server_type_requirements` allowing standalone library servers to omit workspace environments while preserving mandatory environment checks for workspace local servers.
     - Documented decoupled runtime resolution in [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py) when `environment_id is None`:
       - Loading profile presets from `overlay.active_profile` if set.
       - Clean fallback to collection defaults (`profile_id = None`, `profile = {}`) emitting structured debug log `mcp_library_profile_fallback_to_defaults` when no active profile is specified.
       - Evaluating variables via 3-tier precedence in [`LibraryVariableResolver`](file:///home/src/pypost/core/variable_resolver.py).
       - Enforcing empty `overridable_keys` and aggregating `hidden_keys` for secret masking.
     - Documented server registry lifecycle and reference reconciliation in [`MCPServerRegistry`](file:///home/src/pypost/core/mcp_server_registry.py):
       - Dedicated branches in `reconcile_references()` for `configuration.library_id` and `configuration.bundled_library` that skip workspace environment checks when `environment_id is None`.
       - Preservation guarantee: standalone servers remain active and are never stopped or marked `"failed"` during workspace environment deletion or pruning.
       - Process startup logging (`standalone=True`), reference verification via `library_service.get_connection()`, and ignoring standalone servers during `refresh_environment()`.
     - Documented UI configuration and presentation in [`McpServersDialog`](file:///home/src/pypost/ui/dialogs/mcp_servers_dialog.py):
       - `_McpServerEditor` dynamic visibility toggling: hiding the Environment dropdown and its form row label when collection source is `"library"`.
       - Automatic collection index defaulting to 0 when switching to library source.
       - Form validation (`_accept_if_complete()`) requiring library collection selection while bypassing environment checks.
       - Generating `McpServerConfiguration` with `environment_id = None` when the environment field is hidden.
       - Table rendering in `McpServersDialog.refresh()` displaying an em-dash (`"—"`) for standalone servers, preventing `TypeError` and clearly communicating standalone status.
     - Updated execution roadmap and child story tracking table, marking COLVAR-2 / PYPOST-1410 as **Completed**.
     - Expanded traceability links to all PYPOST-1410 task artifacts and automated repro tests.

2. **Updated Documentation Index**:
   - [`doc/dev/README.md`](../../doc/dev/README.md)
     - Updated table of contents under "Collections and environments" to reference PYPOST-1410 alongside PYPOST-1407, PYPOST-1408, and PYPOST-1409.
     - Added cross-reference under the "MCP" section linking directly to `doc/dev/collection_scoped_variables.md#standalone-mcp-server-configuration-and-execution-pypost-1410`.
     - Verified all relative markdown links and table of contents numbering integrity across the developer documentation index.

3. **Context & Motivation**:
   - In legacy PyPost versions, MCP servers could only execute if bound to a workspace [`Environment`](file:///home/src/pypost/models/models.py). This forced users of library-based MCP servers (e.g. Jira, GitHub, GitLab) to create phantom workspace environments solely to satisfy schema and validation constraints.
   - PYPOST-1410 builds on the foundation established by PYPOST-1409 (where collections own their variable definitions and presets) to decouple MCP servers from workspace environments.
   - Documenting these architectural changes ensures clarity for developers implementing subsequent stories ([PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) workspace environment variable import, [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) integration test suite) and maintaining MCP server registry supervision.

## Key Topics Documented

1. **Data Model Schema Decoupling**:
   - Schema modification: `environment_id: Optional[str] = None` in [`McpServerConfiguration`](file:///home/src/pypost/models/settings.py).
   - Root validator `validate_server_type_requirements`:
     - Workspace local servers (`collection_id` present): require non-empty `collection_id` and non-empty `environment_id`.
     - Library local servers (`library_id` present): `environment_id` is optional and defaults to `None`.
     - Bundled library servers: `environment_id` is optional and defaults to `None`.
     - Proxy servers: require `upstream_url`; do not require `collection_id` or `environment_id`.

2. **Runtime Resolution Decoupling**:
   - Method signature: `LibraryRuntimeResolver.resolve(selection, environment_id=None, candidate_overlay=None) -> RuntimeInputs`.
   - `RuntimeInputs.environment_id: Optional[str] = None`.
   - Profile resolution hierarchy when `environment_id is None`:
     1. `overlay.active_profile` or candidate overlay preset (if defined).
     2. Clean fallback to collection defaults (`profile_id = None`, `profile = {}`) with debug logging `mcp_library_profile_fallback_to_defaults`.
   - Effective variable resolution via 3-tier precedence in [`LibraryVariableResolver`](file:///home/src/pypost/core/variable_resolver.py).
   - Dynamic secret aggregation into `hidden_keys` (from `collection.variables`, `manifest.variables`, and `overlay.secrets`).
   - Setting `overridable_keys` to an empty set.

3. **Server Registry Reference Reconciliation & Supervision**:
   - Implemented in [`MCPServerRegistry`](file:///home/src/pypost/core/mcp_server_registry.py):
     - `reconcile_references()` validates library connectivity via `library_service.get_connection(configuration.library_id)` and skips environment validation when `configuration.environment_id is None`, logging `mcp_registry_reconcile_standalone_library_server`.
     - Bundled library servers with `environment_id is None` skip environment checks with log `mcp_registry_reconcile_standalone_bundled_server`.
     - Standalone servers are immune to workspace environment pruning or deletion and never transition to `"failed"` due to missing environments.
     - `start()` logs `standalone=True/False` and delegates to `_runtime_inputs()`.
     - `_runtime_inputs()` passes `environment_id` directly to `LibraryRuntimeResolver.resolve()`.
     - `_start_manager()` initializes the MCP server process manager with suppliers for resolved variables, secrets, and overridable keys, logging `mcp_registry_manager_starting`.
     - `_verify_references()` verifies library connection without requiring workspace collections or environments.
     - `refresh_environment()` ignores standalone servers (`environment_id is None`).

4. **UI Behavior in Editor and Dialogs**:
   - Implemented in [`pypost/ui/dialogs/mcp_servers_dialog.py`](file:///home/src/pypost/ui/dialogs/mcp_servers_dialog.py):
     - `_McpServerEditor`:
       - `_on_collection_source_changed()` dynamically toggles visibility of the Environment combobox and its form layout label (`show_env = not (is_local and is_library)`).
       - Auto-selects the first library collection (index 0) if none is selected.
       - `_accept_if_complete()` validates that `_library_collection.currentData()` is selected, bypassing environment selection.
       - `configuration()` saves `environment_id = None` when the environment widget is hidden.
     - `McpServersDialog`:
       - `refresh()` table rendering displays an em-dash (`"—"`) for standalone servers where `environment_id is None`, preventing runtime `TypeError` and presenting clean UI status.

## Traceability

- **Parent Epic**: [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407)
- **Decomposition Task**: [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)
- **Foundation Implementation Task**: [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409)
- **Current Feature Task**: [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410)
- **Downstream Tasks**:
  - [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411): Workspace environment variable import action from collections
  - [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412): Integration test suite, compatibility matrix, and developer documentation
- **Related Artifacts**:
  - Roadmap: [`ai-tasks/PYPOST-1410/00-roadmap.md`](00-roadmap.md)
  - Requirements: [`ai-tasks/PYPOST-1410/10-requirements.md`](10-requirements.md)
  - Architecture: [`ai-tasks/PYPOST-1410/20-architecture.md`](20-architecture.md)
  - Code Cleanup: [`ai-tasks/PYPOST-1410/40-code-cleanup.md`](40-code-cleanup.md)
  - Observability: [`ai-tasks/PYPOST-1410/50-observability.md`](50-observability.md)
  - Technical Debt: [`ai-tasks/PYPOST-1410/60-tech-debt.md`](60-tech-debt.md)
  - Repro & Verification Test: [`tests/test_mcp_standalone_execution_repro.py`](../../tests/test_mcp_standalone_execution_repro.py)
  - Developer Documentation: [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md)
  - Developer Documentation Index: [`doc/dev/README.md`](../../doc/dev/README.md)
