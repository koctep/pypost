# PYPOST-1221: [Libraries] Library manifest schema validator and local secrets overlay manager

## Goals

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost is introducing version-controlled collection libraries that teams can share via Git repositories and standalone directories.

Following the core collection schema and serialization format introduced in [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220), libraries need a formal manifest definition (`pypost-library.yaml` / `pypost-library.json`) to bundle multiple collections, declare shared variable schemas, and specify environment preset profiles.

However, sharing collection libraries across teams and source control introduces key operational challenges:
1. **Accidental Credential Exposure**: Developers frequently work with sensitive authentication credentials (API keys, personal access tokens, passwords). If collections require secrets to run, users might inadvertently commit secret values into version control.
2. **Disconnected Variable Overrides**: Developers often need machine-specific or environment-specific variable overrides (e.g., pointing a service URL to `localhost:8080` instead of a remote server) without dirtying the Git working tree or modifying shared team definitions.
3. **Complex Multi-Layered Variable Merging**: A collection library has default values, named target profiles (such as `local`, `staging`, `production`), and individual user secrets. Without a unified, deterministic resolution hierarchy, consumers cannot reliably predict what variable value will take effect during execution.

**Business Goal:**
Deliver a robust library manifest schema validator and a secure `LocalOverlayManager`. This subsystem allows teams to distribute version-controlled collection libraries with declared variable schemas and preset profiles, while storing all user-entered secret values, local overrides, and active profile choices in local configuration storage (`~/.pypost/libraries_data/`). The system evaluates effective variables across a predictable 3-tier precedence hierarchy (Defaults -> Active Profile -> Local Overlays), preventing secrets from ever entering Git while guaranteeing deterministic request execution.

## Programming Language

- **Implementation language**: Python (manifest models, schema validators, local overlay persistence manager, resolution engine, and unit tests).

## User Stories

- As a **Library Consumer (Developer / QA Engineer)**, I want to load a collection library through its manifest, select an active preset profile (e.g., `staging`), and provide my private tokens and local variable overrides in a local overlay, so that my requests execute with effective values without modifying the version-controlled library files.
- As a **Security Administrator / Team Lead**, I want team collection libraries to declare required variables and secrets via manifest schemas without embedding real sensitive credentials, ensuring secret values stay strictly confined to individual local user directories (`~/.pypost/libraries_data/`) and are never exposed in Git commits or pull requests.
- As an **Automated Runner / CLI / Agent**, I want to validate library manifests against standard schemas, apply environment or local overlay overrides, and resolve effective variables deterministically, receiving descriptive validation diagnostics when required secrets or variables are missing.
- As a **Downstream Feature Developer (Git Sync & UI Integration)**, I want a standardized manifest validator model and `LocalOverlayManager` contract (for [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222) and [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)) to inspect library metadata, persist per-library local overrides, and compute effective runtime variables.

## Definition of Done

This task is considered complete when:

1. Business requirements, entity definitions, and acceptance criteria for library manifests, local overlays, and effective variable resolution are fully documented.
2. A manifest schema validator parses and validates `pypost-library.yaml`, `pypost-library.yml`, and `pypost-library.json` files, verifying library metadata (id/name, version, description, collection file paths, library-level variable declarations, and preset profiles).
3. The `LocalOverlayManager` manages per-library local storage in `~/.pypost/libraries_data/<library-id>/`, storing user-entered secret values, local variable overrides, and the active profile selection per library.
4. Layered effective variable resolution is implemented and verified according to the strict precedence hierarchy:
   - **Layer 1 (Base)**: Manifest and Collection Default Values
   - **Layer 2 (Profile)**: Active Preset Profile Values
   - **Layer 3 (Overlay)**: Local Secret Values and Variable Overrides
5. Round-trip local overlay persistence is verified: saving, updating, retrieving, and clearing local overrides and secrets operates reliably without data corruption or workspace file interference.
6. Required variable and secret enforcement validates that all mandatory parameters (flagged with `required: true`) have non-empty effective values prior to execution, producing descriptive diagnostic errors for unpopulated required secrets.
7. Error diagnostics provide actionable, user-friendly messages for malformed manifests (syntax errors, missing fields, missing referenced collection files, type mismatches) and missing required secrets.
8. Scope boundaries are respected: pure domain models, manifest validators, local overlay persistence, and resolution engine without GUI widgets ([PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)) or Git cloning logic ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)).
9. Comprehensive test suite verifies manifest parsing, validation errors, overlay isolation, resolution precedence, required secret enforcement, and round-trip persistence.
10. Full repository quality gates pass (`make check`, `make lint`, `make typecheck`, `make test`, `make verify-ai-tasks`).

## Task Description

### Problem

When teams collaborate on API collections stored in Git repositories, sharing requests and variables requires a library-level manifest to group related collections and define standard environments. However:
- Version-controlled files must not contain personal secrets (API tokens, private keys, passwords).
- Users need to override specific endpoints or headers on their local machines without creating dirty Git working tree changes.
- Manifests can reference non-existent collections or specify invalid variable types, causing unexpected failures during execution.
- Without a clearly defined variable precedence hierarchy, users cannot determine whether a default, profile, or local value will be used during request execution.

### Current State (Inventory)

- **Collection Variable & Format Models** ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220)):
  - `CollectionVariable` (`pypost.models.collection_variable`): defines `name`, `type`, `default`, `description`, `required`, `secret`.
  - `Collection` (`pypost.models.models`): supports `description`, `version`, `variables`, `presets`, `requests`, `websockets`, `mcp_clients`.
  - `collection_serializer` (`pypost.core.collection_serializer`): serializes and deserializes self-contained YAML and JSON collections.
- **Environment System**:
  - `Environment` (`pypost.models.models.Environment`): legacy workspace-level key-value mapping with hidden key flags.
- **Missing Capabilities (Addressed in This Task)**:
  - No library manifest model or schema validator for `pypost-library.yaml` / `.json`.
  - No local overlay storage under `~/.pypost/libraries_data/` to isolate user secrets and overrides outside the Git workspace.
  - No multi-tier variable resolution engine merging manifest defaults, preset profiles, and local overlays.

### Scope (This Task)

- Define core domain models for:
  - Library Manifest (library ID/slug, name, version, description, referenced collections, variable declarations, preset profiles).
  - Library Local Overlay (library ID, active profile name, secret values dictionary, variable overrides dictionary).
  - Effective Variable Resolution Result (resolved key-value mappings, provenance metadata, unresolved required variables list).
- Implement manifest schema validator supporting both YAML (`pypost-library.yaml` / `.yml`) and JSON (`pypost-library.json`).
- Validate referenced collection files against filesystem paths relative to the manifest directory.
- Implement `LocalOverlayManager` for persistent storage under `~/.pypost/libraries_data/` (with configurable base directory for testing).
- Implement layered effective variable resolution engine merging:
  1. Default variable values declared in manifest and collections.
  2. Active preset profile variable overrides.
  3. User's local overlay secret values and variable overrides.
- Enforce required variable and secret checks, reporting all missing required items.
- Provide comprehensive error handling and diagnostics for invalid manifests and missing secrets.

### Out of Scope (This Task)

- Git repository clone, pull, push, and remote authentication service ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)).
- UI Library Manager panel, secret input dialogs, active profile dropdowns, and Git commit/push GUI flow ([PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)).
- Updating repository examples and sample library migrations ([PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224)).

### Functional Requirements

- **FR-1: Library Manifest Schema Definition & Validation**
  - The system shall define and validate the schema for a library manifest containing:
    - `id` / `slug`: Unique identifier for the library.
    - `name`: Human-readable display name of the library.
    - `version`: Semantic version string of the library.
    - `description`: Optional documentation / description text.
    - `collections`: List of relative file paths to collection files within the library directory.
    - `variables`: Optional list/mapping of library-level variable declarations (name, type, default, description, required, secret).
    - `presets`: Optional mapping of named preset profiles (e.g. `local`, `staging`, `production`) to variable value overrides.
  - Manifest validation shall enforce mandatory fields (`id` or `name`, `collections`), valid semantic versioning or string format, and valid variable definitions.

- **FR-2: Multi-Format Manifest Parsing (YAML & JSON)**
  - The system shall parse library manifests from both YAML (`pypost-library.yaml`, `pypost-library.yml`) and JSON (`pypost-library.json`) files or strings.
  - The parser shall report human-readable syntax and structural errors if the manifest content is malformed.

- **FR-3: Referenced Collection Verification**
  - When validating a manifest from a directory or file path, the system shall verify that all referenced collection files exist on disk relative to the manifest directory.
  - If a referenced collection file is missing or contains invalid collection data, the validator shall report a structured diagnostic error specifying the missing or invalid file path.

- **FR-4: Local Overlay Isolation and Directory Structure**
  - The system shall maintain local overlay data in the user's home configuration directory: `~/.pypost/libraries_data/<library-id>/`.
  - The overlay storage must remain strictly outside the library's Git working tree, ensuring local secret values and overrides are never exposed to version control.
  - The overlay base path must be configurable to support isolated test fixtures and custom data locations.

- **FR-5: Local Secret & Override Management**
  - The `LocalOverlayManager` shall store and retrieve per-library configuration containing:
    - `active_profile`: Optional name of the currently selected preset profile.
    - `secrets`: Mapping of variable names to user-entered secret values.
    - `overrides`: Mapping of variable names to user-entered local non-secret variable overrides.
  - Local overlay files must be saved with appropriate file permissions to protect sensitive information on multi-user systems.

- **FR-6: Layered Effective Variable Resolution**
  - The system shall resolve effective variable values for request execution according to the following precedence hierarchy (lowest to highest priority):
    1. **Level 1 (Base Defaults)**: Default values defined in the library manifest and individual collection variable schemas.
    2. **Level 2 (Active Profile)**: Variable values defined in the currently active preset profile (if a profile is selected).
    3. **Level 3 (Local Overlays & Secrets)**: Local variable overrides and secret values stored in the user's local overlay for the library.
  - A higher-precedence value shall override a lower-precedence value for the same variable key.

- **FR-7: Required Variable & Secret Enforcement**
  - When resolving effective variables, the system shall verify that every variable marked as `required: true` has a non-empty resolved effective value.
  - If any required variable or secret is missing or empty, the resolution engine shall return a list of unpopulated required variable names along with their descriptions and secret status, allowing consumers to prompt the user or fail gracefully.

- **FR-8: Local Overlay CRUD Operations**
  - The `LocalOverlayManager` shall provide operations to:
    - Load the local overlay for a given library ID.
    - Save or update secrets and variable overrides for a given library ID.
    - Set or clear the active preset profile for a given library ID.
    - Delete the local overlay data when a library is removed.
    - List all libraries that have local overlay data stored.

- **FR-9: Active Profile Selection & Persistence**
  - The system shall allow users to select or switch the active preset profile for a library.
  - The active profile choice shall be persisted in the local overlay so that subsequent sessions remember the selected profile.
  - If the active profile does not exist in the manifest presets, the resolution engine shall fall back gracefully or report an informative warning.

- **FR-10: Diagnostic Error Reporting**
  - The manifest validator and resolution engine shall provide structured diagnostic errors containing:
    - Error code or category (e.g., `MANIFEST_SYNTAX_ERROR`, `MISSING_COLLECTION_FILE`, `TYPE_MISMATCH`, `MISSING_REQUIRED_SECRET`).
    - Human-readable message explaining the root cause.
    - Contextual details (file path, line number if available, variable name, expected vs. actual type).

### Non-Functional Requirements

- **NFR-1 Security & Secret Isolation**: Sensitive credentials must be stored strictly in the user's local data directory (`~/.pypost/libraries_data/`) with restricted file permissions. Secrets must never be written to repository workspace files, manifests, or exported collection files.
- **NFR-2 Determinism & Consistency**: Variable resolution must be strictly deterministic: given the same manifest, active profile, and local overlay, the resulting effective variables must be identical on every evaluation.
- **NFR-3 Robustness & Data Integrity**: Missing directories, corrupt JSON/YAML files, or unexpected disk failures must be handled gracefully with clear diagnostics without crashing the application or corrupting other libraries' overlay data.
- **NFR-4 Performance & Efficiency**: Manifest validation, overlay loading, and variable resolution must be lightweight in-memory operations completing in milliseconds even for libraries with dozens of collections and hundreds of variables.
- **NFR-5 Cross-Platform Compatibility**: Directory path resolution (`~/.pypost/libraries_data/`) and relative collection file paths must function seamlessly across Linux, macOS, and Windows operating systems.

### Constraints and Assumptions

- Python is the implementation language for all manifest models, schema validators, local overlay managers, and resolution logic.
- Integrates cleanly with the `Collection` and `CollectionVariable` models established in [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220).
- Pure backend/core implementation; no GUI components or Qt dependencies are introduced in this task.
- Git repository synchronization is handled separately in [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222).
- Local overlay data is serialized in standard JSON format under `~/.pypost/libraries_data/<library-id>/overlay.json`.

### Main Entities (Business Perspective)

| Entity | Description | Key Business Attributes |
| --- | --- | --- |
| **Library Manifest** | Manifest descriptor defining a cohesive collection library bundle. | Library ID, Display Name, Version, Description, Collections List, Variable Declarations, Preset Profiles |
| **Collection Reference** | Reference to an individual collection file contained within the library. | Relative File Path, Loaded Collection Model, Validation Status |
| **Local Library Overlay** | User-specific local configuration and secret storage for a single library. | Library ID, Active Preset Profile Name, Secret Values Mapping, Variable Overrides Mapping |
| **Local Overlay Manager** | Subsystem managing storage, loading, updating, and removal of local overlays on disk. | Base Directory (`~/.pypost/libraries_data/`), CRUD Operations, Permissions Management |
| **Effective Variable Resolution** | Resolved variable state computed from the 3-tier precedence hierarchy. | Effective Key-Value Map, Variable Provenance (Default / Profile / Overlay), Missing Required Variables List |
| **Manifest Validator / Parser** | Engine validating manifest structure, variable types, and referenced collection files. | Supported Formats (`YAML`, `JSON`), Diagnostic Validation Results, Error Collector |

## Q&A

| Question | Answer |
| --- | --- |
| **Why is a library manifest needed in addition to individual collection files?** | A library manifest provides a single source of truth for bundling multiple related collections, declaring shared library-level variables, and establishing common preset profiles across an entire API domain or service suite. |
| **Why store secrets in `~/.pypost/libraries_data/` instead of `.env` files in the repository?** | Storing secrets in `.env` files within a Git working tree risks accidental commits, merge conflicts, or exposure in pull requests. Storing secrets in `~/.pypost/libraries_data/` completely decouples sensitive user data from the version-controlled workspace. |
| **What is the variable resolution order if a variable is defined in multiple places?** | The resolution order is strictly 3-tiered: (1) Base Defaults (manifest & collection defaults) -> (2) Active Profile Overrides -> (3) Local Overlay Overrides & Secrets. The local overlay always wins, allowing individual developers to override any value locally. |
| **What happens if a required secret is not provided in the local overlay?** | The effective variable resolution engine detects that the required variable lacks a value, marks it in the missing required list, and raises or returns a structured diagnostic error so the UI or CLI can prompt the user to input the secret. |
| **Are collections within a library forced to use YAML?** | No. Manifests can reference collections in either YAML (`.yaml`, `.yml`) or JSON (`.json`) format, matching the format-agnostic parser developed in PYPOST-1220. |
| **Is UI or Git sync code included in this task?** | No. This task implements only the core manifest schema validator, the `LocalOverlayManager`, and the effective variable resolution engine. UI integration is delivered in PYPOST-1223 and Git operations in PYPOST-1222. |

## References

- [PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221) — This task
- [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) — Parent Epic: *Git-based Collection Libraries & Self-Contained Collection Format*
- [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220) — Preceding story: *Core schema and serializers for self-contained collection format with variable metadata*
- [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222) — Sibling story: *Git repository clone, pull, and hybrid auth service*
- [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223) — Sibling story: *UI library manager panel, dirty check guards, and two-way Git commit/push flow*
- [PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224) — Sibling story: *Modernize examples to unified library format and preserve legacy fixtures in tests*
- `pypost/models/collection_variable.py` — Collection variable schema model
- `pypost/models/models.py` — Collection domain model
- `pypost/core/collection_serializer.py` — YAML/JSON collection serializers
