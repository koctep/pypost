# PYPOST-1278: Enhance Library Manager with a manageable list of collection libraries

## Goals

PyPost users may connect multiple collection libraries over time. The current manager makes it
difficult to find a particular library quickly and does not put enough status information or
common management actions where users make their selection. Users must spend unnecessary time
opening libraries one by one, interpreting their state, or leaving the manager to perform basic
file and library-management tasks.

The business goal is to make collection libraries easy to discover, understand, and manage from
one dependable place. Users should be able to identify the library that needs attention, safely
bring it up to date, and connect an existing local library without recreating or moving it. Clear
offline, error, and empty states should reduce confusion and prevent users from taking an unsafe
action based on missing or stale information.

This task enhances the existing Library Manager experience for connected collection libraries.
Remote Git cloning remains supported, and existing library content and synchronization behavior
remain available within the improved management experience.

## Programming Language

- **Implementation language**: Python, as required by the existing PyPost product.

## User Stories

- As a **Collection Author or Library Maintainer**, I want to search and filter my connected
  libraries by recognizable information and status, so that I can find the library I need without
  scanning the entire list.
- As a **Collection Author or Library Maintainer**, I want to sort libraries by name,
  synchronization status, or last modified time, so that I can prioritize routine work and
  libraries needing attention.
- As a **Library Consumer**, I want each library row to show understandable status
  badges, so that I can see whether it is current, has local changes, needs remote updates, or is
  unavailable before I select it.
- As a **Library Maintainer**, I want quick actions for refresh, pull, branch switching, copying
  the local path, and disconnecting or deleting a library, so that routine management does not
  require navigating through several unrelated views.
- As a **Library Maintainer**, I want pull and branch changes to warn me about local changes, so
  that I do not accidentally lose work.
- As a **Library Consumer**, I want to connect an existing local collection-library directory in
  addition to cloning a remote repository, so that I can use libraries that are already on my
  computer without duplicating them.
- As a **Library Consumer working offline**, I want the manager to distinguish unavailable remote
  services from healthy or current libraries, so that I know which local actions remain safe and
  which synchronization actions must wait.
- As a **Library Maintainer**, I want actionable inline diagnostics and clear status meanings, so
  that I can understand a problem and choose the next safe action from the manager.

## Functional Requirements

### FR-1: Manageable library list

1. The Library Manager shall show every currently connected collection library in a single list.
2. Each row shall show the library's display name. If no display name exists, it shall show the
   stable library identifier.
3. Each row shall expose, directly in the list, these status details:
   - synchronization state;
   - local-change or clean state;
   - `Offline`, `Unavailable`, `Invalid`, or `Error` condition when present; and
   - the last modified value, or `Unavailable` when it cannot be established.
4. The user shall be able to enter search text to narrow the list by library display name or
   identifier. Search shall be case-insensitive and shall update the visible results as the query
   changes.
5. The manager shall use the following complete status vocabulary for filtering. A row has one
   synchronization status and may also have condition statuses. The user may select one status
   filter at a time; no selected filter shows all rows.

   **Synchronization statuses, in canonical ascending order from most attention needed to least:**

   1. `Checking` — the current status is being checked.
   2. `Unknown` — no current synchronization result is available.
   3. `Local changes and remote updates` — both kinds of changes are present.
   4. `Local changes` — local changes are present and remote updates are not confirmed.
   5. `Remote updates available` — remote updates are available and no local changes are known.
   6. `Locally ahead` — local commits are ahead of the remote source.
   7. `No remote source` — the library has no configured remote source.
   8. `Current` — the local library matches its remote source and has no local changes.

   **Condition statuses:** `Offline` means the remote source cannot be reached; `Unavailable`
   means the local path or required library information cannot be read; `Invalid` means the
   library information is incomplete or invalid; and `Error` means the latest requested operation
   failed. When any of these conditions prevents a current synchronization result, the
   synchronization status is `Unknown`. A condition status does not replace the synchronization
   status. The filter menu lists condition statuses in this order: `Offline`, `Unavailable`,
   `Invalid`, `Error`. `Stale` is a marker, not a filter value. A filter matches a row when the row
   has the selected exact label.
6. The user shall be able to sort the list in ascending or descending order by:
   - library name;
   - synchronization status; or
   - last modified time.
7. Sorting and filtering shall be deterministic:
   - Name sorting compares case-insensitive display names, using the stable library identifier as
     the name when no display name exists. Ties use stable library identifiers in ascending order.
   - Synchronization-status sorting uses the canonical status order in item 5. Ties use
     case-insensitive display names in ascending order, then stable library identifiers in ascending
     order.
   - Last-modified sorting compares timestamps. Missing timestamps always appear after timestamped
     rows. Ties use case-insensitive display names in ascending order, then synchronization status
     order, then stable library identifiers in ascending order.
   - The selected sort direction reverses only the primary sort value; all tie-breakers remain in
     ascending order. Filtering preserves the active sort order. A selected library remains selected
     by stable identifier if it remains in the filtered list; otherwise selection is cleared and
     guidance is shown.
8. Selecting a row shall show the selected library's details and available actions. If no row is
   selected, the manager shall show guidance rather than stale details for a previously selected
   library.

### FR-2: Status badges and state presentation

1. The manager shall present a concise, human-readable status for each connected library without
   requiring the user to open its details.
2. The status presentation shall distinguish all statuses defined in item 5:
   - `Current`;
   - `Local changes`;
   - `Remote updates available`;
   - `Locally ahead`;
   - `Local changes and remote updates`;
   - `No remote source`;
   - `Offline`, `Unavailable`, `Invalid`, and `Error`; and
   - `Checking` or `Unknown`.
3. Status text shall not rely on color alone. The state shall remain understandable through text,
   icons, or accessible labels.
4. If the manager displays last-known information after a failed check, it shall show the time of
   the last successful check and a `Stale` marker.
5. A status refresh shall update the affected library's badges and details. A failed refresh shall
   not incorrectly present the library as current.
6. The selected-library view shall continue to provide enough context to understand the active
   branch or `No active branch`, local changes, synchronization position, and most recent known
   modification or update.

### FR-3: Quick library operations

1. The selected library shall provide quick access to:
   - refresh status;
   - pull or synchronize remote changes;
   - switch branch;
   - copy the local library path; and
   - disconnect or delete the library. The list row may provide the same actions.
2. Actions shall be associated with the library on which they operate, and unavailable actions
   shall be disabled or accompanied by a clear explanation.
3. Copying the path shall place the exact local path on the clipboard and provide confirmation.
4. Pulling or switching branch shall check for local changes first. If local changes could be
   affected, the manager shall explain the risk, list the affected files when they can be
   identified, or state that the file list is unavailable, and require the user to cancel or
   address the changes before continuing.
5. The manager shall show a visible in-progress state while an operation is running and shall
   prevent an accidental duplicate submission of that same operation.
6. On success, the list and selected-library details shall reflect the new state. On failure, the
   affected library shall retain a truthful diagnostic state and the user shall receive guidance
   about the next action.
7. Disconnect and delete shall be separate, explicit choices with source-specific behavior:
   - **Disconnect** removes the library connection from the managed list and preserves the complete
     local directory and every file for both cloned libraries and in-place registered directories.
   - **Delete** is offered only for a cloned library. After confirmation, it removes that clone's
     managed local directory and associated local library data; it does not affect the remote
     source.
   - A registered local directory is never deleted or modified by the manager. It has no destructive
     delete action; the user disconnects it when they want to remove it from the managed list.
8. Both disconnect and delete confirmations shall identify the library name, source type, and exact
   local path. The disconnect confirmation shall state that all local files will be retained. The
   cloned-library delete confirmation shall state that the local clone and associated local data
   will be permanently removed, including local changes in that clone. Canceling either confirmation
   shall leave the connection and all local files unchanged.

### FR-4: Add or connect library options

1. The manager shall offer both of these ways to add a library:
   - clone a new library from a remote Git repository into a managed local copy; and
   - connect an existing local directory in place.
2. Connecting a local directory shall register that directory in place; it shall not silently move,
   copy, or overwrite the user's existing files.
3. Before registration, the manager shall validate that the selected directory is a recognizable
   collection library and shall explain what is missing or invalid when it is not.
4. The manager shall reject or clearly resolve duplicate connections, including a directory that is
   already connected or a library identity that conflicts with an existing entry.
5. A successful clone or local connection shall add the library to the list and make it available
   for selection and management.
6. Canceling either add flow shall make no library or file-system changes.

### FR-5: Empty, offline, and diagnostic states

1. When no libraries are connected, the manager shall show an empty-state explanation and clear
   entry points for cloning a remote library or connecting a local directory.
2. When search or filtering produces no matches, the manager shall distinguish that result from an
   empty library collection and offer a way to clear the active search or filter.
3. When a remote source cannot be reached, the manager shall identify the library as `Offline`,
   retain the last successfully read local name, path, modification value, and local-change state,
   show when that information was checked with a `Stale` marker, and explain which actions require
   connectivity. It shall not label the synchronization state `Current` without a successful
   current check.
4. When library metadata or status cannot be read, the manager shall show an inline, actionable
   diagnostic for that library while keeping other library rows usable.
5. Diagnostics shall use plain language, identify the affected operation, and suggest a next step
   such as retrying, checking the path, checking credentials, or resolving local changes.
6. User-facing diagnostics shall not expose secret values, authentication material, or raw internal
   error output.

### FR-6: Guidance and documentation

1. User-facing and developer-facing documentation shall describe the enhanced list, exact status
   meanings and sort order, quick actions, source-specific disconnect and delete behavior,
   local-directory connection, and offline/error behavior.
2. Documentation shall state that a canceled operation leaves the affected connection and local
   files unchanged, and shall remain consistent with the delivered user-visible behavior.

## Non-Functional Requirements

- **NFR-1 Responsiveness:** Searching, filtering, sorting, selection, and badge rendering shall
  remain responsive for the maximum supported number of connected libraries. Operations that may
  access disk or a remote source shall not make the application appear frozen.
- **NFR-2 Data safety:** No pull, branch switch, disconnect, or delete action shall silently discard
  local user work. Risky operations shall provide a clear confirmation or local-change safeguard.
- **NFR-3 Truthful state:** The manager shall never label a library as current when its status is
  unknown or stale because a check failed. State transitions shall be understandable before,
  during, and after an operation.
- **NFR-4 Accessibility:** All important states and actions shall be understandable without relying
  only on color, and the list, filters, actions, confirmations, and diagnostics shall be usable
  with the application's supported keyboard and assistive-technology conventions.
- **NFR-5 Cross-platform presentation:** The experience shall remain usable on supported desktop
  platforms and in supported light and dark themes, including readable status badges and dialogs.
- **NFR-6 Privacy and security:** Paths and diagnostics may identify the local library but shall not
  reveal credentials, tokens, private keys, or other secret values.

## Scope Boundaries

### In scope

- Improving the connected-library list with search, state filters, sorting, selection behavior, and
  directly visible badges.
- Making refresh, pull, branch switching, path copying, disconnect, and delete easy to reach and
  safe to use.
- Adding an option to connect a valid existing local collection-library directory.
- Preserving remote Git cloning as an add-library option.
- Improving empty, in-progress, stale, offline, and error guidance in the Library Manager.
- Documentation updates that explain the enhanced management experience.

### Out of scope

- Replacing or redesigning the underlying Git operations, authentication providers, or remote Git
  hosting services.
- Changing the collection-library manifest format, collection serialization, or local secret and
  override storage rules.
- Building a merge-conflict editor, general-purpose Git client, or collection editing workflow.
- Changing unrelated application navigation, collection browsing, request execution, or workspace
  behavior except where the existing Library Manager must report the result of a library action.
- Moving or copying an existing local directory as part of connecting it.
- Adding new remote repository providers or credential types beyond existing product support.

## Business Entities and Interactions

- **Collection Library**
  - Business meaning: A named set of collections that a user has made available to PyPost.
  - Key attributes: Display name, stable identifier, local path, source type (`Cloned managed
    copy` or `Registered local directory`), active branch or `No active branch`, and current
    availability.
- **Library Connection**
  - Business meaning: The user's relationship between PyPost and a local or remote-backed
    library.
  - Key attributes: Connected, disconnected, or pending state; source location; validation result;
    and lifecycle actions.
- **Library Status**
  - Business meaning: The latest understandable assessment of a library's local and remote state.
  - Key attributes: One synchronization status from FR-1, condition statuses, last checked, stale
    marker, and last modified value or `Unavailable`.
- **Library List Entry**
  - Business meaning: The row through which a user finds and acts on one library.
  - Key attributes: Searchable identity, sortable values, status badges, selection, and quick
    actions.
- **Library Operation**
  - Business meaning: A user-requested action that changes or inspects a library.
  - Key attributes: Refresh, pull, branch switch, copy path, clone, connect, disconnect, or delete;
    preconditions, progress, result, and diagnostic.
- **Local Change Safeguard**
  - Business meaning: A user-protection interaction before an operation could affect local work.
  - Key attributes: Affected files when known, risk explanation, cancel outcome, and path to
    address the changes.
- **Library Diagnostic**
  - Business meaning: A user-facing explanation of an unavailable, invalid, stale, or failed
    library state.
  - Key attributes: Affected library, operation, severity/state, last known information, and
    recommended next action.
- **Library Manager User**
  - Business meaning: A person who consumes, authors, or maintains collection libraries.
  - Key attributes: Finds libraries, interprets status, invokes safe operations, and responds to
    guidance.

The primary interaction is: a user searches, filters, or sorts the collection of Library List
Entries; selects one; reviews its Library Status; and invokes a Library Operation. The operation
may update the Library Connection and Status, trigger a Local Change Safeguard, or produce a
Library Diagnostic. The list must continue to represent unaffected libraries when one library
cannot be read or synchronized.

## Constraints and Assumptions

- Python is the implementation language for this task.
- Existing collection-library and Git capabilities remain the foundation for remote cloning,
  status, pulling, and branch management. This task defines the management experience around them.
- An existing local directory is connectable only when it is a valid, readable collection library
  according to the product's existing library rules.
- Connecting a local directory records a reference to the directory in its current location. Users
  remain responsible for its file permissions and continued availability.
- A local library may be usable when its remote source is unavailable. Remote-dependent actions
  must be identified as unavailable rather than treated as successful.
- Last modified means the most recent known modification to the library's local content or
  synchronized library state, not the time at which the manager was opened. If that value cannot
  be established, it is shown as `Unavailable` rather than as an invented timestamp.
- Disconnect preserves the complete local directory for both source types. Delete is available only
  for a cloned managed copy, removes that local copy and associated local library data after
  explicit confirmation, and never removes the remote source. A registered local directory is
  never deleted or modified by the manager.
- The manager can display a stale last-known status after a failed check only when it is clearly
  marked stale and paired with the failure guidance.
- Network availability, Git credentials, file permissions, and local path availability are external
  conditions. The manager must explain their effect but cannot guarantee them.

## Definition of Done

The task is complete when all of the following business outcomes are true:

1. A user can see all connected collection libraries in one manager list and find a library by
   searching or filtering its identity or status.
2. A user can sort the list by name, synchronization status, and last modified time in either
   direction, with predictable results.
3. Each library row exposes readable badges for local changes, synchronization, availability, and
   last-known status and modification information without requiring the detail view.
4. A user can refresh, pull, switch branch, copy a library path, disconnect, or delete from the
   manager, with the action applied to the intended library.
5. Pull and branch-switch workflows protect local changes; disconnect and delete clearly distinguish
   preservation from destruction and require the appropriate confirmation.
6. The manager offers both remote cloning and connecting an existing valid local directory, does
   not move or overwrite files during connection, and handles duplicates and invalid directories
   with actionable guidance.
7. Empty results, no-library state, offline or stale status, invalid metadata, operation progress,
   cancellation, and operation failures are distinguishable and understandable.
8. User-facing diagnostics do not expose secret values or raw internal error output.
9. Relevant user-facing and developer-facing documentation describes how to use the enhanced
   Library Manager, interpret its states, and understand source-specific deletion behavior.
10. The requirements are reviewed and accepted by the Step 1 acceptance-gate owner. This execution
    leaves Step 1 at `[/]` for that acceptance.

## Task Description

### Problem

The Library Manager supports connected collection libraries, but a growing list is difficult to
scan and manage. Important state is not sufficiently visible at the point where users choose a
library, common actions are not uniformly easy to reach, and users cannot add a local directory
without using the remote-clone path. Weak empty, offline, and error guidance makes it harder to
know whether a library is healthy, stale, or safe to operate on.

### Desired outcome

Provide a dependable management surface where users can locate a library, understand its state,
take routine actions safely, add either remote or local libraries, and recover from common errors
with clear guidance. The enhancement should make a multi-library workspace manageable without
requiring users to resort to external file or Git workflows for routine library administration.

### Current-context boundaries

The existing product already has a Library Manager, collection-library representations, remote Git
library operations, and library status concepts. PYPOST-1278 improves how those capabilities are
found and understood in the manager. It does not redefine the underlying library format or Git
behavior, and it does not introduce general Git conflict-resolution or collection-editing tools.

## Q&A

- **Why is this enhancement needed?**

  To reduce the time and risk involved in finding, interpreting, synchronizing, and maintaining
  multiple collection libraries.

- **Does connecting a local directory copy or move its files?**

  No. It registers the directory in its existing location and must not silently copy, move, or
  overwrite it.

- **What is the difference between disconnect and delete for a cloned library?**

  Disconnect removes the library from PyPost's managed list and retains the complete local clone.
  Delete removes the clone's local directory and associated local library data only after explicit
  confirmation. It does not affect the remote repository.

- **What happens when a registered local directory is disconnected or deleted?**

  Disconnect removes only the managed connection and retains the directory and every file. The
  manager never offers a destructive delete action for an in-place registered directory and never
  deletes or modifies it.

- **What should users see when the network is unavailable?**

  The library is labeled `Offline`. Last-known local information remains visible with its last
  successful check time and a `Stale` marker, and remote-dependent actions explain why they cannot
  proceed.

- **What does last modified mean?**

  It is the most recent known modification to local library content or synchronized library state,
  not the time the manager was opened. If it cannot be established, the value is `Unavailable`.

- **Can users still clone remote Git repositories?**

  Yes. Remote cloning remains an add-library option alongside connecting an existing local
  directory.

- **What happens for an invalid or duplicate local directory?**

  The directory is not registered silently. The user receives a specific explanation and guidance
  to choose a valid directory or resolve the duplicate.

- **Are Git internals and manifest changes part of this task?**

  No. Existing Git, authentication, collection-library format, and local overlay behavior are
  outside this enhancement's scope.

- **What happens to a library with local changes before pull or branch switch?**

  The user is warned about the risk and affected files when they can be identified, or told that
  the file list is unavailable, and must cancel or address the changes before continuing.

## References

- `doc/dev/library_manager_ui.md` — existing Library Manager capabilities and terminology.
- [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223) — existing Library Manager UI
  and Git flow.
- [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222) — existing Git library service.
