# Collection-Scoped Variables, Standalone MCP Servers, and Workspace Import

## Overview

As part of parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) (*Collection-scoped variables for standalone MCP servers and workspace collection import*) and architectural decomposition [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408), this document details the architectural evolution from hybrid library-level variable management to self-contained collection-scoped variables.

With the completed implementation of [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) (*Eliminate library-level variables and establish collection-scoped variables and catalog manifest*), the collection library system transitions to a clean, catalog-only model where each [`Collection`](file:///home/src/pypost/models/models.py) serves as the authoritative single source of truth for its variable declarations and environment presets.

In the legacy design, collection libraries declared variable schemas and preset profiles at the overall library manifest level (`manifest.variables` and `manifest.presets`). While functional for single-collection repositories, this design introduced significant architectural drawbacks:
1. **Global Variable Pollution**: Unrelated collections within a single library (such as Jira, GitLab, and GitHub MCP servers) pooled their variables into a unified namespace, creating naming conflicts and cognitive overhead.
2. **Forced Workspace Environment for MCP Servers**: Launching an MCP server from a library collection required users to create or bind a workspace [`Environment`](file:///home/src/pypost/models/models.py), generating phantom environments solely to satisfy schema constraints.
3. **Missing Variable Bridge on Collection Copy**: Copying a collection from a connected library into a user workspace provided no mechanism in the environment variables view to import declared variables.
4. **Dual Variable Authority**: Both [`LibraryManifest`](file:///home/src/pypost/models/library_manifest.py) and [`Collection`](file:///home/src/pypost/models/models.py) declared variables and presets, obscuring data provenance.

Under the updated architecture, collection libraries act strictly as lightweight catalogs. Each collection is self-contained, owning its declared variables, types, secrets, descriptions, and presets. MCP servers execute standalone without requiring workspace environments, and the environment variables interface provides a dedicated import workflow for workspace synchronization.

---

## Architecture & Data Models

### Architectural Layers

```mermaid
flowchart TB
    subgraph CatalogLayer["1. Catalog Layer (PYPOST-1409 - COMPLETED)"]
        LM["LibraryManifest (Catalog Only)<br/>id, name, version, collections[]"]
        COL["Collection (Self-Contained)<br/>requests[], variables[], presets{}"]
        LM -->|references| COL
    end

    subgraph ResolutionLayer["2. Resolution Engine (PYPOST-1409 - COMPLETED)"]
        LVR["LibraryVariableResolver<br/>(Collection-First 3-Tier Precedence)"]
        LRR["LibraryRuntimeResolver<br/>(Resolves Standalone MCP Inputs)"]
        LLO["LocalLibraryOverlay<br/>(User secrets & active preset)"]
        COL --> LVR
        LLO --> LVR
        LVR --> LRR
        LLO --> LRR
    end

    subgraph McpLayer["3. MCP Server Subsystem (PYPOST-1410)"]
        MSC["McpServerConfiguration<br/>environment_id: Optional[str] = None"]
        MSD["McpServersDialog<br/>(Collection-specific presets & secrets)"]
        MSK["McpServerController / Runner<br/>(Executes standalone daemon process)"]
        LRR --> MSK
        MSC --> MSK
        MSD --> MSC
    end

    subgraph WorkspaceLayer["4. Workspace Environment Subsystem (PYPOST-1411)"]
        ENV["Environment<br/>variables{}, hidden_keys{}"]
        EVW["EnvironmentVariablesWidget<br/>('Import from Collection' Action)"]
        ICD["ImportCollectionVariablesDialog<br/>(Conflict Resolution: Overwrite / Skip)"]
        COL -.->|import variables| ICD
        ICD -->|merge & apply| EVW
        EVW --> ENV
    end
```

### Core Domain Models

1. **Catalog Manifest ([`LibraryManifest`](file:///home/src/pypost/models/library_manifest.py))**:
   - `LibraryManifest` serves solely as an index of collection file references.
   - `variables` and `presets` fields are deprecated (`deprecated=True`), defaulting to empty structures. Incoming manifests declaring them trigger non-fatal deprecation warnings.
   - Serialization via [`serialize_manifest_to_dict`](file:///home/src/pypost/core/library_manifest.py) automatically strips empty `variables` and `presets` fields so saved catalog manifests remain clean indexes.
   ```python
   class LibraryManifest(BaseModel):
       id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       name: str
       version: str = "1.0.0"
       description: str = ""
       collections: List[str] = Field(default_factory=list)
       # Deprecated fields retained for backward compatibility only
       variables: List[CollectionVariable] = Field(
           default_factory=list,
           deprecated=True,
           description="Deprecated: Use Collection.variables instead.",
       )
       presets: Dict[str, Dict[str, Any]] = Field(
           default_factory=dict,
           deprecated=True,
           description="Deprecated: Use Collection.presets instead.",
       )
   ```

2. **Self-Contained Collection ([`Collection`](file:///home/src/pypost/models/models.py))**:
   - Sole authority for variable declarations, typing, and presets:
     - `variables: List[CollectionVariable]` ([`CollectionVariable`](file:///home/src/pypost/models/collection_variable.py))
     - `presets: Dict[str, Dict[str, Any]]` (mapping preset names to key-value maps)
     - `requests: List[RequestData]`
     - `websockets: List[WebSocketConnection]`
     - `mcp_clients: List[McpClientConnection]`

3. **Standalone Server Configuration ([`McpServerConfiguration`](file:///home/src/pypost/models/settings.py))**:
   - `environment_id` is made optional:
   ```python
   class McpServerConfiguration(BaseModel):
       # ...
       environment_id: Optional[str] = None
       library_id: Optional[str] = None
       manifest_id: Optional[str] = None
       library_collection_path: Optional[str] = None
   ```
   - When `library_id` is set, `environment_id` may be `None`. The server resolves inputs entirely from collection presets and local overlays.

4. **Local Secrets Overlay ([`LocalLibraryOverlay`](file:///home/src/pypost/models/library_manifest.py))**:
   - Stores machine-local active presets, non-versioned secret overrides, and parameter configurations outside version control at `~/.pypost/libraries_data/<library_id>/overlay.json` with `0o600` file permissions via [`LocalOverlayManager`](file:///home/src/pypost/core/local_overlay_manager.py).

---

## Variable Resolution Engine & Precedence (PYPOST-1409)

The resolution engine in [`LibraryVariableResolver`](file:///home/src/pypost/core/variable_resolver.py) implements collection-scoped variable authority and a strict 3-tier precedence hierarchy.

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Client (MCP / Runner / Test)
    participant Resolver as LibraryVariableResolver
    participant Col as Collection (Authoritative)
    participant Manifest as LibraryManifest (Catalog Fallback)
    participant Overlay as LocalLibraryOverlay (Local Machine)

    Caller->>Resolver: resolve(manifest, collection, active_profile, overlay)

    Note over Resolver: Layer 1: Base Defaults
    Resolver->>Col: Read collection.variables (provenance=DEFAULT)
    opt Legacy Manifest Fallback
        Resolver->>Manifest: Read manifest.variables (only keys not in collection)
    end

    Note over Resolver: Layer 2: Preset Profile
    opt Profile Selected (active_profile or overlay.active_profile)
        Resolver->>Col: Read collection.presets[profile] (provenance=PROFILE)
        opt Legacy Manifest Preset Fallback
            Resolver->>Manifest: Read manifest.presets[profile] (only keys not in collection preset)
        end
    end

    Note over Resolver: Layer 3: Local Overlay Overrides & Secrets
    opt Overlay Present
        Resolver->>Overlay: Apply overlay.overrides (provenance=LOCAL_OVERRIDE)
        Resolver->>Overlay: Apply overlay.secrets (provenance=LOCAL_SECRET)
    end

    Note over Resolver: Namespace Isolation & Redaction
    Resolver->>Resolver: Filter sibling collection variables (is_other_collection_var)
    Resolver->>Resolver: Validate types (validate_variable_value) & check required
    Resolver-->>Caller: VariableResolutionResult(variables, provenance, missing_required, errors)
```

### 1. 3-Tier Precedence Hierarchy

Effective variable values are evaluated in order of ascending priority:

1. **Layer 1 (Base Defaults)**:
   - Primary: Default values declared in `collection.variables` (`var.default`).
   - Fallback: Default values in `manifest.variables` are utilized strictly if the key is not declared in `collection.variables`.
   - Provenance: [`VariableProvenance.DEFAULT`](file:///home/src/pypost/models/library_manifest.py).
2. **Layer 2 (Active Preset Profile)**:
   - Evaluated when an active profile is specified (`active_profile` argument or `overlay.active_profile`).
   - Primary: Preset values declared in `collection.presets[profile_name]`.
   - Fallback: Preset values in `manifest.presets[profile_name]` are applied only for keys not declared in the collection preset.
   - Provenance: [`VariableProvenance.PROFILE`](file:///home/src/pypost/models/library_manifest.py).
3. **Layer 3 (Local Overlay - Highest Priority)**:
   - Applied from [`LocalLibraryOverlay`](file:///home/src/pypost/models/library_manifest.py) stored on the local machine.
   - User overrides: `overlay.overrides` applied with provenance [`VariableProvenance.LOCAL_OVERRIDE`](file:///home/src/pypost/models/library_manifest.py).
   - User secrets: `overlay.secrets` applied with provenance [`VariableProvenance.LOCAL_SECRET`](file:///home/src/pypost/models/library_manifest.py).

### 2. Cross-Collection Namespace Isolation

In multi-collection libraries (e.g. bundling Jira, GitHub, and GitLab MCP tools), declaring variables at the catalog root formerly caused cross-collection namespace pollution.

[`LibraryVariableResolver`](file:///home/src/pypost/core/variable_resolver.py) enforces strict cross-collection namespace isolation:
- **Collection Prefix Identification**: Calculates stem prefixes from the target collection's file path, collection name, and ID (`collection_prefixes`).
- **Sibling Prefix Identification**: Computes prefixes belonging to sibling collections declared in `manifest.collections` (`other_collection_prefixes`).
- **Prefix Filtering Contract (`is_other_collection_var`)**:
  - Excludes variables with dot prefixes matching sibling collections (e.g., `github.api_key` is discarded when resolving a Jira collection).
  - Excludes sibling underscore/hyphen prefixed keys (e.g., `github_token` when resolving Jira).
  - Permits un-namespaced variables defined directly in the target collection without forcing awkward manual prefixes.

### 3. Type Validation & Diagnostic Redaction

- Variable values are type-checked against declared schema types (`string`, `integer`, `number`, `boolean`, `array`, `object`) via `validate_variable_value`.
- **Sensitive Redaction**: If a variable is marked `secret=True` on [`CollectionVariable`](file:///home/src/pypost/models/collection_variable.py), its value is masked as `[REDACTED]` in validation error strings and diagnostic logs, preventing credential leaks.
- Under strict mode (`strict_required=True`), unfulfilled required variables without default values are reported in `result.missing_required`.

---

## MCP Runtime Resolution & Secret Masking (PYPOST-1409)

When executing MCP servers from library collections, [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py) prepares runtime inputs and coordinates secret masking:

### 1. Dynamic Profile Resolution without Manifest Mutation

- Prior to PYPOST-1409, `LibraryRuntimeResolver` mutated `manifest.presets` in-place to inject collection profiles.
- Under the updated contract, profiles are resolved dynamically by reading directly from `collection.presets` and `manifest.presets`, preserving catalog immutability.

### 2. Comprehensive Secret Masking

[`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py) aggregates `hidden_keys` from all contributing layers:
- Declared collection secrets: `{var.name for var in collection.variables if var.secret}`
- Legacy manifest secrets: `{var.name for var in manifest.variables if var.secret}`
- Machine-local overlay secrets: `set(overlay.secrets.keys())`
- Attached workspace environment secrets: `set(environment.hidden_keys)` if an environment is bound.

The aggregated `hidden_keys` set is passed into the MCP server runner, guaranteeing that process environment logs and diagnostic exports mask sensitive parameters.

### 3. Graceful Missing Secret Handling on Initialization

During initial MCP server inspection and catalog loading:
- Missing non-secret required variables raise immediate errors:
  ```
  ValueError("profile_invalid: required library variables are missing")
  ```
- Missing secret variables are handled gracefully without raising fatal errors during server registration and inspection. This allows headless initialization routines, test suites, and catalog dialogs to load and inspect MCP servers before a user has configured machine-local secret overrides in [`LocalLibraryOverlay`](file:///home/src/pypost/models/library_manifest.py).

### 4. Observability & Performance Metrics

- **Latency Tracking**: Runtime resolution records duration using `time.monotonic()` and logs `mcp_library_runtime_validation_completed duration_seconds=...`.
- **Prometheus Metrics**: Validation outcomes are tracked via `track_mcp_library_validation(category)`:
  - Recorded with category `"success"` on completion.
  - Recorded with error categories (e.g. `"profile_missing"`, `"profile_invalid"`, `"manifest_invalid"`) upon failures.

---

## Standalone MCP Server Execution Flow

When an MCP server is configured from a library collection, it executes as a standalone process without referencing or modifying workspace environments.

```mermaid
sequenceDiagram
    autonumber
    actor User as Operator / Developer
    participant UI as McpServersDialog
    participant Config as McpServerConfiguration
    participant Resolver as LibraryRuntimeResolver
    participant Col as Collection
    participant Overlay as LocalLibraryOverlay
    participant Runner as McpServerController

    User->>UI: Selects Library Collection
    UI->>UI: Detects Library Collection Source
    Note over UI: Hides Workspace Environment Dropdown<br/>Displays Collection Variables & Presets
    User->>UI: Selects Collection Preset & Enters Secret Overrides
    User->>UI: Clicks "Save / Start"
    UI->>Config: Create McpServerConfiguration(environment_id=None, collection_path=...)
    UI->>Runner: start_server(server_id)
    Runner->>Resolver: resolve(selection, environment_id=None)
    Resolver->>Col: Load Collection(variables, presets)
    Resolver->>Overlay: Load Local Secrets & Active Profile
    Resolver->>Resolver: Merge Collection Defaults + Preset + Overlay Secrets
    Resolver-->>Runner: RuntimeInputs(environment=effective_vars, hidden_keys=secrets)
    Runner->>Runner: Launch MCP Stdio/HTTP Server with Effective Env
    Runner-->>UI: Server Status: RUNNING
```

### Key Execution Highlights

- **Dynamic UI Presentation**: In [`McpServersDialog`](file:///home/src/pypost/ui/dialogs/mcp_servers_dialog.py), the workspace environment combobox is hidden when a library collection is chosen. The dialog displays only variables declared by that specific collection.
- **Direct Variable Resolution**: [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py) merges:
  1. Base default values from `Collection.variables`.
  2. Selected profile values from `Collection.presets[profile_name]`.
  3. Machine-local user overrides and secrets from `LocalLibraryOverlay`.
- **Process Isolation**: The resolved variables are passed to the spawned server process environment. Sensitive values flagged as secrets are automatically masked in logging and diagnostics.

---

## Workspace Environment Variable Import Flow

When a user copies a library collection into their workspace or works with an existing collection, declared variables can be imported directly into a workspace [`Environment`](file:///home/src/pypost/models/models.py).

```mermaid
sequenceDiagram
    autonumber
    actor User as Workspace User
    participant Widget as EnvironmentVariablesWidget
    participant Dialog as ImportCollectionVariablesDialog
    participant Col as Target Collection
    participant Env as Environment

    User->>Widget: Clicks "Import from Collection..."
    Widget->>Dialog: Open Dialog(available_collections, target_environment)
    Dialog->>Col: Read declared variables (name, default, type, secret)
    Dialog->>Dialog: Inspect target Environment variables for collisions
    Note over Dialog: Flags new keys vs. existing keys<br/>User chooses Conflict Policy (Skip / Overwrite)
    User->>Dialog: Confirms Import
    Dialog-->>Widget: ImportResult(imported_vars, hidden_keys)
    Widget->>Env: Update environment.variables & environment.hidden_keys
    Widget->>Widget: Refresh Table Rows & Secret Masks
    Widget-->>User: Visual Confirmation ("N variables imported")
```

### Import Policies and Secret Protection

- **Trigger Location**: A dedicated `Import from Collection...` button is embedded in [`EnvironmentVariablesWidget`](file:///home/src/pypost/ui/widgets/environments/environment_variables_widget.py).
- **Conflict Resolution Strategies**:
  - `Skip`: Preserves existing environment variable values; adds only newly declared collection variables.
  - `Overwrite`: Replaces existing values with collection default values.
- **Automatic Secret Mapping**: Any variable with `secret=True` on [`CollectionVariable`](file:///home/src/pypost/models/collection_variable.py) is automatically added to `Environment.hidden_keys`, guaranteeing masking in UI tables and encryption at rest via the secure storage manager.
- **Pure Domain Helper**: Variable synchronization logic is encapsulated in a pure helper function:
  ```python
  def import_collection_variables_to_environment(
      environment: Environment,
      collection: Collection,
      overwrite: bool = False,
      selected_keys: Optional[Set[str]] = None,
  ) -> ImportSummary:
      ...
  ```

---

## Backward Compatibility & Migration Strategy

To ensure seamless operation across existing repositories and saved state, the system adheres to strict compatibility rules:

1. **Legacy Manifest Ingestion**:
   - Manifests containing root `variables` or `presets` are accepted without error.
   - Non-fatal structured warning logs (`legacy_manifest_variables_detected`, `legacy_manifest_presets_detected`) and `DeprecationWarning` exceptions are emitted.
   - Deserialization continues to succeed, and resolvers use collection-scoped variables primarily, falling back to legacy manifest variables only if undefined in the collection.
2. **Catalog Serialization Cleanliness**:
   - Serializing a `LibraryManifest` with empty `variables` or `presets` strips those fields from the output dictionary, generating clean catalog files.
3. **Existing Workspace Environments**:
   - Workspace collections that explicitly link to workspace environments continue to operate without regression.
   - Standalone execution is opt-in for library collections where `environment_id is None`.
4. **Data Integrity**:
   - Adding collection-scoped variables or importing them into environments does not alter existing request definitions, authentication headers, or script bindings.

---

## Child Task Execution Sequence

Epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) is partitioned into four focused child stories under Sprint 2033:

```mermaid
flowchart TD
    COLVAR1["[x] PYPOST-1409 (COLVAR-1, 3 SP)<br/>Eliminate library variables & establish catalog manifest"]
    COLVAR2["[ ] PYPOST-1410 (COLVAR-2, 5 SP)<br/>Standalone MCP server without workspace environment"]
    COLVAR3["[ ] PYPOST-1411 (COLVAR-3, 3 SP)<br/>Workspace environment variable import action"]
    COLVAR4["[ ] PYPOST-1412 (COLVAR-4, 3 SP)<br/>Integration test suite, compatibility matrix & dev docs"]

    COLVAR1 --> COLVAR2
    COLVAR1 --> COLVAR3
    COLVAR2 --> COLVAR4
    COLVAR3 --> COLVAR4
```

| Jira Key | Identifier | SP | Status | Focus Area | Downstream Deliverables |
| --- | --- | :---: | :---: | --- | --- |
| [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) | `COLVAR-1` | 3 | **Completed** | Catalog manifest & collection authority | Deprecate manifest variables; update `LibraryManifest`, `LibraryVariableResolver`, and `LibraryRuntimeResolver`. |
| [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) | `COLVAR-2` | 5 | In Progress | Standalone MCP server execution | Optional `environment_id` in `McpServerConfiguration`; dialog UI refactor; standalone runtime launch. |
| [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) | `COLVAR-3` | 3 | Ready | Workspace variable import action | `EnvironmentVariablesWidget` import trigger; selection dialog; conflict resolution; secret masking. |
| [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) | `COLVAR-4` | 3 | To Do | Integration tests & documentation | End-to-end test suite; legacy manifest compatibility matrix; user guide documentation updates. |

### Phased Roadmap

1. **Phase 1 (Foundation - COMPLETED)**: Executed [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) to establish the catalog-only manifest model, deprecate library-level variables, and anchor 3-tier variable resolution within collections.
2. **Phase 2 (Parallel Feature Tracks)**:
   - Execute [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) for standalone MCP server execution without requiring workspace environments.
   - Execute [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) for the environment variable import UI and core helper.
3. **Phase 3 (Consolidation & Verification)**: Execute [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) to validate end-to-end integration contracts across all components and update user-facing documentation.

---

## Traceability & References

- **Parent Epic**: [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407)
- **Decomposition Task**: [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)
- **Foundation Implementation Task**: [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409)
- **Architecture Specification**: [`ai-tasks/PYPOST-1409/20-architecture.md`](file:///home/src/ai-tasks/PYPOST-1409/20-architecture.md)
- **Observability Report**: [`ai-tasks/PYPOST-1409/50-observability.md`](file:///home/src/ai-tasks/PYPOST-1409/50-observability.md)
- **Technical Debt Report**: [`ai-tasks/PYPOST-1409/60-tech-debt.md`](file:///home/src/ai-tasks/PYPOST-1409/60-tech-debt.md)
- **Automated Repro & Regression Tests**: [`tests/test_collection_scoped_variables_repro.py`](file:///home/src/tests/test_collection_scoped_variables_repro.py)
- **Related Developer Guides**:
  - [Library Manifest and Local Secrets Overlay Manager](library_manifest_and_overlay.md)
  - [Collection Format v2](collection_format_v2.md)
  - [Collection Variable Setup Guidance](collection_variable_guidance.md)
  - [Environment Management and Variable Display](environments.md)
