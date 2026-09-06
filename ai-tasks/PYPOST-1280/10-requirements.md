# PYPOST-1280: Select a library collection for an MCP server

## Goals

PyPost users need to expose a collection maintained in a connected Git library
through a local MCP server without first creating a separate workspace copy.
The MCP server configuration experience must make both workspace collections
and library collections discoverable, while giving the user a clear way to
complete the library collection's environment requirements.

The business goal is reliable, repeatable MCP server setup for shared library
content. A user should be able to choose the intended collection, see which
configuration values will be used, supply only local values that are needed,
and save a configuration that remains valid after the dialog is closed or the
application is restarted.

## User Stories

- As a PyPost user, I want to choose whether a local MCP server uses a
  workspace collection or a collection from a connected library.
- As a PyPost user, I want to browse connected libraries and the collections
  declared by each library manifest so that I can select a known library asset.
- As a PyPost user, I want required library variables to be shown with their
  available defaults and active-profile values so that I understand what the
  selected collection needs.
- As a PyPost user, I want to provide local overrides and secret values without
  changing the shared library content.
- As a PyPost user, I want invalid or incomplete configurations rejected with
  actionable feedback before an MCP server configuration is saved.
- As a PyPost user, I want to cancel browsing or configuration safely without
  changing my existing MCP server settings.
- As a PyPost maintainer, I want the user-facing behavior covered by UI,
  presenter, and controller tests and documented for future contributors.

## Definition of Done

The story is complete when all of the following business outcomes are met:

1. The local MCP server editor offers an explicit collection source choice:
   workspace collection or connected library collection.
2. The workspace source continues to show selectable workspace collections.
   Existing proxy-server behavior remains outside this story's local-collection
   selection flow.
3. The library source lets the user browse all currently connected libraries,
   identify each library, and select a bundled collection declared by its
   manifest.
4. A library collection can only be selected when its library and manifest
   entry are available and valid. A missing, unreadable, malformed, or stale
   library entry is not silently treated as a workspace collection.
5. After library collection selection, the user can review the collection's
   required and optional environment variables, including descriptions, types,
   secret designation, and available default values where supplied.
6. Effective values are presented using this business precedence, from lowest
   to highest priority:
   - collection or library manifest defaults;
   - the selected active profile's values;
   - the user's local non-secret overrides;
   - the user's local secret values.
7. The user can choose or confirm the active profile when profiles are provided,
   and an unavailable profile is reported as an error rather than ignored.
8. Required variables without usable values, values that do not match their
   declared type, and other invalid environment configuration prevent saving.
   The feedback identifies what the user must correct without exposing secret
   contents.
9. Local overrides and secrets are associated with the selected library and
   persist for later use without modifying the connected library's manifest or
   collection files. Secrets remain protected and are never displayed in clear
   text in diagnostics, logs, or documentation examples.
10. Saving a valid library-backed local MCP server configuration records the
    selected library collection and its resolved environment association through
    `McpServerSettingsController` and `MCPServerRegistry`. The saved row can be
    listed, edited, restarted, and restored after application reload.
11. A failed save or failed library/environment validation leaves the prior
    saved configuration unchanged. Existing configured MCP servers continue to
    be independently manageable.
12. While connected libraries or manifests are being browsed or environment
    values are being prepared, the user receives a visible busy state. The user
    can cancel the operation, and cancellation leaves no partial MCP server
    configuration or local overlay changes.
13. Library unavailable, manifest invalid, collection missing, environment
    incomplete, persistence failure, and cancellation states have distinct,
    understandable user feedback and do not cause an unhandled application
    failure.
14. Automated coverage verifies the behavior at the UI, presenter, and
    controller levels, including successful selection, precedence and required
    variable validation, persistence, cancellation, and representative errors.
15. Developer documentation explains the supported library-backed MCP server
    workflow, manifest/environment expectations, secret-handling boundary, and
    the relevant test coverage.

## Task Description

### Scope

This story covers the local MCP server configuration workflow for selecting and
using a collection from a connected Git collection library. It includes:

- choosing the collection source in the MCP server editor;
- browsing connected libraries and manifest-declared bundled collections;
- presenting and completing library collection environment configuration;
- resolving defaults, active profile values, local overrides, and secrets;
- validating the selected collection and environment before save;
- persisting the valid selection and keeping it usable through the MCP server
  settings controller and registry;
- safe cancellation and user-facing error states;
- UI, presenter, controller, and developer-documentation verification.

### Out of scope

- Creating, cloning, connecting, pulling, switching, or deleting Git libraries.
- Editing a library manifest or a library's shared collection content.
- Importing a library collection into workspace storage.
- Changing proxy MCP server configuration behavior.
- Defining new manifest syntax or changing the general library format.
- Changing the general environment manager outside the values needed by this
  library-backed MCP configuration flow.
- Redesigning MCP runtime protocol behavior or server transport behavior.

### Business entities and interactions

- **Workspace collection**: a collection already available in the user's local
  PyPost workspace and selectable as the local MCP server's source.
- **Connected library**: a user-connected local representation of a Git
  collection library, identified independently from its display name and path.
- **Library manifest**: the library's declaration of available bundled
  collections and variable metadata, including profiles and defaults.
- **Bundled collection**: one collection entry declared by a library manifest.
- **Environment configuration**: the effective values needed by the selected
  collection, together with their validation state and value provenance.
- **Active profile**: the selected named set of library or collection values.
- **Local overlay**: user-specific non-secret overrides, active-profile choice,
  and secret values kept separate from shared library content.
- **MCP server configuration**: the saved local endpoint definition, including
  its collection source and environment association.

### Functional requirements

#### Collection source selection

- The editor must clearly distinguish workspace and library collection sources.
- Switching source must refresh the available collection choices and must not
  retain an incompatible selection from the other source.
- A library-backed selection must remain identifiable as library-backed when
  displayed in the MCP server list and when edited later.
- An empty workspace or library result must be communicated as an unavailable
  choice, not represented by a misleading blank selection.

#### Library and manifest browsing

- The picker must show connected libraries that are currently discoverable.
- The user must be able to inspect the library identity and choose among its
  manifest-declared bundled collections.
- Collection names and descriptions should be available when the manifest
  supplies them; stable identifying information must remain available when a
  friendly name is absent.
- Invalid or unavailable library data must produce a recoverable diagnostic and
  leave the user able to cancel or choose another source.

#### Environment resolution and editing

- The environment view must show the variables relevant to the selected
  library collection and distinguish required values from optional values.
- Values must be resolved in the documented precedence order and the user must
  be able to recognize whether a value comes from a default, active profile,
  local override, or local secret.
- The user must be able to select an active profile where one is available.
- The user must be able to add or change local overrides and secret values.
- Required missing values, type mismatches, and invalid profile references must
  remain visible as validation failures until corrected or cancelled.
- Secret values must be editable and usable without being revealed in clear
  text by the interface's diagnostics or status messages.

#### Validation and persistence

- Save is enabled only for a complete, valid local MCP server configuration.
- Validation must cover the selected library, bundled collection, environment,
  required variables, value types, and references needed by the server row.
- The controller and registry must receive the same valid business selection;
  neither may silently substitute a different collection or environment.
- A successful save must be recoverable through normal MCP server list and edit
  flows after the current dialog closes and after a subsequent application load.
- A failed persistence operation must report failure and preserve the prior
  saved row and prior valid local values.

#### Cancellation and errors

- The user can cancel library browsing, environment preparation, or editing at
  any point before save.
- Cancellation must stop the user-visible operation, remove its busy state, and
  leave no partial selection or partial local overlay update.
- Errors must be actionable and safe, covering at least unavailable libraries,
  unreadable or invalid manifests, missing bundled collections, invalid profile
  or variable values, missing required values, and save failures.
- Error and cancellation handling must keep unrelated MCP server rows usable.

### Non-functional requirements

- The workflow must remain responsive while connected library data and manifests
  are being inspected.
- User feedback must be deterministic enough for UI and presenter tests to
  assert success, cancellation, and error outcomes.
- Shared library files must not be changed by configuring a local MCP server.
- Secrets and sensitive resolved values must not appear in clear text in logs,
  error messages, test output, or developer documentation.
- Existing workspace collection and MCP server behavior must remain compatible
  for users who do not select a library source.

### User scenarios

#### Select a workspace collection

1. The user opens Add or Edit for a local MCP server.
2. The user selects the workspace collection source.
3. The user chooses a workspace collection and environment.
4. The user saves a valid configuration.
5. The server list shows the saved workspace collection and the configuration
   remains available after reopening the editor.

#### Select a library collection with defaults and profile values

1. The user selects the library collection source.
2. The user chooses a connected library and a bundled collection from its
   manifest.
3. The environment view shows manifest defaults and available profiles.
4. The user selects an active profile and reviews the resulting effective
   values.
5. The user supplies any remaining required local values and saves.
6. The MCP server configuration retains the library-backed selection and the
   effective environment association.

#### Override a shared value and provide a secret

1. The user selects a library collection with a required secret and a defaulted
   non-secret variable.
2. The user enters the secret locally and overrides the non-secret value.
3. Validation succeeds without changing the library files.
4. Reopening the configuration reuses the local values while keeping the secret
   masked.

#### Recover from an invalid library or environment

1. The user selects a library whose manifest or bundled collection is unavailable
   or invalid, or leaves a required variable unresolved.
2. The interface identifies the failure and does not save the incomplete row.
3. The user either corrects the issue, chooses another collection/source, or
   cancels.
4. Existing saved MCP configurations are unchanged.

#### Cancel during asynchronous preparation

1. The user starts browsing a connected library or preparing its environment.
2. The interface shows progress and offers cancellation.
3. The user cancels before completion.
4. The operation ends without a partial server row or partial local overlay
   mutation, and the editor remains safe to close or reuse.

## Q&A

### What is the business reason for this story?

It removes the need to duplicate shared library collections into workspace
storage merely to expose them through a local MCP server, while retaining safe
per-user environment configuration.

### What source of truth defines library collections and variables?

The connected library's manifest declares the bundled collections, variable
metadata, defaults, and named profiles. The user's local overlay supplies
per-user overrides, active-profile selection, and secrets.

### What existing repository contracts informed these requirements?

- `pypost/models/library_manager.py` defines connected-library identity and
  user-facing library records.
- `pypost/models/library_manifest.py` defines manifest collections, profiles,
  variable metadata, and resolution results.
- `pypost/core/variable_resolver.py` defines the existing four-level effective
  value precedence and validation concepts.
- `pypost/ui/dialogs/mcp_servers_dialog.py` defines the current local MCP server
  editor and its workspace collection/environment choices.
- `pypost/ui/mcp_server_controller.py` and
  `pypost/core/mcp_server_registry.py` define the current business ownership of
  MCP configuration persistence and runtime references.
- `doc/dev/examples_library_format.md` documents the library manifest and
  bundled collection convention.

### What is the Step 1 handoff?

The requirements are complete for review and handoff to Step 2. Step 2 may
decide how the existing UI, presenter, controller, registry, and library
services cooperate, but it must preserve the business outcomes and boundaries
listed above.
