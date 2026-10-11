# PYPOST-1356: Offline verification and user guidance for Built-in MCP collections

## Task Metadata

- **Implementation language**: Python

## Goals

Users need confidence that a server using a shipped Built-in collection receives updated tools
after an application upgrade, while private workspace copies remain usable and independent.
They also need clear guidance for selecting Built-in, creating editable environment/collection
copies, and understanding which assets follow shipped updates.

This task verifies the already implemented workflow as one connected offline scenario and
documents it. It does not introduce new runtime behavior or silently migrate existing servers.

## User Stories

- As a user configuring MCP, I want to identify the curated Built-in source and its read-only
  collections so that I can start with a maintained shipped integration.
- As a user, I want to create an editable paired environment so that my local settings and
  credentials remain my own rather than modifying a shipped template.
- As a user, I want a Built-in server to expose newly shipped tools after its next start so that
  application upgrades provide maintained integration updates.
- As a user customizing a collection, I want Copy for editing and Save explained so that I can
  choose an independent workspace collection and understand that it stops following updates.
- As a user with an existing examples-library server or workspace copy, I want an explicit
  explanation that my existing setup is not automatically migrated to Built-in.
- As a maintainer, I want deterministic offline verification and developer pointers so that
  the complete workflow can be maintained without external accounts or credentials.

## Definition of Done

1. One automated offline end-to-end scenario covers configuring a Built-in MCP server, creating
   its editable paired environment, and starting the server with the original shipped tools.
2. The same scenario simulates an application upgrade with a newer shipped collection and
   verifies that the next start of the Built-in server exposes the updated tools.
3. The scenario then uses Copy for editing, saves the server against the workspace collection,
   and verifies that the workspace-backed server remains functional with the copied tool set.
   The editable asset is independent of the shipped collection and retains the chosen environment.
4. The scenario runs without external network dependencies, live accounts, or real credentials,
   with explicit finite test timeouts and bounded lifecycle waits.
5. The MCP user guide, or a directly linked feature page, explains Built-in selection and its
   read-only marker, editable paired-environment creation, collection Copy for editing,
   Save/Cancel behavior, and the update responsibility of a private workspace copy.
6. The guidance explains that Built-in servers resolve shipped updates on their next start,
   while editable collection copies no longer receive shipped collection updates.
7. The guidance explains the relation between the curated Built-in source and the examples
   library, and distinguishes copying one collection from the Library Manager's whole-library
   editable-copy action.
8. The guidance explicitly states that existing examples-library servers and existing workspace
   copies are not automatically migrated or converted to Built-in. Existing example-path
   references remain unchanged.
9. Developer guidance identifies the maintained bundle-discovery and curated-view boundaries
   so future contributors can find the workflow's authoritative source.
10. The offline test, documentation lint/link checks, and combined repository quality gate run
    through Make targets. The new verification is green; pre-existing gate failures are
    separately classified and remain linked rather than being hidden or attributed to this task.

## Task Description

The preceding child tasks supply the Built-in source, its lifecycle, and editable-copy actions.
This final child verifies that those capabilities work together across a simulated upgrade and
provides user-facing guidance that distinguishes shipped assets from user-owned copies.

### Scope In

- One connected offline scenario from Built-in configuration and paired-environment copying
  through original startup, simulated shipped update, next-start tool refresh, and a saved
  workspace collection copy that continues working.
- User guidance covering every topic in the Definition of Done, reachable from the MCP guide.
- Developer pointers to the existing bundle-discovery and curated-view responsibilities.
- Bounded automated verification and documentation integrity checks through the Makefile.

### Scope Out

- New MCP runtime behavior, source selection modes, copying capabilities, or migration rules.
- Changing existing example paths, example-path references, shipped integration definitions,
  or user server associations as part of documenting the workflow.
- Real application installation/upgrade services, live remote integrations, accounts, or secrets.
- Automatic merging of shipped changes into private copies.
- Replacing the focused behavior tests already delivered by earlier child tasks.
- Unrelated infrastructure, snapshot, or registry-race repairs.

### Main Entities

- **Built-in source**: The curated read-only view of application-shipped MCP collections.
- **Built-in server**: A saved server association that follows the selected shipped collection.
- **Paired environment copy**: An editable workspace environment created from a shipped template.
- **Shipped update**: A newer application-provided collection containing an updated tool set.
- **Workspace collection copy**: A private editable asset that is independent of shipped updates.
- **Existing examples-library server**: A previously configured library-backed server whose
  association is preserved rather than automatically converted to Built-in.
- **Whole-library copy**: A separate editable library created through Library Manager.
- **User/developer guidance**: Maintained instructions describing the workflow and its boundaries.

### Constraints and Assumptions

The scope follows the [epic decomposition](../PYPOST-1335/decomposition.md) and
[approved parent design](../PYPOST-1336/20-architecture.md). PYPOST-1354 and PYPOST-1355 are
completed dependencies; this task verifies their delivered behavior rather than redesigning it.
The already filed PYPOST-1298/1299/1361/1362 baseline issues remain separately tracked.
No new performance threshold, permission model, or credential storage behavior is introduced.

## Q&A

- **Why an offline scenario?** Maintainers need repeatable confidence in the complete upgrade
  and customization workflow without live services, accounts, or credential exposure.
- **When does a Built-in server receive updated tools?** On its next start against the newer
  shipped collection; no immediate update of an already running server is promised here.
- **Do workspace copies keep following shipped updates?** No. They remain independently
  editable user-owned assets, and the guide must explain that responsibility.
- **Are existing examples-library servers converted?** No. Their associations and existing
  workspace copies remain unchanged unless the user explicitly chooses another configuration.
- **Is Copy for editing the same as copying a library?** No. It creates one workspace collection;
  Library Manager's editable copy creates a separate whole library.
- **Will this task add missing production behavior?** Its intended scope is verification and
  documentation of existing behavior. Any demonstrated acceptance gap must be assessed explicitly
  rather than silently broadening scope or presenting a failing assertion as baseline debt.
