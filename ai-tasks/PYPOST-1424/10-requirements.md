# PYPOST-1424: Asynchronous Connection and Remote Manifest Discovery

## Goals

Users opening the Import Collection Variables dialog should see the dialog appear
immediately, even when connected library catalogs are slow to enumerate. Today,
discovering library connections and remote collection manifests blocks dialog
construction on the UI thread, so a sluggish remote library delays the first paint
and interaction. Collection content fetch is already asynchronous
(CollectionFetchWorker from prior work); this task extends that non-blocking
experience to startup discovery.

## User Stories

1. As a workspace user with a slow or high-latency remote library connection, I want
   the Import Collection Variables dialog to open instantly so I can browse local
   workspace collections without waiting on the network.
2. As a workspace user, I want remote library collections to appear in the source
   dropdown once discovery finishes, without freezing the dialog while waiting.
3. As a workspace user, if library discovery fails, I want a clear non-blocking
   indication so I can still work with workspace collections and retry or continue.

## Definition of Done

- Opening the dialog does not wait on library connection listing or remote
  manifest enumeration on the UI thread.
- Workspace collections remain available immediately in the source dropdown.
- Remote library collections populate the dropdown asynchronously after discovery.
- Discovery failures do not crash or permanently freeze the dialog; the user can
  still use workspace sources when present.
- Automated repro covers the non-blocking startup behavior and passes after the fix.
- Existing import-dialog virtualization and remote-fetch behaviors remain intact.

## Task Description

Related tech debt from PYPOST-1415: synchronous `list_connections()` and
`list_manifest_collections()` during dialog initialization. Collection fetching is
already off the UI thread via CollectionFetchWorker (and module extraction in
PYPOST-1423). This task removes the remaining startup latency for remote catalog
discovery so dialog initialization feels instantaneous on slow remotes.

## Q&A

- **Q:** Why is this needed if remote collection *content* fetch is already async?
  **A:** Catalog discovery still runs during `__init__` before the dialog paints;
  users feel that delay every time they open Import even before selecting a remote
  collection.
- **Q:** Programming language?
  **A:** Python (PySide6 Qt UI), matching the existing dialog and worker stack.
