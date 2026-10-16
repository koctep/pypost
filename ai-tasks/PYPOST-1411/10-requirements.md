# PYPOST-1411: Workspace environment variable import action from collections

## Goals

In PyPost, workspace environments allow users to store and manage variables—such as base URLs, authentication tokens, API keys, and parameter configurations—that dynamically parameterize requests and scripts across collections.

With the introduction of collection-scoped variables, collections authoritatively declare their own required variables, expected data types, default values, documentation descriptions, secret flags, and preset profiles. When users work with collections—whether authoring new ones, managing existing workspace collections, or copying curated integrations from connected libraries—they frequently need to synchronize these declared collection variables into their active workspace environments.

Previously, there was no direct bridge between a collection's declared variables and workspace environments. This created significant friction:
1. **Manual and Error-Prone Data Entry**: Users had to inspect a collection's variable requirements and manually re-enter variable names, default values, and types into their environment one by one.
2. **Risk of Exposing Sensitive Credentials**: When users manually transcribed variables, they had to remember to manually flag secret tokens as hidden. Forgetting to do so resulted in sensitive credentials being displayed in plaintext and stored unencrypted.
3. **Lack of Safe Conflict Resolution**: If an environment already contained variables with overlapping names, users had no structured way to preview differences, choose whether to preserve existing values or replace them with collection defaults, or selectively import specific keys.
4. **Friction when Adopting Library Collections**: When a user copied a collection from a shared library into their workspace, they faced an awkward manual configuration step before they could run requests against their own environment.

The goal of this task is to provide an intuitive, secure, and user-friendly "Import from Collection" capability within the Environment Variables view. Users must be able to select a workspace or library collection, inspect its declared variables and preset profiles, select individual variables to import, choose a conflict resolution strategy (e.g., skip existing keys vs. overwrite existing values), and cleanly import the variables and secret protections into their workspace environment.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **API developer**, I want to import variables declared by a collection directly into my workspace environment from the Environment Variables view, so that I can configure my environment quickly without manually typing each variable name and default value.
- As a **developer working with multiple environments**, I want to select a collection's preset profile (such as Staging or Production) during the import process, so that my workspace environment is populated with the specific configuration values tailored to my target deployment.
- As a **security-conscious user**, I want variables marked as secrets in the collection to be automatically imported as hidden, protected variables in my workspace environment, so that sensitive tokens are never displayed in plaintext or stored unencrypted.
- As an **integrator managing overlapping services**, I want to choose a conflict resolution strategy (e.g., keep my existing environment values or overwrite with collection defaults) when importing variables that already exist in my environment, so that I do not accidentally lose custom settings.
- As an **operator reviewing variable changes**, I want to preview candidate variables, see which ones already exist in my environment, and selectively include or exclude specific variables before committing the import, so that I retain full control over my environment state.
- As a **user with both workspace and connected library collections**, I want to select from any available workspace collection or connected library collection, so that I can import variables regardless of where the collection originates.

## Definition of Done

This task is considered complete when:
1. An "Import from Collection" action is readily accessible within the Environment Variables management interface.
2. An import dialog allows users to choose any available workspace collection or connected library collection as the import source.
3. The interface displays the selected collection's declared variables, including variable names, expected data types, default values, descriptions, and secret status.
4. When the selected collection contains preset profiles, users can choose whether to import base default values or values from a specific preset profile.
5. Users can selectively choose which variables to import using selection controls (e.g., checkboxes with select-all/deselect-all capability).
6. Conflict handling options are provided to resolve collisions when a variable name already exists in the target environment:
   - "Skip existing": Preserves existing environment variable values and only adds new variables.
   - "Overwrite existing": Updates existing environment variables with the collection default or preset values.
7. Any imported variable designated as a secret is automatically marked as hidden in the workspace environment, ensuring UI masking and encrypted storage.
8. Imported variable names are validated according to variable naming standards, preventing invalid identifiers from entering the environment.
9. Completing the import updates the environment variables table immediately, marks the environment as modified, and saves changes reliably.
10. All business logic, conflict resolution, secret handling, and user interface workflows are verified through automated tests and repository quality gates.

## Task Description

### Problem Statement

Workspace environments are the primary vehicle for configuring runtime parameters in PyPost. While collections now encapsulate their own variable declarations, data types, descriptions, secret indicators, and environment presets, there is currently no capability in the environment management view to inspect a collection and pull its declared variables into an environment.

Users who copy collections from shared libraries or work with existing workspace collections must manually transcribe variable keys, guess or copy default values, and remember to enable secret masking manually. This causes configuration errors, wastes time, and introduces security vulnerabilities when secrets are accidentally left unmasked.

### Scope

- **Import Action in Environment Variables View**: Add an accessible and clear "Import from Collection" action to the environment variables editor.
- **Collection Source Picker**: Provide an intuitive selector that discovers and lists all accessible collections, including workspace collections and collections from connected libraries.
- **Variable Inspection and Selection**: Display a comprehensive preview of candidate collection variables (name, type, default value, description, secret indicator), allowing users to select or deselect individual items.
- **Preset Profile Integration**: Enable users to select an available collection preset profile so that values from the chosen preset can be imported instead of base defaults.
- **Collision Detection & Conflict Strategies**: Detect which candidate variables already exist in the target environment and offer clear conflict resolution policies:
  - Skip existing keys (preserve current environment values and only import new keys).
  - Overwrite existing keys (replace existing values with the collection defaults or preset values).
- **Automatic Secret Protection**: Map collection variables marked as secrets directly to the target environment's hidden/secret protection mechanism, ensuring immediate visual masking and encryption at rest.
- **Variable Name Validation**: Ensure that all imported variable names comply with identifier naming requirements before applying them to the environment.
- **User Feedback & State Synchronization**: Provide visual confirmation of the import result (e.g., count of added and updated variables) and refresh the environment variables view cleanly.

### Out of Scope

- Standalone MCP server execution without workspace environments (delivered in PYPOST-1410).
- Automatic background synchronization or two-way synchronization between environments and collections (variables are imported explicitly by the user).
- Modifying underlying encryption algorithms or credential vault storage backends.
- Full end-to-end integration test suite and final cross-epic developer documentation (scheduled for PYPOST-1412).

### Functional Requirements

- **FR1 (Import Action Trigger)**: The Environment Variables view must provide an "Import from Collection" trigger accessible whenever an environment is selected for editing.
- **FR2 (Collection Selection)**: The import workflow must allow users to choose from all available collections, including local workspace collections and collections in connected libraries.
- **FR3 (Variable Inspection and Preview)**: The import interface must present a structured preview of declared variables for the selected collection, displaying variable name, expected type, value (default or preset), description/help text, secret status, and whether the variable already exists in the target environment.
- **FR4 (Selective Import)**: Users must be able to select and deselect individual variables for import, with convenient options to select all or deselect all candidate variables.
- **FR5 (Preset Profile Value Selection)**: If the selected collection defines preset profiles, the interface must allow the user to select an active preset, updating the previewed values to reflect the chosen preset profile.
- **FR6 (Conflict Resolution Policy)**: The interface must provide explicit conflict resolution options when candidate variables already exist in the destination environment:
  - *Skip existing*: Keep the current environment values; only add variables that do not already exist in the environment.
  - *Overwrite existing*: Overwrite existing variable values with the collection's default or preset values.
- **FR7 (Automatic Secret Protection)**: Variables designated as secrets in the collection must automatically be marked as hidden in the destination environment, ensuring UI masking and secure encrypted storage.
- **FR8 (Validation Guardrails)**: The import engine must validate that variable names conform to naming standards, cleanly rejecting or flagging invalid names before saving.
- **FR9 (Feedback and Refresh)**: Upon confirming the import, the system must apply the changes to the working environment, provide clear feedback indicating the number of variables added and updated, and immediately refresh the environment variables view.

### Non-Functional Requirements

- **NFR1 (Usability & Intuitiveness)**: The import process must be straightforward, requiring minimal clicks, clearly indicating existing variable collisions, and providing readable descriptions for all candidate variables.
- **NFR2 (Security & Confidentiality)**: Secret variables must never be exposed in plaintext or saved without hidden protection flags. Default secret masks must be applied immediately.
- **NFR3 (Data Safety & Non-Destructiveness)**: The default conflict resolution policy must be non-destructive ("Skip existing"), protecting existing customized values from accidental overwrites.
- **NFR4 (Performance & Responsiveness)**: Inspecting collection variables, toggling presets, and applying imported variables to an environment must be instantaneous without noticeable interface lag.

### Constraints and Assumptions

- **Target Environment Presence**: The import action operates on an existing, selected workspace environment. If no environment is currently selected, the import action is disabled or prompts the user to select or create an environment.
- **Collection Availability**: At least one collection (workspace collection or connected library collection) must be available to perform an import. If no collections exist, an informative message guides the user.
- **One-Way Explicit Import**: Importing is an explicit, point-in-time user action; it does not establish a persistent synchronization binding between the collection and the environment.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Workspace Environment** | The destination container for runtime variables | Environment name, variable key-value pairs, hidden/secret keys set, MCP override flags |
| **Source Collection** | The collection from which variables are imported | Collection identity, display name, origin (workspace vs. library), declared variables, preset profiles |
| **Collection-Scoped Variable** | Declared parameter specification within a collection | Variable name, data type, default value, description, required status, secret status |
| **Collection Preset Profile** | Pre-configured environment profile within a collection | Preset name, specific parameter value mappings |
| **Import Plan / Specification** | User-configured parameters for the import operation | Source collection, target environment, chosen preset profile, selected variable keys, conflict resolution policy |
| **Import Summary / Result** | Outcome report of the import operation | Count of added variables, count of updated variables, count of skipped variables, list of newly hidden keys |

### User Scenarios

#### Scenario 1: Quick Import from a Newly Copied Library Collection
A user copies a "Jira Cloud API" collection from a team library into their workspace. To start executing requests, the user opens the Environment Variables view for their "Development" environment and clicks "Import from Collection". The user selects the Jira collection from the source dropdown. The dialog previews the declared variables (`base_url`, `user_email`, `api_token`), showing that `api_token` is a secret. With "Skip existing" selected by default, the user clicks "Import". The variables are immediately added to their environment, and `api_token` is masked as a hidden variable.

#### Scenario 2: Safe Conflict Handling with Existing Environment Variables
A user is working on an environment that already defines `base_url = "https://staging.example.com"` and `timeout = "30"`. They import variables from an updated collection that defines `base_url = "https://api.example.com"` and `page_size = "50"`. In the import dialog, the user sees `base_url` flagged as an existing key. The user selects the "Skip existing" conflict policy and completes the import. The resulting environment retains `base_url = "https://staging.example.com"` and `timeout = "30"`, while adding `page_size = "50"`.

#### Scenario 3: Overwriting Variables Using a Specific Collection Preset
A developer wants to align their local workspace environment with the collection's "Staging" configuration profile. They open the import dialog, choose the collection, and select the "Staging" preset from the preset selector. The preview table instantly updates default values to the staging endpoints and configurations. The user selects the "Overwrite existing" conflict policy and proceeds. Existing keys are updated with the staging values, and new staging parameters are imported.

#### Scenario 4: Selective Import with Secret Protection
A QA engineer only needs two specific variables from a large collection containing thirty variables. They open the import dialog, uncheck "Select All", and check only the two desired variables (one of which is an API secret key). The engineer confirms the import. Only the two selected variables are added to the environment, and the secret key is automatically hidden and protected.

## Q&A

**Q: Why is an import action in the Environment Variables view needed if collections already have collection-scoped variables?**  
A: Collection-scoped variables provide self-contained definitions and enable standalone MCP servers to run without workspace environments. However, standard request execution in the workspace relies on workspace environments. Users who copy collections or run requests in their workspace need a fast, reliable way to populate their workspace environments with collection parameters without manual re-typing.

**Q: What is the default conflict resolution strategy, and why?**  
A: The default conflict strategy is "Skip existing" (keep existing environment values). This safe, non-destructive default ensures that users who have already configured specific environment values (e.g., custom tokens or local endpoints) do not accidentally overwrite them when importing variables.

**Q: How does the import action protect sensitive credentials?**  
A: When a collection variable has its secret indicator set, the import engine automatically marks the variable as hidden in the destination workspace environment. This ensures that the secret value is masked in the user interface and encrypted when encryption at rest is enabled.

**Q: Can users import variables from connected libraries as well as workspace collections?**  
A: Yes. The collection selector displays both workspace collections and collections available in connected libraries, allowing users to import variables regardless of whether the collection has already been copied into the workspace.

**Q: Does importing variables link the environment permanently to the collection?**  
A: No. The import operation is an explicit, point-in-time merge of variables into the environment. It does not create a tight coupling or permanent dependency between the environment and the collection, preserving environment flexibility.
