# PYPOST-1410: Standalone MCP server configuration and execution without workspace environment

## Goals

Model Context Protocol (MCP) servers in PyPost enable external AI assistants, autonomous agents, and client applications to access API collections as standardized tools and resources. When users want to expose a curated integration (such as Jira, GitHub, or GitLab tools) from a shared collection library, they expect a streamlined setup process that works out of the box.

Previously, setting up an MCP server from a library collection required binding it to an "Environment" in the user's workspace. This architectural constraint created several operational and user experience problems:
1. **Forced Creation of Dummy Environments**: Users who simply wanted to run a library tool integration were forced to create and maintain empty or dummy workspace environments solely to satisfy the requirement of binding an environment to an MCP server.
2. **Cluttered Configuration Interface**: The MCP server configuration interface presented workspace environment selectors and displayed confusing, global library variable lists rather than showing only the configuration settings relevant to the specific collection being exposed.
3. **Impeded Standalone Execution**: Even though library collections contain their own variable declarations, default values, documentation, and preset profiles, the system could not run them independently without tying them to workspace environments.

With self-contained, collection-scoped variables and presets established, each collection contains all the metadata and default values needed for its operation. Combined with machine-local secret storage, a library collection can function as a completely autonomous, standalone MCP server.

The goal of this task is to decouple MCP server configuration and execution from workspace environments, allowing users to configure, customize presets and local secrets for, and launch standalone MCP servers cleanly and directly from library collections with zero workspace environment overhead.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **AI integration developer**, I want to configure and launch an MCP server directly from a library collection without selecting or creating a workspace environment, so that I can immediately expose tools to my AI client without cluttering my workspace with dummy environments.
- As an **operator / user**, I want the MCP server setup interface to display only the configuration variables, help descriptions, and preset profiles belonging to the selected collection, so that I have a clean, focused, and intuitive setup experience.
- As a **developer using multiple environments**, I want to select a pre-configured collection preset (such as Staging or Production) directly in the MCP server configuration, so that the server starts with the right parameters for my target environment.
- As a **security-conscious user**, I want to supply secret credentials (such as API keys and access tokens) for a standalone MCP server on my local machine without modifying shared collection files or storing them in workspace environments, so that sensitive credentials remain private and secure.
- As an **existing PyPost user with workspace-linked MCP servers**, I want my existing workspace collection MCP servers to continue operating normally with their associated workspace environments, so that my existing workflows and configurations remain unbroken.

## Definition of Done

This task is considered complete when:
1. MCP servers created from library collections can be configured, saved, and executed without requiring or selecting a workspace environment.
2. The MCP server configuration interface dynamically adapts based on the collection source: when a library collection is selected, workspace environment selectors are hidden, and collection-specific variables, descriptions, and presets are displayed.
3. Users can select from available collection presets and configure machine-local secret overrides directly within the MCP server setup workflow.
4. Standalone MCP servers successfully initialize and execute tool requests using resolved collection variables, active preset values, and local secret overrides.
5. Missing required non-secret variables produce clear diagnostic messages preventing server startup, while missing secrets during inspection do not cause fatal crashes.
6. Workspace collections that rely on workspace environments continue to function without regression.
7. Acceptance criteria are validated through automated tests and repository quality gates.

## Task Description

### Problem Statement

PyPost allows users to expose collections as MCP servers so external AI tools can interact with APIs. However, the system historically treated workspace environments as mandatory for all MCP server configurations. When a user wanted to run a standard server from a connected library, they were forced to select or generate a workspace environment. This requirement introduced unnecessary cognitive overhead, polluted user workspaces with single-purpose dummy environments, and exposed users to confusing global variable lists.

Because collections now authoritatively define their own variables and environment presets, this tight coupling is no longer necessary. Standalone MCP servers should run directly from collection-declared parameters and machine-local user secrets without touching the workspace environment subsystem.

### Scope

- **Decoupled MCP Server Configuration**: Update the MCP server configuration data model so that workspace environment binding is optional, enabling standalone configuration for library collection servers.
- **Context-Aware Configuration Interface**: Enhance the MCP server configuration dialog so that selecting a library collection removes workspace environment selection controls and presents collection-specific variables, data types, help text, and preset choices.
- **Preset Profile Selection**: Allow users to select an active collection preset profile directly within the MCP server configuration.
- **Machine-Local Secret and Override Management**: Enable users to input sensitive secrets and custom variable overrides for standalone MCP servers, storing them securely in machine-local storage rather than in shared collection files or workspace environments.
- **Standalone Server Runtime Execution**: Update server startup and execution logic to launch standalone MCP server processes using resolved collection variables, chosen preset values, and local secret overrides.
- **Validation and Graceful Diagnostics**: Ensure that server startup validates that all required non-secret variables are satisfied, while allowing server inspection to proceed gracefully before secrets are entered.

### Out of Scope

- Importing collection variables into workspace environments (addressed in child task PYPOST-1411).
- End-to-end integration test suite and final developer documentation across the complete epic (addressed in child task PYPOST-1412).
- Modifying the underlying MCP protocol transport layers (stdio, SSE, HTTP).

### Functional Requirements

- **FR1 (Optional Workspace Environment)**: The system must allow an MCP server configuration to be saved and executed without an associated workspace environment when configured from a library collection.
- **FR2 (Context-Aware Configuration Interface)**: When configuring an MCP server from a library collection, the interface must hide the workspace environment selector and present only the variables, types, and help descriptions declared by that specific collection.
- **FR3 (Collection Preset Selection)**: The configuration interface must allow users to choose from the preset profiles defined by the collection (e.g., Development, Staging, Production) to populate baseline parameter values.
- **FR4 (Machine-Local Secret and Parameter Overrides)**: The configuration interface must allow users to provide secret values and parameter overrides that are saved in machine-local storage, ensuring sensitive tokens are not saved into shared collection files or workspace environments.
- **FR5 (Standalone Runtime Launch)**: When starting a standalone MCP server, the runtime runner must launch the server process using the effective variables resolved from the collection's defaults, selected preset profile, and machine-local secrets and overrides.
- **FR6 (Startup Validation and Diagnostics)**: Before launching a standalone MCP server, the system must verify that all required variables have been satisfied by defaults, presets, or user overrides, presenting actionable error messages if required parameters are missing.
- **FR7 (Backward Compatibility for Workspace Servers)**: Existing and new MCP servers created from workspace collections must continue to support workspace environment selection and variable resolution without regression.

### Non-Functional Requirements

- **NFR1 (Usability & Simplicity)**: Users must be able to configure and run a library collection MCP server in a single streamlined workflow without creating auxiliary workspace assets.
- **NFR2 (Security & Confidentiality)**: Secret values entered by the user must be stored in machine-local storage with restricted file permissions, and sensitive values must be masked in runtime process logs and diagnostics.
- **NFR3 (Reliability & Robustness)**: The server supervision system must handle process crashes or configuration errors gracefully, reporting clear diagnostic statuses back to the user interface.
- **NFR4 (Performance)**: Resolving configuration variables and spawning the standalone server process must introduce no measurable delay compared to workspace-bound execution.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **MCP Server Configuration** | Stored specification for running an MCP tool server | Server name, server type, collection reference, optional workspace environment, enabled tools/resources |
| **Self-Contained Collection** | Autonomous collection providing tools and request definitions | Collection identity, display name, declared variables, preset profiles |
| **Collection Preset Profile** | Pre-configured environment profile tailored for the collection | Preset name, collection-specific parameter values |
| **Machine-Local Secrets & Overrides** | User-specific credentials and custom settings for a collection on the local machine | Collection reference, active preset selection, secret overrides, parameter overrides |
| **MCP Server Runtime Process** | Active running server process servicing AI client tool calls | Process status, port/transport, effective runtime parameters, masked secrets |
| **Workspace Environment (Optional)** | Traditional workspace variable container | Environment identity, name, variable key-value pairs (used only when explicitly bound) |

### User Scenarios

#### Scenario 1: Quick-Start Standalone MCP Server from a Library
An AI developer wants to provide a GitHub MCP tool server to their local coding assistant. The developer opens the MCP server dialog in PyPost and selects the GitHub collection from a connected library. The dialog immediately shows the collection's declared variables (such as repository URL and API token) and hides the workspace environment selector. The developer selects the "Default" preset, enters their API token, and clicks "Start". The server starts immediately as a standalone process without creating any workspace environment.

#### Scenario 2: Switching Environment Presets for a Standalone Server
A QA engineer uses an MCP server for a payment gateway collection. The collection defines "Sandbox" and "Production" presets. The engineer edits the MCP server configuration, selects the "Sandbox" preset from a dropdown, and saves. When the server launches, it automatically receives the endpoint and configuration associated with the Sandbox preset, combined with the engineer's local test credentials.

#### Scenario 3: Secure Local Secret Storage
A user configures an MCP server from a team-shared library collection that requires an administrative token. The user enters the token into the configuration dialog. The system stores the secret in the user's machine-local secure storage rather than modifying the shared collection definition or creating an unencrypted workspace variable. When the team updates the collection in version control, the user's local token remains intact and secure.

#### Scenario 4: Preserving Existing Workspace Collection MCP Servers
A user has an existing custom workspace collection paired with a workspace environment named "Staging". When opening the MCP server dialog for this server, the workspace environment selector remains available, and the server continues to execute using the workspace environment variables exactly as before.

## Q&A

**Q: Why should MCP servers be decoupled from workspace environments?**  
A: Curated library collections are self-contained: they declare all their required variables, data types, documentation, and presets. Forcing users to create or select a workspace environment just to run an MCP server forces users to generate unnecessary phantom environments and clutters the interface. Decoupling them allows zero-friction, out-of-the-box execution.

**Q: How are required variables validated when starting a standalone MCP server?**  
A: Before launching the server process, the system verifies that all required variables declared by the collection have resolved values (either from collection defaults, the selected preset profile, or user overrides in local storage). If any required variable is unfulfilled, startup is halted with a clear diagnostic message highlighting which parameters need to be configured.

**Q: Where are sensitive credentials stored for a standalone MCP server?**  
A: Sensitive credentials (secrets) entered in the configuration dialog are stored in machine-local storage with restricted file permissions on the user's machine. They are never written to shared collection files, preventing credential leakage when sharing collections.

**Q: Will existing MCP servers that use workspace environments break?**  
A: No. Making the workspace environment optional preserves complete backward compatibility. MCP servers associated with workspace collections can still select and use workspace environments, ensuring existing workflows and configurations continue without disruption.
