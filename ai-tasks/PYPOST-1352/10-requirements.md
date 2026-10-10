# PYPOST-1352: Built-in rows in MCP registry lifecycle and controller save

## Goals

Ensure that running Built-in MCP servers remain operational through workspace collection changes,
environment updates, and reconfiguration, and can be saved from the controller without modifying
shared library state.

From a business perspective, users who configure Built-in MCP servers (such as Jira, GitLab, and
GitHub MCP) expect them to behave as resilient, read-only first-class endpoints:
- A running Built-in server must not be inadvertently stopped when workspace collections are
  refreshed or when unrelated configuration dialogs (such as Environment Manager) close, because
  Built-in servers depend on curated package resources rather than workspace collection records.
- When a user edits workspace environment variables selected by a Built-in server, the server must
  refresh its variables while preserving default declarations from the shipped collection catalog
  for variables that the user environment does not explicitly define.
- A user can reconfigure or save a Built-in server without mutating or creating overlay state files
  in user storage (preserving read-only integrity for shipped library bundles).
- When a user attempts to save a Built-in server configuration that points to an invalid or
  non-entry collection, the system safely rejects the save without corrupting registry or settings
  state.
- Existing workspace and ordinary library server workflows remain fully intact and backward
  compatible.

## Implementation Language

- Python

## User Stories

- As an MCP server user, I want my active Built-in MCP server to keep running uninterrupted when
  workspace collections are updated or when the Environment Manager closes, so that unrelated
  workspace changes do not disrupt my active server tools.
- As an MCP server user, I want my active Built-in MCP server to stop with clear diagnostic
  reporting only if its selected workspace environment is explicitly deleted.
- As an MCP server user, I want updates to my workspace environment variables to immediately reflect
  in my running Built-in server while maintaining catalog defaults for omitted variables, so that
  required server settings remain complete and valid.
- As an MCP server user, I want to save or reconfigure a Built-in server without writing or
  altering shared library overlay files on disk, ensuring clean isolation and preventing unintended
  side effects across server instances.
- As an MCP server user, I want saving a Built-in server to validate against the official shipped
  bundle even if an external library clone with the same identifier is connected, ensuring my server
  always uses authentic bundled tools.
- As an administrator, I want invalid Built-in configurations (such as pointing to non-entry
  collection paths) to be rejected with a clear validation error upon save, preventing corrupt
  configurations from being stored.

## Definition of Done

1. **Server Lifecycle Stability**:
   - Running Built-in server endpoints remain operational when workspace collections are refreshed
     or when unrelated configuration dialogs close.
   - Built-in servers validate existence against the curated collection bundle rather than workspace
     collections.

2. **Accurate Fault Handling**:
   - A running Built-in server is stopped with clear diagnostics indicating a missing environment
     only when its selected workspace environment is deleted or absent.

3. **Seamless Reconfiguration Support**:
   - Running Built-in servers can be reconfigured seamlessly while serving clients, without failure
     due to the absence of workspace-scoped collection identifiers.

4. **Environment Updates with Catalog Defaults**:
   - Updating workspace environment variables merged into a running Built-in server preserves all
     catalog defaults for unassigned variables, ensuring parameter completeness matches initial
     startup.

5. **Isolation and Persistence Safety**:
   - Saving a Built-in server configuration validates against the curated collection bundle,
     unaffected by any identically named external libraries.
   - Saving a Built-in server never modifies or generates external overlay files on disk; the
     bundled library remains strictly read-only.
   - Saving a Built-in server referencing an invalid collection entry is rejected with an explicit
     validation error.
   - Saving an active Built-in server updates server configuration seamlessly, and any save failure
     performs an atomic rollback that leaves existing settings and runtime state unmodified.

6. **Backward Compatibility**:
   - Workspace server configurations and ordinary library server configurations retain their
     existing lifecycle and persistence behavior.

7. **Quality Gate Verification**:
   - Automated quality checks and task artifact integrity verification pass cleanly.

## Task Description

This task provides robust lifecycle management and safe persistence for Built-in MCP server
configurations in the desktop application.

### Business Problem and Context

Built-in MCP servers represent pre-packaged integrations shipped with the application. Unlike
workspace-defined servers, Built-in servers rely on curated collection definitions and standard
environment definitions.

Previously:
- Lifecycle checks evaluated Built-in servers against workspace collections, causing active Built-in
  servers to stop erroneously during workspace refreshes or dialog dismissals.
- Reconfiguration operations rejected Built-in server updates because workspace collection
  identifiers were absent.
- Refreshing environment variables discarded catalog defaults, leaving running servers with
  incomplete configuration whenever workspace environments changed.
- Saving Built-in configurations routed through shared library persistence paths, risking unwanted
  overlay file writes to disk and exposure to conflicting external library clones.

### Scope In

- **Server Lifecycle Stability**:
  - Keep Built-in servers active across workspace collection synchronization and dialog closures.
  - Reconcile Built-in server references against the curated collection bundle.
- **Fault Handling**:
  - Stop running Built-in servers with clear diagnostic errors only when the referenced workspace
    environment is deleted.
- **Reconfiguration Support**:
  - Allow updating parameters of running Built-in servers seamlessly without workspace collection
    constraints.
- **Environment Updates**:
  - Merge updated workspace environment variables while preserving catalog defaults for unassigned
    variables.
- **Isolation and Persistence Safety**:
  - Verify server configurations strictly against the curated collection catalog.
  - Persist Built-in server settings without writing or altering library overlay files.
  - Guarantee atomic rollbacks of settings and runtime state upon save failures.

### Scope Out

- Modifying lifecycle behavior for ordinary (non-Built-in) library servers (tracked in follow-up
  task PYPOST-1347).
- User interface changes to the MCP Servers dialog, server badge displays, or source selectors.
- Copying or duplicating built-in collections or paired environments into the workspace.
- Data schema migration for existing server configuration stores.

### Main Domain Entities

- **Built-in MCP Server Endpoint**: A pre-packaged, read-only MCP server instance managed by the
  runtime registry.
- **Curated Library Bundle**: The authoritative, shipped collection package providing verified tool
  and server definitions.
- **Workspace Environment**: User-defined environment variable sets that supply instance-specific
  configuration values.
- **Server Configuration Store**: Persistent application settings managing MCP server definitions
  and connection properties.
- **Environment Variable Snapshot**: The resolved combination of curated catalog defaults and
  workspace environment overrides active in a running server instance.

## Q&A

- **Why must Built-in server save operations take precedence over generic library saves?**
  Built-in servers represent curated integrations shipped with the application. If routed through
  generic library handling, external user-connected libraries sharing identical identifiers could
  override curated definitions, and shared overlay files could be modified. Dedicated handling
  guarantees isolation and authentic bundle resolution.
- **Why must no overlay files ever be written for Built-in servers?**
  Curated collections are shipped resources intended to remain strictly immutable. Instance-specific
  configuration belongs exclusively in the user's workspace settings and selected environment, not
  in shared disk overlay files.
- **Why must environment updates preserve catalog defaults for Built-in servers?**
  A running server requires both catalog defaults (such as standard operational parameters and
  flags) and user environment overrides. Merging updates rather than replacing the snapshot ensures
  that default values are not discarded when a user modifies unrelated environment variables.
- **Why are ordinary library servers excluded from this lifecycle change?**
  Ordinary library servers have an existing issue regarding workspace collection references that is
  tracked separately under PYPOST-1347. Restricting this update to Built-in servers delivers
  immediate stability for bundled integrations without creating unintended regressions for external
  libraries.
