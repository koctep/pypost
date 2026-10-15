# PYPOST-1409: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) (Foundation / COLVAR-1: Eliminate library-level variables and establish collection-scoped variables and catalog manifest under parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) and architectural decomposition [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)).

## Documentation Updates

1. **Updated Developer Guide**:
   - [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md)
     - Documented the completed foundation implementation for [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409).
     - Expanded catalog manifest schema, deprecation contracts, and serialization cleanliness rules.
     - Documented the 3-tier variable resolution engine and provenance hierarchy in [`LibraryVariableResolver`](file:///home/src/pypost/core/variable_resolver.py).
     - Detailed cross-collection namespace isolation mechanics using dynamic collection stem prefix filtering.
     - Documented runtime resolution, secret masking, graceful secret initialization handling, and Prometheus observability metrics in [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py).
     - Updated execution roadmap and status matrix to reflect PYPOST-1409 completion.

2. **Updated Documentation Index**:
   - [`doc/dev/README.md`](../../doc/dev/README.md)
     - Updated table of contents under "Collections and environments" to reference PYPOST-1409 alongside PYPOST-1407 and PYPOST-1408.
     - Verified all relative markdown links and section anchor integrity across the developer documentation index.

3. **Context & Motivation**:
   - In the initial collection library implementation (PYPOST-1221), variables and presets were declared at both the library manifest level and individual collection levels.
   - This design caused global variable pollution in multi-collection libraries (e.g. Jira, GitHub, GitLab sharing a single namespace), forced users to configure workspace environments for MCP servers, and created inverted precedence where catalog manifests eclipsed collection defaults.
   - Story [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) resolves these architectural defects by establishing [`LibraryManifest`](file:///home/src/pypost/models/library_manifest.py) strictly as a lightweight catalog index, elevating [`Collection`](file:///home/src/pypost/models/models.py) as the single source of truth for variables and presets, and establishing a 3-tier precedence hierarchy.
   - Updating `doc/dev/collection_scoped_variables.md` provides future maintainers and developers of child stories ([PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) standalone MCP servers, [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) workspace environment variable import, [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) integration test suite) with exact contracts and precedence specifications.

## Key Topics Documented

1. **Catalog Manifest Deprecation & Serialization**:
   - Deprecated `variables` and `presets` fields on [`LibraryManifest`](file:///home/src/pypost/models/library_manifest.py) using Pydantic `deprecated=True`.
   - Manifest ingestion in [`deserialize_manifest_from_dict`](file:///home/src/pypost/core/library_manifest.py): emits non-fatal structured logs (`legacy_manifest_variables_detected`, `legacy_manifest_presets_detected`) and standard `DeprecationWarning` exceptions while continuing validation.
   - Manifest serialization in [`serialize_manifest_to_dict`](file:///home/src/pypost/core/library_manifest.py): automatically omits empty `variables` and `presets` entries, ensuring emitted YAML and JSON files represent pure catalog indexes.

2. **Collection-Scoped Variable Authority**:
   - [`Collection`](file:///home/src/pypost/models/models.py) owns `variables: List[CollectionVariable]` and `presets: Dict[str, Dict[str, Any]]` as the authoritative source of truth.
   - Decouples collection configuration from parent library repositories, enabling self-contained sharing, export, and standalone MCP tool suite execution.

3. **3-Tier Resolution Engine & Precedence**:
   - Implemented in [`LibraryVariableResolver`](file:///home/src/pypost/core/variable_resolver.py):
     - **Layer 1 (Base Defaults)**: `collection.variables` authoritative; fallback to legacy `manifest.variables` only for keys undefined in the collection. Provenance: `VariableProvenance.DEFAULT`.
     - **Layer 2 (Active Preset Profile)**: `collection.presets[profile]` authoritative; fallback to legacy `manifest.presets[profile]`. Provenance: `VariableProvenance.PROFILE`.
     - **Layer 3 (Local Overlay - Highest Priority)**: `overlay.overrides` (provenance: `VariableProvenance.LOCAL_OVERRIDE`) and `overlay.secrets` (provenance: `VariableProvenance.LOCAL_SECRET`) from [`LocalLibraryOverlay`](file:///home/src/pypost/models/library_manifest.py).
   - Provenance tracking with [`VariableProvenance`](file:///home/src/pypost/models/library_manifest.py).
   - Type validation against schema definitions (`string`, `integer`, `number`, `boolean`, `array`, `object`) with automatic redaction of secret values (`[REDACTED]`) in error strings and logs.

4. **Cross-Collection Namespace Isolation**:
   - Prevents variables belonging to sibling collections within a shared library catalog from polluting the active collection's resolved variable dictionary.
   - Dynamic stem prefix identification (`collection_prefixes` vs `other_collection_prefixes`) and filtering via `is_other_collection_var(key)`.
   - Eliminates the need for awkward dot-notation prefix workarounds in self-contained collection definitions.

5. **MCP Runtime Resolution & Secret Masking**:
   - Implemented in [`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py):
     - Dynamic profile resolution merging `collection.presets` and `manifest.presets` without in-place mutation of catalog manifests.
     - Aggregation of `hidden_keys` across collection variables (`secret=True`), manifest variables (`secret=True`), local overlay secrets, and bound environment hidden keys.
     - Graceful handling of missing secret variables during MCP server initialization: non-secret missing required variables raise validation errors, whereas unconfigured secrets are tolerated during server registration and catalog inspection until local overlay overrides are supplied.
     - Structured audit logging (`mcp_library_secret_masking_applied`, `mcp_library_runtime_validation_completed`), latency duration tracking, and Prometheus validation category counters via `MetricsTrackerProtocol.track_mcp_library_validation()`.

## Traceability

- **Parent Epic**: [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407)
- **Decomposition Task**: [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)
- **Foundation Implementation Task**: [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409)
- **Downstream Feature Tasks**:
  - [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410): Standalone MCP server configuration and execution without workspace environment
  - [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411): Workspace environment variable import action from collections
  - [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412): Integration test suite, compatibility matrix, and developer documentation
- **Related Artifacts**:
  - Requirements: [`ai-tasks/PYPOST-1409/10-requirements.md`](10-requirements.md)
  - Architecture: [`ai-tasks/PYPOST-1409/20-architecture.md`](20-architecture.md)
  - Code Cleanup: [`ai-tasks/PYPOST-1409/40-code-cleanup.md`](40-code-cleanup.md)
  - Observability: [`ai-tasks/PYPOST-1409/50-observability.md`](50-observability.md)
  - Technical Debt: [`ai-tasks/PYPOST-1409/60-tech-debt.md`](60-tech-debt.md)
  - Developer Documentation: [`doc/dev/collection_scoped_variables.md`](../../doc/dev/collection_scoped_variables.md)
