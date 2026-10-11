# PYPOST-1355: Copy for editing a Built-in MCP collection

## Task Metadata

- **Implementation language**: Python

## Goals

Users need to customize the requests and tools in a curated Built-in MCP collection without
changing application-shipped resources or affecting other servers. They need a private editable
workspace copy and a clear explanation that this copy no longer receives shipped updates.

Creating an editable copy must be separate from committing an MCP server configuration. Users
must be able to inspect the copy, cancel the server edit, and retain their new workspace asset
without unexpectedly replacing an existing Built-in server's collection.

## User Stories

- As a developer configuring a Built-in MCP server, I want a **Copy for editing** action so that
  I can customize its collection in my workspace.
- As a developer, I want the copy to preserve every request definition so that customization
  starts from the same collection behavior rather than an incomplete reconstruction.
- As a developer, I want the newly saved copy selected in the open editor so that I can choose
  to save the server against it without further navigation.
- As a developer, I want Cancel to preserve the server's existing Built-in association while
  retaining the workspace copy so that creating an asset does not force reconfiguration.
- As a developer, I want a visible warning that the editable copy no longer receives shipped
  updates so that I understand the maintenance responsibility before choosing customization.
- As a developer, I want repeated copies to receive unique identities and distinct names so that
  they never overwrite each other or existing workspace collections.

## Definition of Done

1. The MCP server editor offers a dedicated **Copy for editing** action when a local Built-in
   collection is selected. The action applies to the selected curated collection.
2. Successful copying creates and persists a private editable workspace collection. Its request
   content and behavior match the selected Built-in collection at creation. Independent
   request identities may differ to keep copied assets safely selectable and editable.
3. The copy has a fresh unique identity and a conflict-safe display name beginning with
   `<Built-in name> (copy)`. Repeated copying uses distinct names, such as an incremental suffix,
   without replacing any existing collection.
4. The copy is visible and editable through the normal workspace collection workflow. Editing
   it cannot modify the shipped collection or another independently created copy.
5. After successful persistence, the open editor switches to the Workspace collection source
   and selects the new copy. Copying alone does not change a persisted server configuration.
6. Cancel preserves an existing server's Built-in association and retains the workspace copy.
   For a new server, Cancel creates no server configuration while retaining the copy.
7. Save commits the edited server against the selected workspace copy. The saved server has a
   workspace collection association with no Built-in or connected-library association remaining.
   Other servers keep their current associations.
8. The editor visibly explains that the workspace copy no longer receives application-shipped
   collection updates. Built-in servers that were not switched retain their existing update
   behavior.
9. The shipped collection file remains byte-identical before and after copying, editing the copy,
   saving the server, or cancelling the editor.
10. A failed copy does not switch the editor to an unavailable collection or alter a persisted
    server association. The failure is reported so the user can retry.
11. Headless automated GUI verification covers copy content/editability, source selection,
    Save/Cancel behavior, repeated identity/name safety, update-note visibility, and source-file
    immutability. Task-added tests and repository quality checks run through the Makefile;
    pre-existing failures remain separately tracked rather than being attributed to this change.

## Task Description

Built-in MCP collections are immutable curated application resources. Users receive newer
versions when the application ships updated definitions. Customization therefore requires an
independent workspace collection; that collection becomes user-owned and stops following the
shipped definition.

This task adds the collection-copy workflow to the MCP server editor. It does not copy an entire
library or create another environment. It preserves the distinction between creating a workspace
asset and choosing which asset a persisted server uses.

### Scope In

- The selected Built-in collection's **Copy for editing** action.
- Persisted, editable workspace copies with preserved request definitions.
- Fresh identity and conflict-safe naming for every copy.
- Workspace source selection and preselection of the successful copy in the current editor.
- Save as the point that commits the server's new workspace association.
- Cancel preserving an existing server's Built-in association while retaining the created asset.
- A visible explanation that the editable copy no longer receives shipped updates.
- Failure handling and automated verification of these boundaries.

### Scope Out

- Copying whole libraries or adding/editing library connection entries.
- Changing the Library Manager's existing library-copy workflow.
- Copying paired environments, already implemented by PYPOST-1354.
- Changing runtime variable resolution or the selected environment.
- Reconfiguring other servers or migrating existing configurations.
- Modifying shipped examples, collection templates, or environment templates.
- Automatically merging future shipped updates into an editable workspace copy.
- The broader end-to-end upgrade scenario and user documentation assigned to PYPOST-1356.

### Main Entities

- **Built-in collection**: A curated read-only collection whose updates are shipped with PyPost.
- **Workspace collection copy**: A persisted user-owned collection with independent identity,
  a distinct display name, and editable request definitions.
- **MCP server editor**: An open configuration draft with a selected source and collection.
- **Persisted MCP server configuration**: The saved association that changes only on Save.
- **Request definition**: The request content and behavior preserved when creating a copy;
  independent identity does not imply changing its behavior.

### Constraints and Assumptions

The workflow follows the business decisions established by the
[epic decomposition](../PYPOST-1335/decomposition.md) and the
[approved parent design](../PYPOST-1336/20-architecture.md), including decision (b): the copy
is retained independently, and switching the persisted server requires Save. Those references
provide implementation guidance for subsequent steps; this document defines business behavior.

All workspace copies remain within the existing private workspace collection workflow. The
selected workspace environment is retained. No new performance threshold or permission model is
introduced by this task.

## Q&A

- **Why does copying not immediately reconfigure the server?** Creating a private asset is a
  separate decision from committing a server change; Save remains the explicit boundary.
- **Why retain the copy after Cancel?** The copy is an independently created workspace asset,
  useful for later editing or another server even if this configuration draft is discarded.
- **Does the editable copy receive later shipped updates?** No. It preserves the chosen starting
  content and then belongs to the user; the editor must communicate this consequence visibly.
- **Must copied requests retain the same identity?** Their content and behavior must remain
  equivalent; identities may change where needed for independent editable workspace assets.
- **Are other servers changed?** No. Only the server whose editor is saved can switch to the copy.
- **Does copying create or replace an environment?** No. Paired-environment copying is a separate
  optional workflow, and this action retains the selected workspace environment.
