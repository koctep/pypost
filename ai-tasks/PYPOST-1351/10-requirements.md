# PYPOST-1351: Built-in identity in MCP server configuration and startup

## Goals

A persisted MCP server configuration in PyPost must be able to reference a built-in collection by
stable identity, guaranteeing that the MCP server always serves the version of the collection
shipped with the currently running PyPost installation (auto-update upon application upgrade). At
the same time, existing persisted server configurations (workspace servers and ordinary library
servers) must remain completely untouched and function with backward compatibility.

To achieve this, the configuration model needs a clear marker for built-in library identity, and
the MCP server runtime registry must resolve built-in server instances directly from the shipped
bundled library adapter. This ensures that built-in servers are never shadowed by user-connected
libraries sharing the same identifier, do not inherit arbitrary library presets or overlays that
could clobber user configuration, and start seamlessly both in interactive GUI sessions and in
headless daemon mode.

## User Stories

- As an MCP server administrator or user, I want my configured Built-in MCP server to always serve
  the latest tools and resources shipped with PyPost, so that upgrading the application updates the
  server's exposed capabilities automatically without manual reconfiguration.
- As an MCP server user, I want my Built-in server's environment variables to be sourced exclusively
  from my selected workspace environment and manifest defaults, so that external presets or
  overlays from user libraries cannot inadvertently override my configured credentials or settings.
- As an MCP server user, I want the system to reject invalid built-in configurations (such as an
  invalid library identifier or an unrecognized collection path) with clear error diagnostics
  ("missing built-in collection"), so that misconfigurations are quickly diagnosed.
- As a headless PyPost user or daemon runner, I want enabled Built-in MCP servers to start reliably
  under DaemonRuntime without requiring an external library manager service, so that background
  services operate robustly.
- As an existing PyPost user, I want all my pre-existing workspace and library MCP server
  configurations to continue loading and running unchanged, preserving existing workflows without
  any forced migration.

## Definition of Done

1. **Configuration Model Extension and Validation**:
   - `McpServerConfiguration` includes a `bundled_library: bool = False` attribute.
   - Model validation preserves existing precedence:
     - Proxy server validation remains unchanged (`server_type == "proxy"`).
     - Local server with `library_id`: `manifest_id` and `library_collection_path` are required;
       `collection_id` (if present) is ignored. If `bundled_library` is `True`, `library_id` must
       equal `"pypost-examples"`.
     - Local server without `library_id`: `collection_id` is required; `bundled_library: True`
       without `library_id` is strictly rejected.
   - Configurations without `bundled_library` default to `False`.

2. **Registry Bundled Adapter and Startup Resolution**:
   - `MCPServerRegistry` initializes an internal bundled adapter by default, making built-in
     collection resolution available regardless of whether an external `library_service` is
     injected.
   - For rows marked with `bundled_library = True`:
     - Resolution fetches the connection record directly from the shipped bundled library,
       preventing any stored user connection with id `"pypost-examples"` from shadowing it.
     - Runtime inputs resolution runs with an empty overlay and applies no preset, ensuring
       variables come strictly from the selected workspace environment and manifest defaults.
     - Membership check against the built-in collection view: a collection path that is not an
       entry of `builtin-collections.yaml` (e.g., `collections/mcp.json`) is allowed to load into
       settings, but is never started.
     - When reference resolution fails for a built-in server or its path is not an entry in the
       built-in view, the missing reference diagnostic states `"missing built-in collection"`.

3. **Runtime Compatibility Across Construction Points**:
   - An enabled Built-in row starts successfully under `DaemonRuntime` (where `MCPServerRegistry`
     is created without `library_service`) without triggering `mcp_failed`.
   - A registry injected into `McpServerSettingsController` serves Built-in rows with identical
     behavior.
   - Existing caller construction points require no custom wiring changes.

4. **Regression Protection and Upgrade Behavior**:
   - Legacy rows (workspace rows, ordinary library rows, and library rows carrying a stale
     `collection_id`) validate, load, and start as before.
   - Updating the shipped bundle files (simulated upgrade) updates the tools exposed on the next
     server start without modifying stored settings.
   - A connected library with identifier `"pypost-examples"`, an active preset, or a
     `pypost-examples` overlay does not affect the served collection or variable values of a
     Built-in row.

5. **Quality Gate**:
   - `make check` passes, including scoped tests and static analysis.

## Task Description

This task (PYPOST-1351, Child C3a of epic PYPOST-1335) implements the configuration identity and
startup runtime logic for Built-in MCP servers.

The implementation language is Python. The task operationalizes Decision (e) and the Validator
Rule specified in `ai-tasks/PYPOST-1336/20-architecture.md` and detailed in
`ai-tasks/PYPOST-1335/decomposition.md`.

### Scope In

- `pypost/models/settings.py`:
  - Add `bundled_library: bool = False` to `McpServerConfiguration`.
  - Update `validate_server_type_requirements`:
    - When `library_id` is set: enforce `manifest_id` and `library_collection_path`; ignore
      `collection_id`; if `bundled_library` is `True`, enforce `library_id == "pypost-examples"`.
    - When `library_id` is not set: enforce non-empty `collection_id`; reject
      `bundled_library == True`.
- `pypost/core/mcp_server_registry.py`:
  - In `MCPServerRegistry.__init__`, build a bundled adapter by default using
    `PredefinedLibraryService` and `BuiltinCollectionView`, independent of any injected
    `library_service`.
  - In `_runtime_inputs`:
    - For `bundled_library = True` rows, resolve connection `"pypost-examples"` via the bundled
      adapter (never via stored connections).
    - Validate that the collection path is an active entry in the built-in view; non-entries load
      into configuration but fail start.
    - Run `LibraryRuntimeResolver.resolve` with an empty overlay and no preset.
  - In `_missing_reference`, report `"missing built-in collection"` when a `bundled_library` row
    fails reference resolution.
- Verify construction points (`McpServerSettingsController.__init__` in
  `pypost/ui/mcp_server_controller.py` and `DaemonRuntime` in `pypost/core/qt/daemon_runtime.py`)
  with targeted tests ensuring no modifications to these entry points are needed.

### Scope Out

- Registry lifecycle operations (`reconcile_references`, `_validate_replacement_references`,
  `refresh_environment`) and UI controller save transactions (deferred to PYPOST-1352 / C3b).
- MCP Servers dialog UI changes, read-only badges, and source switching (deferred to PYPOST-1353 /
  C4).
- Copying built-in collections or paired environments (deferred to PYPOST-1354 / C5 and
  PYPOST-1355 / C6).
- End-to-end user documentation and cross-cutting workflow tests (deferred to PYPOST-1356 / C7).
- Migration of existing persisted configurations.

### Main Entities

- `McpServerConfiguration`: Persisted configuration record for an MCP server endpoint, carrying
  the `bundled_library` flag.
- `MCPServerRegistry`: Central lifecycle registry managing active MCP server processes, resolving
  runtime inputs at start.
- `BuiltinCollectionView`: Curated domain view defining active built-in collection entries from
  shipped package data.
- `PredefinedLibraryService`: Authoritative provider for the shipped examples library
  (`pypost-examples`).
- `LibraryRuntimeResolver`: Domain resolver converting library identity and workspace environment
  into server runtime inputs.

### Business Acceptance Criteria

1. **Built-in Server Startup**: A server configured with `bundled_library=True` successfully starts
   and exposes the tools defined in the shipped collection.
2. **Auto-update on Application Upgrade**: Modifying or upgrading the shipped collection content
   causes the server to expose the updated tools on its subsequent start without modifying
   persisted server settings.
3. **Isolation from Library Overlays and Presets**: The existence of a user-connected library
   named `"pypost-examples"`, a library preset, or a stored library overlay has zero impact on the
   collection served or the environment variable values resolved for a Built-in server.
4. **View Membership Enforcement**: A `bundled_library=True` row referencing an unknown path or a
   manifest-declared path outside `builtin-collections.yaml` (e.g. `collections/mcp.json`) can be
   loaded in settings, but fails to start, reporting `"missing built-in collection"`.
5. **Backward Compatibility for Legacy Rows**: Workspace servers, normal library servers, and
   legacy library rows carrying both `library_id` and a stale `collection_id` validate, load, and
   start exactly as before. Existing persisted files without `bundled_library` load as `False`.
6. **Model Validation Constraints**: Setting `bundled_library=True` with any `library_id` other
   than `"pypost-examples"` or without `library_id` raises a model validation error.
7. **Daemon and Controller Construction Points**: An enabled Built-in server row starts correctly
   under `DaemonRuntime` without raising `mcp_failed`, and functions under
   `McpServerSettingsController` with an injected registry.
8. **Automated Verification**: `make check` passes completely.

## Q&A

- **Why is `bundled_library` represented as a boolean on `McpServerConfiguration` instead of
  a new `server_type`?**
  In PyPost, `server_type` differentiates between `"local"` (locally hosted Python MCP server) and
  `"proxy"` (HTTP/SSE upstream proxy). Built-in servers are local servers that reuse the library
  identity model (`library_id`, `manifest_id`, `library_collection_path`). Introducing a new
  server type would fragment existing local server process management, whereas an additive boolean
  flag cleanly preserves existing structure while distinguishing built-in identity.
- **Why must `bundled_library` strictly require `library_id == "pypost-examples"`?**
  Built-in collections are exclusively supplied by the shipped examples library. Enforcing this in
  the model validator guarantees that user configurations cannot attempt to treat arbitrary
  third-party libraries as bundled, preventing security and isolation issues.
- **Why are non-entry collections like `collections/mcp.json` prevented from starting?**
  `collections/mcp.json` is a synthetic test fixture in the examples library without a paired
  environment or user-facing curated status. Only collections explicitly listed in
  `examples/builtin-collections.yaml` are part of the Built-in view.
- **Why does startup not use the generic `library_service` injected into the registry?**
  If a user clones or connects a custom library with manifest id `"pypost-examples"`, the generic
  `library_service` would shadow the built-in library. Built-in servers must strictly resolve
  against the shipped package library adapter to ensure integrity and consistency.
