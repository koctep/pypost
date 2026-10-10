# PYPOST-1354: Editable copy of the paired environment for Built-in MCP servers

## Task Metadata

- **Implementation language**: Python

## Goals

Provide users creating or configuring a Built-in MCP server with an intuitive, one-click mechanism
to obtain the built-in collection's paired environment as an editable workspace environment.

From a business perspective:
- Users need a friction-free starting point for configuring credentials and variable settings
  required by curated Built-in MCP servers (e.g., Jira Cloud, GitLab, GitHub MCP) without
  manually assembling variable structures or discovering configuration schemas.
- Application-shipped environment files, templates, and baseline settings must be protected from
  in-place modification or corruption (preserving immutable package resources across upgrades).
- Shipped template secret values (such as API tokens or personal access tokens) must never be
  populated with live secrets or dirty credentials; users start with clean, empty secret fields to
  fill in safely within their private workspace.
- The workflow must prevent naming and identity collisions when a user creates multiple server
  instances or copies environments repeatedly.
- The copy action must remain entirely optional, allowing users to select any existing workspace
  environment whenever appropriate, while maintaining validation that blocks saving without an
  environment.

## User Stories

- As an API developer configuring a Built-in MCP server, I want to click an action in the server
  editor to create an editable copy of the collection's paired environment, so that I immediately
  get a complete, pre-structured environment matching the server's requirements.
- As an API developer configuring a Built-in MCP server, I want the newly created environment to be
  automatically saved to my workspace and preselected in the server's environment selector, so that
  I do not have to perform extra navigation steps before filling in my credentials.
- As an API developer, I want all sensitive secret values in the copied environment to be empty by
  default, so that placeholder tokens are cleared and I am prompted to enter my own credentials
  securely.
- As an API developer, I want the copied environment to preserve all paired variable keys, hidden
  flags, and MCP overridable flags, so that the environment behaves correctly with the server tools
  and variable resolution rules.
- As an API developer, I want the copy action to be prominently highlighted when no environment
  derived from that paired environment exists yet, so that I am guided to the recommended setup
  path.
- As an API developer, I want to create multiple copies of paired environments without collisions
  or overwrites, so that each instance receives a unique identifier and a distinct, conflict-safe
  display name.
- As an API developer, I want to choose any existing workspace environment instead of creating a
  copy if I already have an environment configured, so that my workflow remains flexible.
- As an API developer, I want the server editor to block saving if no environment is selected, so
  that I cannot accidentally persist an incomplete or unusable server configuration.

## Definition of Done

1. **Editor Action Availability & Visibility**:
   - The MCP server editor provides a dedicated action ("Create editable copy of paired
     environment") visible when the Built-in collection source is selected.
   - When no workspace environment derived from the paired environment exists, the action is
     visually highlighted as the recommended default action.
   - The action remains available but unhighlighted if matching or derived environments already
     exist in the workspace.

2. **Environment Derivation & Preservation**:
   - Triggering the action derives a new workspace environment from the paired environment of the
     selected built-in collection.
   - The derived environment preserves all variable keys defined in the paired environment.
   - Hidden variable keys (`hidden_keys`) and MCP overridable variable keys
     (`mcp_overridable_keys`) are strictly retained.
   - All secret variable values are cleared (empty string), preventing placeholder or template
     values from leaking into the user's workspace.
   - Non-secret variable definitions and defaults are preserved.

3. **Immutability of Shipped Resources**:
   - Shipped environment template files under the application examples directory remain strictly
     unmodified and byte-identical before and after the copy action.

4. **Collision Safety & Identifier Generation**:
   - Each created copy receives a fresh, globally unique identifier.
   - The display name is assigned conflict-safely (e.g., base name if available, or incremental
     suffix like `"<name> (2)"` when matching names exist), preventing overwrites of existing
     environments.
   - Repeated copy actions succeed deterministically without identifier or name collisions.

5. **Persistence & Selection Workflow**:
   - The new environment is saved directly to workspace environment storage.
   - The newly saved environment is immediately selected in the editor's environment selector.
   - Attempting to save a Built-in server without any selected environment remains strictly
     blocked.
   - Selecting any other existing workspace environment instead of copying remains fully
     functional.

6. **Quality & Verification**:
   - Headless automated GUI tests verify the editor action, creation workflow, collision handling,
     and validation behavior per repository testing standards.
   - Repository quality checks (`make check`) and task artifact integrity verification
     (`make verify-ai-tasks`) pass cleanly.

## Task Description

This task introduces the user interface action and business workflow to create an editable copy of
a built-in MCP collection's paired environment directly within the MCP server editor.

### Business Context

When configuring a curated Built-in MCP server (such as Jira Cloud, GitLab, or GitHub MCP), the
server requires a specific set of configuration variables and credentials (e.g., base URLs, API
tokens, organization slugs) to execute remote tool requests. Each built-in collection provides a
corresponding paired environment template defining these variables and their metadata (which keys
represent secrets and which keys can be overridden by MCP tools).

Because shipped application resources are immutable and must never be edited in place, users need
an effortless way to copy this specification into their private workspace environment collection.
Creating an editable copy with cleared secret fields ensures security best practices while
providing an optimal developer experience.

### Scope In

- Adding the "Create editable copy of paired environment" action to the MCP server editor when
  the Built-in source is active.
- Highlighting the copy action as the primary/default choice when no derived environment for the
  selected built-in collection currently exists in the workspace.
- Deriving a new workspace environment from the selected built-in collection's paired environment.
- Generating a fresh environment identifier and conflict-safe display name.
- Retaining all variable keys, hidden variable key markers, and MCP overridable key markers.
- Emptying all secret values in the derived environment.
- Persisting the new environment to the workspace environment store and selecting it in the
  environment combo.
- Maintaining the requirement that an environment must be chosen before saving the server.
- Supporting the manual choice of any existing workspace environment as an alternative.

### Scope Out

- Copying built-in collections for editing (tracked separately in PYPOST-1355).
- Modifying shipped application files or templates under the examples repository or package
  resources (strictly forbidden).
- Modifying the core variable resolution mechanism or registry runtime execution rules.
- Automatic migration of legacy server configurations.

### Main Entities

- **MCP Server Editor**: The configuration interface for setting up and modifying local MCP
  servers.
- **Built-in Collection**: Curated, immutable MCP collection shipped with PyPost.
- **Paired Environment**: The template environment associated with a built-in collection,
  defining its configuration keys, secret designations, and tool override permissions.
- **Workspace Environment**: A user-owned, editable configuration entity storing variable
  values and credentials within the active workspace.
- **Environment Selector**: The editor UI control used to select the workspace environment
  assigned to the MCP server.

## Q&A

- **Why is creating a copy of the paired environment optional rather than mandatory?**
  Users may already have an appropriate workspace environment created (for instance, an existing
  environment with shared credentials, or an environment copied previously). Allowing users to
  select any workspace environment provides necessary workflow flexibility while ensuring all
  runtime variables come strictly from the chosen workspace environment.
- **Why are secret values cleared in the copied environment instead of keeping placeholders?**
  Shipped environment templates contain descriptive placeholder tokens (e.g., `YOUR_API_TOKEN`)
  that are invalid credentials. Clearing secret fields prevents users from accidentally attempting
  to authenticate with non-functional placeholder values and encourages prompt entry of valid
  personal credentials.
- **How does the system determine whether to highlight the copy action?**
  The editor inspects available workspace environments. If no environment derived from the
  collection's paired environment is present, the action is styled prominently to guide the user
  toward creating one.
- **Why must shipped environment files remain byte-identical?**
  Shipped environments are part of the read-only application package. Preserving them as immutable
  guarantees that future PyPost application updates can be cleanly applied without file conflicts
  or credential pollution.
