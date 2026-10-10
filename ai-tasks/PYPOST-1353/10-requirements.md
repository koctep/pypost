# PYPOST-1353: "Built-in" source with read-only marker in the MCP server dialog

## Task Metadata

- **Implementation language**: Python

## Goals

Enable users to discover, select, and configure curated built-in MCP servers directly from the MCP
servers management dialog, while making it transparent that these built-in collections are
read-only application-managed resources.

From a business perspective:
- Users should have seamless, first-class access to curated integrations (such as Jira, GitLab, and
  GitHub MCP) without having to manually import collection files or connect external repositories.
- Users must clearly understand that built-in collections are immutable and shipped with the
  application (receiving official updates on application upgrade), so they are not surprised by
  the absence of in-place editing or library overlay configurations.
- Users can pair a built-in collection with any of their workspace environments, requiring an
  environment selection to ensure valid server execution while preventing incomplete server
  configurations from being saved.
- Server overview tables must provide immediate visual clarity on whether an active MCP server is
  powered by a workspace collection, an external library, or a read-only built-in collection.
- Existing workspace collections and external library server workflows and presentations must remain
  strictly backward-compatible and undisturbed.

## User Stories

- As an API developer using PyPost, I want to select "Built-in" as the collection source in the MCP
  server creation dialog, so that I can easily configure official integrations shipped with PyPost.
- As an API developer using PyPost, I want to see a curated list of built-in collections marked with
  a "(read-only)" badge and an informative tooltip, so that I understand these collections cannot be
  modified in place and are automatically kept up to date across PyPost upgrades.
- As an API developer using PyPost, I want to select any workspace environment for my built-in MCP
  server and have the Save action blocked until an environment is chosen, so that I cannot save a
  server that lacks required environment settings.
- As an API developer using PyPost, I want the MCP server dialog to hide unnecessary library preset
  and overlay controls when "Built-in" is selected, so that the configuration interface is clean,
  simple, and focused only on the necessary settings.
- As an API developer using PyPost, I want to see "Built-in / <name> (read-only)" in the servers
  table for built-in MCP server rows, so that I can immediately distinguish built-in servers from
  workspace and external library servers.
- As an API developer using PyPost, I want editing an existing built-in server to restore the
  "Built-in" source and preselect its specific collection entry, so that I can review or change its
  assigned workspace environment without reconfiguring the server source from scratch.
- As an API developer using PyPost, I want my existing library and workspace MCP servers to continue
  rendering and operating as before, including legacy rows referencing official examples, so that my
  existing configurations remain undisturbed.

## Definition of Done

1. **Built-in Source Discovery & Selection**:
   - The MCP server editor provides "Built-in" as a third collection source option alongside
     "Workspace collection" and "Library".
   - Selecting "Built-in" populates the collection picker with the curated built-in collections
     catalog.
   - Each entry in the built-in picker displays a "(read-only)" marker and an informative tooltip
     explaining that the collection is shipped with PyPost and updated on upgrade.
   - When "Built-in" is selected, library-specific preset and overlay widgets are hidden or omitted.

2. **Environment Assignment & Save Validation**:
   - The environment selector displays available workspace environments.
   - Saving a built-in server requires an environment selection; attempting to save without an
     assigned workspace environment is blocked.
   - Saving a built-in server produces an MCP server configuration carrying the built-in library
     identity with the bundled marker set and workspace collection identifier cleared.

3. **Server Overview Table Representation**:
   - In the MCP servers overview table, rows configured from the built-in source display
     "Built-in / <name> (read-only)" in their collection/source column.

4. **Edit Workflow Integrity**:
   - Opening an existing built-in server for editing automatically preselects the "Built-in" source
     and its specific built-in collection entry.
   - Changes to the assigned environment or other server options can be saved successfully.

5. **Backward Compatibility & Legacy Row Preservation**:
   - Existing workspace collection and library server creation and editing workflows remain
     completely unchanged.
   - Legacy library rows referencing the example library without the bundled marker continue to open
     and render under the "Library" source as before.

6. **Quality Gate Verification**:
   - Automated GUI tests run headlessly with bounded waits and explicit timeouts.
   - Repository quality gates and task artifact integrity verification pass cleanly.

## Task Description

This task enhances the user interface of the MCP servers management dialog to introduce the
"Built-in" collection source for creating and editing local MCP servers.

### Business Context

PyPost ships with pre-packaged MCP server collections (such as Jira Cloud, GitLab, and GitHub MCP)
that allow users to run standard integrations with zero setup. Prior to this task, users could only
pick collections from their current workspace or from external libraries. To use bundled
integrations, users had to treat them as generic libraries, which exposed confusing preset/overlay
options and lacked clear indication that the collections were read-only and maintained by the
application.

Introducing a dedicated "Built-in" source provides a clear, streamlined path to instantiate
official integrations while protecting their read-only semantics.

### Scope In

- Adding a third collection source option ("Built-in") to the MCP server editor.
- Populating the built-in collection picker from the curated built-in collection catalog.
- Rendering a "(read-only)" marker and helpful tooltip on built-in collection options.
- Suppressing library preset and overlay controls when configuring a built-in server.
- Allowing assignment of any workspace environment while blocking saving when no environment is
  selected.
- Emitting the appropriate built-in server configuration upon saving.
- Preselecting the "Built-in" source and collection entry when editing an existing built-in server.
- Rendering "Built-in / <name> (read-only)" in the servers summary table for built-in rows.
- Seamless availability of the built-in catalog entries directly within the server configuration
  interface.

### Scope Out

- Creating editable workspace copies of built-in collections (handled in follow-up PYPOST-1355).
- Creating editable copies of paired environments (handled in follow-up PYPOST-1354).
- Server startup, reference lifecycle, and controller save logic (completed in PYPOST-1351 and
  PYPOST-1352).
- Automatic migration of existing library or workspace servers to the built-in source.

### Main Entities

- **MCP Server Dialog**: The user interface dialog managing local and remote MCP server
  configurations in PyPost.
- **MCP Server Editor**: The sub-view in the dialog where a user specifies the server name, source,
  collection, environment, and options.
- **Collection Source**: The origin category of the server collection: Workspace collection,
  Library, or Built-in.
- **Curated Built-in Collection**: An immutable collection definition shipped as a package resource
  with PyPost.
- **Workspace Environment**: A user-defined environment providing credentials and configuration
  values to the server.
- **Server Overview Table**: The table listing configured MCP servers with their status, source, and
  actions.

## Q&A

- **Why is "Built-in" presented as a distinct source rather than just another library?**
  Built-in collections are curated application assets that follow different lifecycle rules: they
  are strictly read-only, updated automatically when PyPost is upgraded, and do not use library
  presets or overlay files. Presenting them as a distinct source avoids confusing users with
  irrelevant overlay settings and clearly conveys their immutable nature.
- **Why are library preset and overlay widgets omitted for built-in collections?**
  Unlike generic libraries which allow local overlay configuration files, built-in collections rely
  solely on the user's workspace environment for variable resolution. Omitting preset and overlay
  controls keeps the UI clean and prevents users from configuring settings that are not supported
  for built-in servers.
- **Why must Save be blocked without a workspace environment?**
  Built-in MCP servers require authentication credentials or domain configuration to connect to
  external services (e.g. Jira host or GitHub token). Without an assigned workspace environment,
  the server cannot function. Blocking save when no environment is selected prevents broken server
  states.
- **How are legacy library servers referencing bundled examples handled?**
  Existing server rows that point to the examples library without the bundled marker continue to
  open and display as "Library" rows. No automatic migration is performed, ensuring absolute
  backward compatibility with existing configuration files.
