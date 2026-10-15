# PYPOST-1409: Eliminate library-level variables and establish collection-scoped variables and catalog manifest

## Goals

From a business and end-user perspective, collections in PyPost represent distinct, cohesive sets of API requests, workflows, or tool integrations (such as Jira, GitHub, or GitLab integrations). When these collections are bundled into a shared library, users expect each collection to be self-contained and modular.

Currently, configuration variables and environment profile presets are defined at the overarching library level rather than within individual collections. This design causes several significant operational and user experience problems:
1. **Namespace Pollution**: Configuration variables from completely unrelated collections within the same library are mixed into a single global pool. Users configuring a specific collection are confronted with irrelevant variables from other collections, leading to confusion and errors.
2. **Broken Portability and Modularity**: Because collections depend on ambient variables declared outside themselves, an individual collection cannot function as an independent, self-contained unit. Sharing, exporting, or running a single collection without its parent library becomes unreliable.
3. **Unclear Provenance and Configuration Authority**: Having variables defined at the library level while collections attempt to declare their own variables creates ambiguity over which configuration values take precedence.
4. **Credential Exposure Risk**: When sensitive credentials or secrets are managed at the shared library level rather than per collection with machine-local isolation, sensitive tokens can easily be misconfigured or accidentally leaked across contexts.

The goal of this task is to establish clean collection scoping for all variables and presets, transform libraries into pure catalog indexes, and provide machine-local overlay capability for sensitive secrets and user preferences.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **API collection author**, I want to define all required variables, types, defaults, descriptions, and preset profiles directly inside my collection, so that my collection is completely autonomous, portable, and self-contained.
- As a **library curator**, I want collection libraries to function strictly as catalog indexes pointing to individual collections, so that adding or removing collections does not pollute or break the variable namespaces of other collections in the library.
- As a **developer / operator**, I want to configure and execute a collection using only the variables and preset profiles relevant to that specific collection, so that I am not distracted or confused by variables belonging to unrelated collections.
- As an **end user working across environments**, I want to define machine-local secret overrides and select my active profile preset on my local machine without modifying the shared collection definition, so that my private credentials remain secure and are not committed to shared repositories.
- As an **existing PyPost user with legacy libraries**, I want my existing libraries containing older library-level variables to continue functioning without crashes or configuration loss, while receiving clear deprecation guidance.

## Definition of Done

This task is considered complete when:
1. Library catalog indexes serve strictly as listings of collections, without requiring or defining library-level variables or preset profiles.
2. Collections are established as the single source of truth for their declared variables, expected data types, default values, documentation/descriptions, and profile presets.
3. Variable resolution operates strictly against the target collection's declared variables, the selected collection preset, and machine-local user overlays, eliminating dependence on ambient library variables.
4. Users can store machine-local secret overrides and designate their active preset profile per collection in an isolated local overlay that does not modify the shared collection definition.
5. Legacy library definitions that still include top-level variables or presets are handled gracefully with non-fatal deprecation notices and without application errors.
6. Acceptance criteria are validated through comprehensive fast unit tests and quality verification commands.

## Task Description

### Problem Statement

In the existing PyPost workflow, collection libraries bundle multiple API collections together. However, variable schemas and profile presets are declared at the library catalog level. When a library contains multiple disparate collections, all variables are combined into a global list. This causes name collisions, clutters configuration interfaces, and prevents collections from being treated as self-contained domain entities.

Furthermore, running or configuring an individual collection requires resolving variables against this ambient library definition. This tightly couples collections to their parent library, complicating standalone execution (such as Model Context Protocol servers) and preventing modular sharing.

### Scope

- **Catalog-Only Library Model**: Transition library definitions to act solely as catalog indexes that reference member collections, removing library-level variable and preset declarations from active catalog specifications.
- **Collection-Scoped Authority**: Establish the collection as the authoritative owner of all its variables, data types, defaults, help text, secret flags, and named profile presets.
- **Direct Collection Variable Resolution**: Update core variable resolution so that values are resolved directly from the target collection's definitions, its active preset profile, and machine-local user overrides.
- **Machine-Local Overlays**: Provide machine-local overlay storage to hold local secret values and active profile selections on a per-collection basis, ensuring private credentials remain off shared files.
- **Graceful Backward Compatibility**: Support legacy library catalogs that include top-level variable or preset declarations, issuing informative deprecation warnings while ensuring uninterrupted operation.

### Out of Scope

- Modifying the Model Context Protocol (MCP) server configuration dialog to run without a workspace environment (addressed downstream in PYPOST-1410).
- Building the workspace environment variable import dialog and UI button (addressed downstream in PYPOST-1411).
- End-to-end integration test suite and user-facing developer documentation across all epic deliverables (addressed downstream in PYPOST-1412).

### Functional Requirements

- **FR1 (Catalog Indexing)**: The library catalog must serve purely as an index of collection references (identifying information, version, title, description, and list of collection locations) and must not require or declare global library variables or presets.
- **FR2 (Collection Variable Ownership)**: Every collection must declare and own its variables, including variable name, data type (such as text, number, boolean, array, or object), default value, descriptive help text, required status, and secret designation.
- **FR3 (Collection Profile Presets)**: Every collection must be able to declare its own named profile presets (such as Staging, Production, or Sandbox) containing specific variable value mappings tailored to that collection.
- **FR4 (Collection-First Resolution)**: When resolving variables for execution, the system must evaluate values in a clear order of precedence:
  1. Base default values declared in the collection.
  2. Values defined in the collection's selected profile preset.
  3. Machine-local user overrides and secrets from the local overlay.
- **FR5 (Machine-Local Secret and Preset Isolation)**: The system must allow users to record secret overrides and designate an active profile preset on their local machine without altering the version-controlled collection definition.
- **FR6 (Legacy Catalog Compatibility)**: When loading a legacy library catalog that still contains top-level variables or presets, the system must ingest it without crashing, issue a clear deprecation warning, and use any legacy variables as fallback defaults only if not defined in the collection.

### Non-Functional Requirements

- **NFR1 (Data Integrity & Backward Compatibility)**: Ingestion of legacy library manifests and collections must not corrupt existing data or break existing workspaces.
- **NFR2 (Security & Confidentiality)**: Private credentials and secrets marked by the user must be kept in machine-local storage and never written to shared or exportable collection definitions.
- **NFR3 (Clarity & Usability)**: Users must only see and configure variables belonging to the active collection, eliminating cross-collection variable pollution.
- **NFR4 (Performance)**: Variable resolution and catalog index loading must be instantaneous and lightweight, adding negligible latency to collection loading and execution.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Library Catalog** | Lightweight index representing a curated collection repository | Identity, display name, version, summary description, collection references |
| **Self-Contained Collection** | Autonomous aggregate containing API requests, tool bindings, and configuration | Identity, name, requests, declared collection variables, named profile presets |
| **Collection-Scoped Variable** | Parameter specification owned by a specific collection | Name, data type, default value, description/help text, required indicator, secret indicator |
| **Collection Profile Preset** | Pre-configured environment profile specific to a collection | Preset name, variable value mappings |
| **Local Machine Overlay** | User-specific local configuration for a collection on a particular machine | Collection reference, active profile preset name, private secret overrides |

### User Scenarios

#### Scenario 1: Authoring a Self-Contained Collection
An author creates a collection for a third-party service. Within the collection, the author defines required variables (e.g., base URL, API key) with descriptions and data types, as well as two presets ("Development" and "Production"). When the collection is published or shared as part of a library catalog, other users receive a complete, self-contained package without needing separate library-level configuration.

#### Scenario 2: Configuring a Collection from a Multi-Collection Library
A user opens a library containing three distinct integrations (e.g., Issue Tracker, Code Repository, and Messaging). When selecting the Issue Tracker collection, the user sees only the variables defined for the Issue Tracker. Variables for the Code Repository and Messaging tools are completely isolated and do not appear in the configuration view.

#### Scenario 3: Secure Machine-Local Secret Override
A developer works with a team-shared collection in a version-controlled repository. The collection defines an API key variable marked as a secret. The developer enters their personal API token. The token is saved in their machine-local overlay rather than modifying the shared collection file, ensuring credentials are never accidentally committed or shared.

#### Scenario 4: Loading Legacy Library Catalogs
A user opens an existing library created with an older version of PyPost that has variables declared at the library root. The system safely reads the catalog without crashing, emits a deprecation log advising the user to migrate variables into collections, and allows existing workflows to continue uninterrupted.

## Q&A

**Q: Why must library-level variables be eliminated rather than maintained as a parallel feature?**  
A: Library-level variables create namespace pollution across disparate collections and violate the principle of self-contained modularity. When variables live at the library level, collections cannot be ported, exported, or run independently without their parent library context. Eliminating library variables establishes a clean, predictable single source of truth within each collection.

**Q: How are machine-specific secrets kept separate from shared collection definitions?**  
A: Shared collections define variable specifications (name, description, default, secret flag) and public presets, but never sensitive machine-specific credentials. A machine-local overlay stores the individual user's active preset selection and secret overrides on their local device, keeping credentials secure and preventing accidental repository commits.

**Q: What happens if an older library file with library-level variables is opened?**  
A: The system maintains backward compatibility by accepting the legacy structure without throwing validation errors. It emits a non-fatal deprecation notice and uses any legacy library variables as a fallback only when a variable is not defined within the collection itself.
