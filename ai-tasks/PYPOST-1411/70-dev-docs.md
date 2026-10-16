# PYPOST-1411: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) (Feature / COLVAR-3: Workspace environment variable import action from collections under parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) and architectural decomposition [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)).

## Documentation Updates

1. **New Developer Guide**:
   - [`doc/dev/workspace_environment_variable_import.md`](../../doc/dev/workspace_environment_variable_import.md)
     - Complete documentation of the workspace collection variable import feature.
     - Architecture, component interaction diagram (Mermaid), and domain-UI separation.
     - Pure domain engine specification in `pypost/core/collection_variable_import.py`:
       - `import_collection_variables_to_environment(environment, collection, conflict_strategy, selected_keys, preset_name)`
       - `ConflictStrategy`: `SKIP` (non-destructive, default) vs. `OVERWRITE`
       - `ImportSummary`: Granular mutation tracking (`added_keys`, `updated_keys`, `skipped_keys`, `invalid_keys`, `newly_hidden_keys`, `total_imported`, `format_summary()`).
       - `format_variable_value(value)`: Value normalization rules across booleans, numbers, strings, and JSON objects/lists.
     - Presets evaluation rules: Dynamic lookup of preset profile overrides from `collection.presets` with fallback to `var.default`.
     - Variable name validation guardrails: Jinja2-compatible identifier rules via `validate_variable_name()`, isolation of invalid keys without aborting valid keys.
     - Secret protection policies: Automatic detection of `var.secret`, registration in `Environment.hidden_keys`, exclusion from `Environment.mcp_overridable_keys`, UI table masking with `HIDDEN_MASK`, and encryption at rest.
     - UI integration details:
       - `EnvironmentVariablesWidget` button `COLLECTION_VARIABLE_IMPORT_BUTTON` ("Import from Collection…") and lifecycle enablement.
       - `ImportCollectionVariablesDialog` source discovery (workspace collections and connected libraries via `LibraryManagerService`), preset selector, preview table, batch select controls, conflict radios, and execution flow.
     - Structured logging and observability contract (event names, severity levels, parameters, secret safety).
     - Troubleshooting, FAQ, and automated test suite coverage reference.

2. **Updated Developer Guide**:
   - [`doc/dev/environments_dialog.md`](../../doc/dev/environments_dialog.md)
     - Added dedicated section `## Import collection variables (PYPOST-1411)`.
     - Documented `EnvironmentVariablesWidget` additions: `COLLECTION_VARIABLE_IMPORT_BUTTON`, MCP override column, and integration with `ImportCollectionVariablesDialog`.
     - Linked to `doc/dev/workspace_environment_variable_import.md`.

3. **Updated Developer Guide**:
   - [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md)
     - Updated child task sequence flowchart, marking `COLVAR-3 / PYPOST-1411` as `[x]`.
     - Updated tracking table marking `PYPOST-1411` as **Completed** with references to `workspace_environment_variable_import.md`.
     - Added PYPOST-1411 task artifact links under `Traceability & References`.

4. **Updated Documentation Index**:
   - [`doc/dev/README.md`](../../doc/dev/README.md)
     - Added entry `[Workspace Environment Variable Import from Collections (PYPOST-1411)](workspace_environment_variable_import.md)` under "Collections and environments".

## Validation

- Verified documentation integrity and formatting:
  - `make lint` passes with all markdown and relative link checks green.
  - `make verify-ai-tasks` passes baseline verification.
