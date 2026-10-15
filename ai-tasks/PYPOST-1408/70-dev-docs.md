# PYPOST-1408: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408) (*Decompose epic PYPOST-1407 into child tasks* under parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407)).

## Documentation Updates

1. **Created Documentation**:
   - [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md): Comprehensive developer guide detailing the architecture, data models, standalone MCP server execution flow, workspace environment variable import flow, backward compatibility guarantees, and child task execution sequence for epic PYPOST-1407.

2. **Updated Documentation**:
   - [`doc/dev/README.md`](../../doc/dev/README.md): Registered `collection_scoped_variables.md` under the "Collections and environments" table of contents section.
   - [`ai-tasks/PYPOST-1408/00-roadmap.md`](00-roadmap.md): Updated Step 8 status to `[/]` and recorded documentation deliverables.

3. **Maintainer Overview**:
   - **Architectural Shift**: Decouples `LibraryManifest` from variable storage, transitioning collection libraries to lightweight catalogs. Variables and preset profiles are consolidated exclusively within `Collection` aggregates (`variables: List[CollectionVariable]`, `presets: Dict[str, Dict[str, Any]]`).
   - **Standalone MCP Server Runtime**: Updates `McpServerConfiguration.environment_id` to be optional (`Optional[str] = None`). MCP servers backed by library collections execute using collection defaults, selected presets, and machine-local `LocalLibraryOverlay` secrets without requiring phantom workspace environments.
   - **Workspace Variable Synchronization**: Adds an "Import from Collection..." trigger to `EnvironmentVariablesWidget` with conflict resolution strategies (`Skip` vs. `Overwrite`) and automatic secret masking (`CollectionVariable.secret -> Environment.hidden_keys`).
   - **Implementation Stories & Sizing**:
     - [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) (`COLVAR-1`, 3 SP): Eliminate library-level variables, establish catalog manifest and collection-scoped authority.
     - [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) (`COLVAR-2`, 5 SP): Standalone MCP server configuration and execution without workspace environment.
     - [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) (`COLVAR-3`, 3 SP): Workspace environment variable import action from collections.
     - [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) (`COLVAR-4`, 3 SP): Integration test suite, compatibility matrix, and developer documentation.
     - All 4 stories belong to **Sprint 2033** (Total: 14 Story Points, each $\le 5$ SP).

4. **Backward Compatibility Strategy**:
   - Legacy library manifests declaring top-level `variables` or `presets` will be parsed gracefully with deprecation warnings.
   - Core resolvers will consult legacy manifest variables only as an optional fallback when undefined in collection models.
   - Existing workspace collections and environments remain 100% functional without breaking changes.

5. **Traceability Links**:
   - **Parent Epic**: [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407)
   - **Planning Task**: [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)
   - **Child Stories**:
     - [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) (COLVAR-1, 3 SP)
     - [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) (COLVAR-2, 5 SP)
     - [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) (COLVAR-3, 3 SP)
     - [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) (COLVAR-4, 3 SP)
   - **Workflow Artifacts**:
     - Roadmap: [`ai-tasks/PYPOST-1408/00-roadmap.md`](00-roadmap.md)
     - Requirements: [`ai-tasks/PYPOST-1408/10-requirements.md`](10-requirements.md)
     - Architecture: [`ai-tasks/PYPOST-1408/20-architecture.md`](20-architecture.md)
     - Code Cleanup: [`ai-tasks/PYPOST-1408/40-code-cleanup.md`](40-code-cleanup.md)
     - Observability: [`ai-tasks/PYPOST-1408/50-observability.md`](50-observability.md)
     - Technical Debt: [`ai-tasks/PYPOST-1408/60-tech-debt.md`](60-tech-debt.md)
     - Decomposition Notes: [`ai-tasks/PYPOST-1407/decomposition-notes.md`](../PYPOST-1407/decomposition-notes.md)
