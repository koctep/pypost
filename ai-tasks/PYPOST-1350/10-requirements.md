# PYPOST-1350: Built-in collection view over the examples library

## Goals

PyPost needs to provide users with curated, ready-to-use "Built-in" MCP collections (specifically Jira, GitLab, and GitHub integrations) without duplicating files or inventing disconnected catalog formats. Built-in collections must be established as a clean, read-only view directly over the shipped examples library (`pypost-examples`), pairing each built-in collection with its corresponding template environment.

Furthermore, to guarantee that shipped resources remain trustworthy starting points for users, the structural consistency of each paired environment against the collection's manifest declarations must be continuously verified by automated tests without clobbering pinned test data or runtime values.

## User Stories

- As an MCP server author, I want PyPost to define a clear, curated catalog of Built-in collections (Jira, GitLab, GitHub) so that I can easily discover standard integrations shipped out-of-the-box.
- As an MCP server author, I want each Built-in collection to have an associated paired template environment so that I have the required variable declarations and secret placeholders ready for server configuration.
- As a user or developer, I want the Built-in collection view to always load freshly from the shipped examples library so that application updates and improvements to shipped collections are immediately visible.
- As a system administrator or developer, I want malformed, missing, or corrupted view definitions to be handled gracefully with clear diagnostics rather than crashing the application or MCP subsystem.
- As a maintainer, I want automated structural consistency tests ensuring that paired environments never drift from their manifest declarations (variables, secrets, overridable keys) while preserving committed placeholder values and live test fixtures.

## Definition of Done

1. A declarative definition of built-in collections (`examples/builtin-collections.yaml`) is established, specifying exactly the three curated integrations:
   - Jira Cloud MCP (`collections/jira_mcp.json` paired with `environments/jira_cloud.json`)
   - GitLab MCP (`collections/gitlab_mcp.json` paired with `environments/gitlab.json`)
   - GitHub MCP (`collections/github_mcp.json` paired with `environments/github.json`)
2. A domain view service (`BuiltinCollectionView`) provides read-only access over the shipped library via the predefined library service:
   - `list_entries()` returns exactly the three curated entries, reading display name, collection id, and version directly from the underlying collection JSON assets.
   - Each entry exposes its library identity (`library_id = manifest_id = "pypost-examples"`, `library_collection_path`).
   - `load_collection()` and `load_paired_environment()` reliably load and parse the respective collection and environment models on demand (performing fresh reads on every call).
   - Identifies whether a given server configuration corresponds to a built-in collection (`is_builtin(...)`).
3. Robust error handling and diagnostics:
   - Entries referencing non-manifest-declared collections, missing files, or unreadable JSON produce clear diagnostic records.
   - An invalid or missing view file yields an empty entry list with appropriate diagnostics, without raising unhandled exceptions.
4. Paired-environment structural consistency testing:
   - Automated tests verify that each paired environment's variable keys match the manifest variables declared for that collection.
   - Secret variables declared in the manifest are marked in `hidden_keys`, and secret values in the committed environment files are non-empty committed placeholders.
   - Keys declared in `mcp_overridable_keys` are a strict subset of the environment's variable keys.
   - Structural checks do not compare actual variable values with presets or manifest defaults.
5. Shipped environment files (`examples/environments/*.json`) and existing tests (`tests/test_example_fixtures.py`, `tests/test_jira_mcp_live_smoke.py`) remain untouched and continue to pass.
6. Repository quality gate passes (`make check`).

## Task Description

This Story represents Child C2 of epic PYPOST-1335 ("Built-in collections source for MCP server creation"). It builds directly on the packaging (PYPOST-1348, C1a) and locator (PYPOST-1349, C1b) infrastructure to establish the domain view layer and definition file that identifies which shipped example collections are "Built-in".

The implementation language is Python. Architectural decisions are established in `ai-tasks/PYPOST-1336/20-architecture.md` (decisions c, d, e; gap 5) and task specifications in `ai-tasks/PYPOST-1335/decomposition.md`.

### Scope

- Declarative view specification in `examples/builtin-collections.yaml` for Jira Cloud MCP, GitLab MCP, and GitHub MCP, pairing each with its corresponding environment JSON file.
- Domain models and view service in `pypost/core/builtin_collections.py`:
  - `BuiltinCollectionEntry`: data container holding collection path, environment path, display name, collection id, and version, with identity selection helper `selection()`.
  - `BuiltinCollectionView`: domain view querying the `PredefinedLibraryService`, providing listing, loading, identity matching, and error diagnostics.
- Automated structural consistency tests under `tests/` verifying paired environments against manifest variables and secret rules.

### Constraints and Exclusions

- `mcp.json` (`test-collection-mcp`) is intentionally excluded from the built-in view; it is a test fixture without a paired environment and remains part of the general examples library only.
- Persistence model changes (`bundled_library` field on `McpServerConfiguration`) and runtime registry startup belong to PYPOST-1351 (C3a).
- Registry lifecycle (`reconcile_references`, `refresh_environment`) and controller save logic belong to PYPOST-1352 (C3b).
- UI dialog presentation and source switching belong to PYPOST-1353 (C4).
- Shipped environment values and existing test fixtures are not altered.
- All repository commands and testing must be executed exclusively via `make` targets.

### Main Entities

| Entity | Business Role |
| --- | --- |
| Built-in Collection View (`BuiltinCollectionView`) | Domain service presenting a curated, read-only view of standard integrations over the shipped examples library |
| Built-in Collection Entry (`BuiltinCollectionEntry`) | Descriptor representing a specific curated integration, its display metadata, library identity, and paired environment |
| Paired Environment | Shipped template environment file associated with a built-in collection, defining the necessary keys, secret indicators, and overridable flags |
| Shipped Examples Library (`PredefinedLibraryService`) | The authoritative underlying library of bundled collections and manifests shipped with PyPost |

### User Scenarios

1. **Listing Available Built-in Integrations**: The MCP configuration subsystem requests the list of built-in collections. The view service reads `examples/builtin-collections.yaml`, verifies each against the predefined library, and returns entries for Jira, GitLab, and GitHub with current versions and names.
2. **Accessing Built-in Assets**: A subsystem needs to inspect a built-in collection or its paired template environment. The view service loads and parses the requested asset freshly from disk without caching stale content.
3. **Handling Missing or Corrupt View Definition**: If the built-in configuration YAML is missing, corrupted, or references a collection not declared in the library manifest, the view service records a diagnostic message and returns an empty entry list rather than failing catastrophically.
4. **Verifying Paired Environment Integrity**: During test suite execution, the consistency test suite validates that each paired environment file has keys matching the manifest, marks secrets as hidden, and uses placeholder values, catching any configuration drift before release.

## Q&A

- **Why is Built-in implemented as a view over the examples library rather than a separate catalog or directory?**
  Reusing the examples library as the underlying store avoids duplicating collection files, ensures a single source of truth across the repository and package, and leverages existing library manifest loading, validation, and auto-update mechanisms.
- **Why are exactly three collections included (Jira, GitLab, GitHub) while `mcp.json` is excluded?**
  Per epic PYPOST-1335 decisions, Built-in collections are user-facing, production-ready curated integrations. `mcp.json` is a synthetic integration test fixture without a paired environment or user-facing documentation, so it belongs only to the general developer library.
- **Why does the consistency test check structure rather than comparing values with presets or defaults?**
  Environment files serve as user templates and intentionally carry realistic placeholder configurations (e.g., Jira Cloud environment URL placeholders differ from internal preset keys). Comparing values would break valid template designs and fail pinned fixture tests (`tests/test_example_fixtures.py` and live smoke tests).
- **Does this step include UI controls or server saving logic?**
  No. This step focuses purely on the domain view layer, view configuration, and consistency validation. Persistence models, registry lifecycle, and UI dialogs are owned by subsequent child tasks (PYPOST-1351, PYPOST-1352, PYPOST-1353).
