# PYPOST-1220: [Libraries] Core schema and serializers for self-contained collection format with variable metadata

## Goals

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost is introducing version-controlled collection libraries that teams can share via Git repositories and standalone files.

Today, API collections in PyPost are exported primarily as raw request trees with loose, untyped environment bindings. When collections are shared or committed to source control:
1. **Variable declarations and documentation are disconnected**: Variable names used across requests lack formal declarations, explicit data types, default fallbacks, and descriptions. Consumers (both human engineers and automated agents) must guess what variables are expected.
2. **Secrets risk exposure in Git**: Without explicit metadata distinguishing public configurations from sensitive tokens or passwords, sensitive values can be accidentally committed into version control.
3. **No built-in environment presets**: Collections cannot embed standard target profiles (such as `local`, `staging`, `production`) directly in their definition without requiring separate, disconnected environment files.
4. **Limited format readability**: Git diffs on large monolithic JSON export files can be difficult to review compared to clean, structured YAML.

**Business Goal:**
Deliver a self-contained, version-control-friendly collection file format supporting both **YAML** and **JSON** representations. Each collection file self-describes its requests, its variable schema metadata (type, default, description, required, secret), and its named preset profiles. The format must provide lossless round-trip serialization and full backward-compatible import and export with existing PyPost collection files.

## Programming Language

- **Implementation language**: Python (core models, serializers, validation logic, unit tests).

## User Stories

- As an **API Developer / Collection Author**, I want to define variable metadata (data type, default value, description, required flag, and secret flag) directly within my collection, so that anyone importing or reading the collection understands exactly what inputs are needed.
- As an **API Developer**, I want to define named preset profiles (e.g., `local`, `staging`, `production`) within the collection with non-sensitive defaults, so team members can switch target profiles immediately without setting up external environments manually.
- As a **Team Collaborator / Operator**, I want to store and review collections in YAML format in Git repositories, so that change history, pull request diffs, and reviews are clean, readable, and concise.
- As a **Security-Minded Developer**, I want secret variables clearly flagged in the schema as secrets so that sensitive values are never exported into version-controlled default payloads and can be supplied securely via local overlays.
- As an **External Agent / MCP Consumer**, I want to inspect a collection's variable schema metadata programmatically so I can automatically discover required parameters, their data types, and documentation.
- As a **Legacy PyPost User**, I want to import my existing JSON collections without errors or data loss, and have them automatically upgraded to the new schema structure.
- As a **Downstream Library Service Implementer** (for [PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221), [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222), [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)), I want a reliable core model and serialization contract so manifest validators, local secret overlay managers, and Git sync services can parse and format collections deterministically.

## Definition of Done

This task is considered complete when:

1. Business requirements, entity definitions, and acceptance criteria for the self-contained collection format are fully documented.
2. The core collection model supports variable metadata schemas defining:
   - Variable name/identifier
   - Supported data types (`string`, `integer`, `number`, `boolean`, `array`, `object`)
   - Default value (validated against the declared type if provided)
   - Description / documentation string
   - Required flag (indicating whether a value must be supplied to execute requests)
   - Secret flag (indicating sensitive credentials or private tokens)
3. The core collection model supports named preset profiles containing variable value mappings.
4. Serializers and deserializers for both YAML (`.yaml` / `.yml`) and JSON (`.json`) formats are implemented and verified.
5. Round-trip serialization fidelity is proven: serializing a self-contained collection and deserializing it back produces identical semantic objects.
6. Backward compatibility is verified:
   - Legacy collection files (lacking variable metadata or preset profiles) import cleanly without data loss.
   - Collections can be exported in both the new self-contained YAML/JSON format and the legacy JSON format.
7. Validation and error handling provide clear, user-friendly error messages for malformed files, invalid types, duplicate variable names, or conflicting preset entries.
8. Test coverage validates all serialization, deserialization, type checking, round-trip fidelity, and legacy import/export scenarios.
9. All quality gates (`make check`, `make lint`, `make typecheck`, `make test`, `make verify-ai-tasks`) pass cleanly.

## Task Description

### Problem

API collections currently represent request trees but lack integrated variable schemas and preset profiles. When sharing collections across teams or version-controlling them in Git repositories:
- Users cannot tell which variables are mandatory vs. optional.
- There are no type constraints on variables.
- Secret variables are not explicitly distinguished from normal variables, raising security risks.
- Switching between standard profiles requires managing separate environment files.
- The existing storage and export format is strictly JSON-based, which can be verbose and less readable in Git diffs.

### Current State (Inventory)

- **Collection Model** (`pypost.models.models.Collection`):
  - Contains `id`, `name`, `requests` (`List[RequestData]`), `websockets` (`List[WebSocketConnection]`), `mcp_clients` (`List[McpClientConnection]`).
  - Lacks collection-level variable metadata definitions and preset profiles.
- **Environment Model** (`pypost.models.models.Environment`):
  - Contains `id`, `name`, `variables` (`Dict[str, str]`), `hidden_keys` (`Set[str]`), `enable_mcp` (`bool`).
  - Stored separately from collections; untyped string values only.
- **Export Logic** (`pypost.core.collection_export`):
  - Exports single or multiple collections as indented JSON.
- **Import Logic** (`pypost.core.collection_import`):
  - Imports JSON collections with conflict resolution and shape validation.
- **YAML Support in Project**:
  - `PyYAML` is already a project dependency (used in request body handling and configuration).

### Scope (This Task)

- Define core domain models for:
  - Variable metadata schema (name, type, default, description, required, secret).
  - Preset profiles (named collections of variable values).
  - Enhanced self-contained collection model integrating variable schemas and preset profiles alongside existing requests, websockets, and MCP clients.
- Implement pure serializers and parsers for both YAML and JSON self-contained collection files.
- Enforce schema validation (valid type identifiers, type compatibility of default values, unique variable keys, unique profile names).
- Ensure round-trip serialization preservation (no loss of requests, scripts, headers, params, MCP tool configurations, variable definitions, or presets).
- Provide backward-compatible import parsing for legacy collection formats (auto-populating empty variable schemas and presets).
- Provide export options for both the modern self-contained format (YAML/JSON) and legacy compatibility format.

### Out of Scope (This Task)

- Library manifest (`pypost-library.yaml`) schema parser and validator (**PYPOST-1221**).
- Local secrets overlay manager and storage under `~/.pypost/libraries_data/` (**PYPOST-1221**).
- Effective variable resolution engine combining defaults, active presets, and local secret overlays (**PYPOST-1221**).
- Git repository clone, pull, and hybrid authentication service (**PYPOST-1222**).
- UI Library Manager panel, sync buttons, and Git commit/push dialogs (**PYPOST-1223**).
- Updating repository examples and moving legacy test fixtures (**PYPOST-1224**).

### Functional Requirements

- **FR-1: Variable Metadata Schema Definition**
  - The system shall allow collections to declare a list or mapping of variable definitions.
  - Each variable definition must specify:
    - `name` / `key`: Unique variable identifier.
    - `type`: One of the supported standard data types (`string`, `integer`, `number`, `boolean`, `array`, `object`). Default is `string`.
    - `default`: Optional default value conforming to the declared type.
    - `description`: Optional human-readable explanation of what the variable represents.
    - `required`: Boolean flag indicating whether the variable must have an effective value before executing requests that depend on it. Default is `false`.
    - `secret`: Boolean flag indicating whether the variable holds sensitive data (passwords, tokens, API keys). Default is `false`.

- **FR-2: Variable Default Value Validation**
  - When a default value is specified, the system shall validate that the value matches the declared `type`.
  - If a type mismatch occurs (e.g., default value `"abc"` for type `integer`), parsing or model validation must reject the invalid definition with a clear error description.
  - A `null` / `None` default is always valid regardless of the declared type, representing no default.

- **FR-3: Preset Profiles Definition**
  - The system shall allow collections to declare named preset profiles (e.g., `local`, `staging`, `production`).
  - Each preset profile must have a unique name within the collection and specify variable override values mapped by variable name.
  - Preset values must correspond to declared variable types or be validated against them.

- **FR-4: Self-Contained Collection Model**
  - The collection model shall encompass:
    - Collection identification (`id`, `name`, optional `description`, optional `version`).
    - Variable definitions / metadata schemas.
    - Preset profiles.
    - Child items: HTTP requests (`requests`), WebSocket connections (`websockets`), and MCP client connections (`mcp_clients`).

- **FR-5: YAML and JSON Serializers**
  - The system shall provide serializers that output the complete self-contained collection in standard YAML and JSON representations.
  - The YAML serializer must produce human-readable, cleanly formatted YAML suitable for Git commits and pull request diffs.
  - The JSON serializer must produce well-formed, indented UTF-8 JSON.

- **FR-6: YAML and JSON Deserializers**
  - The system shall provide deserializers that parse self-contained YAML and JSON collection strings or files into the collection model.
  - Deserializers must validate the syntax, structure, variable schemas, and preset profiles, reporting structured errors on invalid input.

- **FR-7: Lossless Round-Trip Serialization**
  - Serializing a collection to YAML or JSON and subsequently parsing the output must recreate the collection model with full semantic equality:
    - All request attributes (URLs, methods, headers, params, body types, post-scripts, MCP tool parameters, retry policies) are preserved.
    - All WebSocket and MCP client connection parameters are preserved.
    - All variable metadata (types, defaults, descriptions, required flags, secret flags) are preserved.
    - All preset profiles and their values are preserved.

- **FR-8: Backward-Compatible Legacy Import**
  - The system shall continue to import legacy collection files (which lack variable metadata schemas, preset profiles, or new metadata fields) without error.
  - Legacy collections imported into the new model shall initialize with empty variable metadata lists and empty preset profile dictionaries.

- **FR-9: Export Format Flexibility**
  - The export subsystem shall support exporting collections as:
    - Self-contained YAML (`.yaml` / `.yml`)
    - Self-contained JSON (`.json`)
    - Legacy compatible JSON (for backward compatibility with older tools or consumers)

- **FR-10: Error Diagnostics**
  - Parsing errors (malformed YAML/JSON, invalid schema types, type mismatches, duplicate names) must produce human-readable diagnostic messages identifying the problem and location or field where possible.

### Non-Functional Requirements

- **NFR-1 Fidelity & Determinism**: Serialization must be deterministic (stable ordering of keys and items) so that saving an unchanged collection produces identical file output and minimal Git diff noise.
- **NFR-2 Human Readability**: YAML output should use clean indentation and standard block styles for multi-line scripts or descriptions.
- **NFR-3 Security & Safe Defaults**: Secret variables must be explicitly recognizable by downstream consumers (such as the Local Overlay Manager in PYPOST-1221) so sensitive values are not inadvertently exported or committed.
- **NFR-4 Performance**: Serialization and parsing of large collections (hundreds of requests and variables) must execute swiftly in memory without UI freezing or noticeable latency.
- **NFR-5 Robustness**: Corrupted or partially invalid collection files must fail cleanly with informative validation messages rather than crashing the application or leaving corrupted state.

### Constraints and Assumptions

- Python is the implementation language for the core models and serializers.
- PyYAML is available in the environment for YAML parsing and dumping.
- Pydantic models are used across PyPost for domain modeling and validation.
- Existing request models (`RequestData`), WebSocket models (`WebSocketConnection`), and MCP client models (`McpClientConnection`) remain the core request item types and are preserved within the collection.
- GUI integration of the Library Manager panel and two-way Git syncing will build on these core models in subsequent stories (PYPOST-1221 through PYPOST-1223).

### Main Entities (Business Perspective)

| Entity | Description | Key Business Attributes |
| --- | --- | --- |
| **Self-Contained Collection** | Top-level business entity encapsulating API requests, variable schemas, and configuration profiles for standalone use or Git sharing. | ID, Name, Description, Version, Variable Definitions, Preset Profiles, Requests, WebSockets, MCP Clients |
| **Variable Definition (Metadata Schema)** | Formal declaration of a variable used by the collection, defining its contract and sensitivity. | Name, Type (`string`, `integer`, `number`, `boolean`, `array`, `object`), Default Value, Description, Required (`bool`), Secret (`bool`) |
| **Preset Profile** | Named configuration profile representing an environment or target context with specific variable value overrides. | Profile Name (e.g. `local`, `staging`, `production`), Variable Values Mapping |
| **Collection Request** | Executable HTTP request definition belonging to the collection. | Name, Method, URL, Headers, Parameters, Body, Post-Script, MCP Settings, Retry Policy |
| **Collection Connection** | WebSocket or MCP client connection associated with the collection. | Connection ID, Name, URL / Command, Connection Parameters |
| **Collection Serializer / Parser** | Logic component converting between in-memory collection models and external file formats. | Supported Formats (`YAML`, `JSON`, `Legacy JSON`), Round-trip Fidelity, Validation |

## Q&A

- **Q: Why are variable metadata and preset profiles embedded directly in the collection file instead of a separate environment file?**
  **A:** When sharing collections in Git repositories or as standalone files, decoupling variable schemas from the collection causes missing documentation, unknown required variables, and broken request execution. Embedding schemas and non-sensitive preset profiles ensures the collection is truly self-contained and immediately understandable by any team member or AI agent.
- **Q: How does this format handle sensitive secrets?**
  **A:** Variables are declared with a `secret: true` flag. The collection file defines the variable schema (its name, type, description, and required status) with no secret values embedded. Actual sensitive secret values are kept out of Git and supplied via local overlay storage (managed in PYPOST-1221).
- **Q: What data types are supported for variables?**
  **A:** Standard types: `string`, `integer`, `number`, `boolean`, `array`, and `object`. Default is `string`. Default values must match the declared type if supplied.
- **Q: Why support both YAML and JSON?**
  **A:** YAML is optimized for human reading and clean Git diffs in version-controlled repositories. JSON is standard for interoperability, programmatic tooling, and legacy export/import workflows.
- **Q: Does this break existing PyPost collection files?**
  **A:** No. The import parser is fully backward-compatible and accepts legacy collection files, initializing missing variable schemas and presets with empty defaults. Legacy JSON export is also maintained.
- **Q: Is UI implementation included in this task?**
  **A:** No. This task is strictly focused on the core models, schema definitions, validation, and pure YAML/JSON serializers. The UI Library Manager and Git sync dialogs are implemented in PYPOST-1223.

## References

- [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220) — This task
- [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) — Parent Epic: *Git-based Collection Libraries & Self-Contained Collection Format*
- [PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221) — Sibling story: *Library manifest schema validator and local secrets overlay manager*
- [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222) — Sibling story: *Git repository clone, pull, and hybrid auth service*
- [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223) — Sibling story: *UI library manager panel, dirty check guards, and two-way Git commit/push flow*
- [PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224) — Sibling story: *Modernize examples to unified library format and preserve legacy fixtures in tests*
- `pypost/models/models.py` — Current core data models
- `pypost/core/collection_export.py` — Current collection export logic
- `pypost/core/collection_import.py` — Current collection import logic
