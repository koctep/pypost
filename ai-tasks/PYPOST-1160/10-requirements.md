# PYPOST-1160: Collections WebSocket menu parity

## Goals

Saved WebSocket profiles already appear in the Collections sidebar and open
in the workspace when the user left-clicks them. The sidebar context menu
that HTTP requests enjoy — **New tab**, **Rename**, and **Delete** — does
not work for WebSocket rows today: right-clicking a WebSocket profile
produces no actionable menu.

User-facing documentation (`doc/user/collections.md`) already tells
collections users they can right-click an item and choose **New tab** to
open a separate editable copy. That promise is broken for WebSocket
profiles. Rename and delete are likewise unavailable from the tree even
though the product can persist WebSocket items in collections.

This story (WS-TM-4 under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) delivers
**menu parity**: WebSocket collection items get the same sidebar context
actions HTTP requests have, with WebSocket-appropriate tab behavior. It
depends on WS-TM-2
([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)) so blank
WebSocket workspace tabs and the WebSocket editor stack already exist.

The business goal is trustworthy Collections management for WebSocket
workflows: organize, duplicate, rename, and remove profiles from the
sidebar without workarounds, and keep the workspace consistent when a
profile disappears from the tree.

## User Stories

- As a **collections user**, I want to right-click a WebSocket profile and
  choose **New tab**, so I can work on a separate copy without losing the
  tab I already have open.
- As a **collections user**, I want **New tab** on a WebSocket profile to
  give me my own live session, so connecting or sending in one tab does
  not affect another tab opened from the same saved profile.
- As a **collections user**, I want to **Rename** a WebSocket profile from
  the sidebar, so the display name in the tree and in any open workspace
  tabs stays accurate.
- As a **collections user**, I want to **Delete** a WebSocket profile from
  the sidebar (with confirmation), so I can remove profiles I no longer
  need.
- As a **collections user**, I want workspace tabs that show a deleted
  WebSocket profile to close or warn me before closing, so I am not left
  editing a profile that no longer exists in Collections.
- As a **collections user**, I want deleting a **collection** that contains
  WebSocket profiles to remove those profiles and affect their open tabs
  the same way deleting a collection with HTTP requests does today.
- As a **collections user**, I want **Export Collection…** on a WebSocket
  row to export the parent collection (same as on a request row), so I do
  not lose export access because the child item is a WebSocket profile.

## Definition of Done

PYPOST-1160 is done when:

1. Right-clicking a WebSocket profile in the Collections tree opens a
   context menu with **New tab**, **Export Collection…**, **Rename**, and
   **Delete** (matching the HTTP request row menu).
2. Choosing **New tab** on a WebSocket profile always opens a **new**
   workspace tab with a separate editable copy of that profile. It does
   **not** merely focus an already-open tab for the same saved profile
   (left-click may still focus an existing tab; **New tab** must not).
3. Each tab opened via **New tab** owns its own connection state: Connect,
   Disconnect, stream, and composer activity in one tab do not drive
   another tab opened from the same profile.
4. Edits in a **New tab** copy do not change the saved profile in
   Collections or the content of other open tabs until the user explicitly
   saves (save itself is
   [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161)).
5. **Rename** on a WebSocket profile starts inline rename in the tree,
   persists the new name, updates the tree label (`ws <name>`), and
   updates titles of open workspace tabs that reference that profile.
6. **Delete** on a WebSocket profile asks for confirmation, removes the
   profile from Collections and the tree, and closes or prompts on every
   workspace tab bound to that profile id.
7. When a tab bound to a deleted profile has unsaved edits and/or an active
   WebSocket connection, delete-tab handling **warns** the user and allows
   cancel or proceed before the tab is closed (HTTP request delete today
   closes matching tabs without this extra warning; WebSocket needs it
   because live sessions and unsaved draft edits are at risk).
8. Deleting a **collection** that contains WebSocket profiles removes those
   profiles and triggers the same open-tab closure rules as item (6)–(7) for
   each affected profile.
9. Left-click open behavior for saved WebSocket profiles is unchanged:
   opening a profile that already has a tab may focus that tab instead of
   creating a duplicate.
10. **New tab** from the Collections context menu is counted in product
    telemetry as a new-tab action from the collections context, attributed
    to the WebSocket protocol (alongside existing HTTP collections **New
    tab** attribution).
11. Rename and delete actions on WebSocket items continue to emit the same
    class of collection action metrics already used for HTTP items and
    collections.

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

WebSocket profiles are first-class collection children: they appear in the
sidebar (`ws <name>`), left-click opens them in the WebSocket editor, and
the product can rename or delete them at the persistence layer. The
**sidebar context menu path** was built for HTTP requests and collection
folders only. WebSocket rows are not recognized as menu targets, so
right-click does nothing useful.

HTTP request rows already demonstrate the expected product behavior:

| Action | HTTP request today | WebSocket today |
| --- | --- | --- |
| Right-click menu | **New tab**, **Export Collection…**, **Rename**, **Delete** | Menu does not appear (item not resolved) |
| **New tab** | Opens a separate tab with an independent editable copy | Not offered |
| **Rename** | Inline rename; tree label and open tab titles update | Not offered |
| **Delete** | Confirmed removal; matching open HTTP tabs close | Not offered |
| Left-click | Opens/focuses in workspace | Opens/focuses (may deduplicate by profile) |

Collections documentation already describes **New tab** for “a request or
WebSocket profile.” Users following that guide hit a dead end on WebSocket
rows. Teams storing live-stream or MCP-oriented WebSocket profiles in
collections cannot manage them from the tree the way they manage HTTP
requests.

### Business Need

WebSocket is a supported collection item type. Sidebar management actions
must match user expectations set by HTTP requests and by `doc/user/collections.md`:

- **Duplicate work in parallel** — open another tab from the same saved
  profile without disturbing the first session.
- **Organize names** — rename profiles where they live in the tree.
- **Retire profiles** — delete obsolete endpoints and keep the workspace
  from showing ghosts of removed items.
- **Safe teardown** — deleting a profile must not leave silent live
  connections or unsaved edits on a tab whose backing item is gone.

Without this story, the Tab Protocol Modes epic
([PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) still
fails FR-4 (Collections WebSocket menu parity) from
`ai-tasks/PYPOST-1156/10-requirements.md`.

### Scope (this task)

- Recognize WebSocket profiles as context-menu targets in the Collections
  tree (parity with HTTP requests and collections).
- **New tab** for WebSocket profiles: always a new workspace tab with an
  isolated copy and independent live session.
- **Rename** and **Delete** for WebSocket profiles from the context menu,
  including tree refresh and open-tab title updates on rename.
- Open-tab lifecycle when a WebSocket profile (or a collection containing
  WebSocket profiles) is deleted: close affected tabs; prompt when a tab has
  unsaved edits and/or an active connection.
- **Export Collection…** remains available on WebSocket rows (parent
  collection export), consistent with request rows.
- Collection rename/delete metrics and new-tab telemetry for WebSocket
  context-menu actions.

### Out of Scope

- Blank WebSocket draft tab creation —
  [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) (dependency,
  not delivered here).
- Protocol picker on `Ctrl+N` / **+** —
  [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157).
- Close-last-tab picker —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- **Save** / **Save As** for WebSocket drafts, overwrite prompts, and
  post-save tab identity —
  [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161).
- Context-aware WebSocket keyboard shortcuts —
  [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162).
- End-user documentation updates —
  [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) (though
  this story makes `collections.md` accurate).
- Changing left-click open/deduplicate behavior for saved profiles.
- Changing how blank WebSocket drafts open or close.
- History replay, MCP probe runtime, or import/export format changes beyond
  what already works once the menu resolves WebSocket items.
- HTTP request delete behavior (HTTP tabs still close without the extra
  WebSocket session/unsaved warning unless a separate story says otherwise).

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Collection** | Folder grouping HTTP requests and WebSocket profiles. |
| **WebSocket profile** | Saved connection configuration (URL, handshake, presets, MCP fields) stored under a collection. |
| **HTTP request** | Saved HTTP call stored under a collection; reference behavior for menu parity. |
| **Collections tree row** | Sidebar item the user right-clicks; shows `ws <name>` for WebSocket profiles. |
| **Context menu** | Right-click actions: **New tab**, **Export Collection…**, **Rename**, **Delete**. |
| **Workspace tab** | Editor strip tab showing a WebSocket profile (saved or copied). |
| **Isolated tab copy** | A **New tab** instance: same saved profile identity for lookup, but independent editor content and live session from other tabs. |
| **Open-tab lifecycle** | What happens to workspace tabs when their backing profile is deleted from Collections. |

### Functional Requirements

#### FR-1: WebSocket profiles are menu targets

- FR-1.1 Right-clicking a WebSocket profile row opens the context menu (no
  silent no-op).
- FR-1.2 The menu offers **New tab**, **Export Collection…**, **Rename**,
  and **Delete**, in the same order as for an HTTP request row.
- FR-1.3 Right-clicking a collection folder or HTTP request row behaves as
  today (no regression).

#### FR-2: New tab opens an isolated WebSocket copy

- FR-2.1 **New tab** always inserts a **new** workspace tab; it must not only
  focus an existing tab for the same saved profile id.
- FR-2.2 The new tab loads a **copy** of the profile configuration (URL,
  handshake fields, presets, sequences, MCP-related fields visible in the
  editor) so changes in that tab are not shared with other tabs until save.
- FR-2.3 Each tab opened via **New tab** maintains its **own** Connect /
  Disconnect state and message stream; no shared live session across tabs.
- FR-2.4 Opening multiple **New tab** copies from the same profile is
  allowed; each is independent.
- FR-2.5 **New tab** is recorded as a collections-context new-tab action
  attributed to WebSocket.

#### FR-3: Rename WebSocket profiles from the tree

- FR-3.1 **Rename** starts inline edit on the tree row (same interaction as
  HTTP requests and collections).
- FR-3.2 Committing a non-empty name persists the new profile name and
  updates the sidebar label to `ws <new name>`.
- FR-3.3 Empty or whitespace-only names are rejected with the same error
  feedback HTTP rename uses.
- FR-3.4 Open workspace tabs showing that saved profile update their visible
  title to reflect the new name.
- FR-3.5 Cancelling rename restores the previous tree label without
  persisting a change.

#### FR-4: Delete WebSocket profiles from the tree

- FR-4.1 **Delete** shows a confirmation dialog naming the profile.
- FR-4.2 Confirming removes the profile from the collection data and the
  sidebar tree.
- FR-4.3 Cancelling leaves the profile and tree unchanged.
- FR-4.4 After a successful delete, every workspace tab bound to that
  profile id is closed or the user is prompted first per FR-5.
- FR-4.5 Deleting a collection removes all contained WebSocket profiles and
  applies FR-4.4 / FR-5 to each affected open tab.

#### FR-5: Open tabs when a profile is deleted

- FR-5.1 Tabs showing a deleted WebSocket profile must not remain open as
  if the profile still exists in Collections.
- FR-5.2 If a affected tab has **no** unsaved edits and **no** active
  WebSocket connection, it closes silently (same practical outcome as HTTP
  request delete today).
- FR-5.3 If a affected tab has unsaved edits and/or an active connection,
  the user sees a warning explaining that the profile was deleted and may
  lose work or disconnect; they can **cancel** (tab stays) or **proceed**
  (tab closes and connection ends).
- FR-5.4 When the last workspace tab is closed as a result of profile
  deletion, the workspace follows the same empty-workspace rule already in
  effect for HTTP tab closure (no new behavior invented here beyond using
  the current product fallback).
- FR-5.5 Unrelated workspace tabs (other profiles, HTTP tabs, blank drafts)
  remain open.

#### FR-6: Left-click behavior unchanged

- FR-6.1 Left-clicking a saved WebSocket profile still opens it in the
  workspace using the existing focus-if-already-open rule for that profile
  id.
- FR-6.2 **New tab** and left-click remain distinct entry points with
  distinct tab-creation rules (FR-2 vs FR-6).

### Non-Functional Requirements

- **NFR-1 Consistency:** WebSocket sidebar actions must feel the same as
  HTTP request actions except where WebSocket live-session safety requires
  an extra delete prompt (FR-5.3).
- **NFR-2 Trust:** Documentation in `doc/user/collections.md` that mentions
  **New tab** for WebSocket profiles must match shipped behavior after this
  story (full doc pass remains PYPOST-1163).
- **NFR-3 Metrics:** Rename, delete, and collections-context **New tab**
  actions on WebSocket items are observable in the same telemetry families
  as HTTP collection actions, with protocol attribution on new-tab events.
- **NFR-4 Safety:** Deleting a profile must not leave orphaned live
  WebSocket connections tied to a removed collection item without user
  acknowledgment when a session is active.

### Constraints and Assumptions

- Parent epic:
  [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on WS-TM-2:
  [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) (WebSocket
  workspace tabs and editor must exist).
- Research:
  [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156)
  FR-4 (Collections WebSocket menu parity).
- The product can already store WebSocket profiles in collections, rename
  them, and delete them at the persistence layer; users cannot reach those
  actions from the sidebar context menu today.
- Save-to-collection after editing a copied tab is
  [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161); this
  story does not add save shortcuts or save-on-close.
- HTTP and WebSocket remain separate editor experiences; menu parity does
  not merge editors.
- **Export Collection…** on a WebSocket row exports the **parent**
  collection (same as on a request row), not an individual WebSocket profile.

## Q&A

- **Why does WebSocket delete prompt but HTTP delete does not?**
  WebSocket tabs can hold active connections and unsaved draft edits that
  are costly to lose silently. Jira acceptance criteria require close or
  prompt; FR-5.3 implements prompt only when there is something at risk.
- **Does New tab create a new Collections item?**
  No. It opens another workspace tab with a copy of the saved profile, same
  as HTTP **New tab**. Persisting changes is PYPOST-1161.
- **If I already have a tab open and choose New tab, do I get two tabs?**
  Yes. **New tab** always adds a tab. Left-click may focus the existing
  one; **New tab** must not.
- **Will rename change the profile id?**
  No. Only the display name changes; the profile id used for tab binding
  stays the same.
- **What happens to MCP tools when I delete an exposed WebSocket profile?**
  The profile is removed from Collections; MCP tool refresh already
  listens to collection changes. Agent runtime behavior is unchanged by
  this story.
- **Does this story update user docs?**
  Not directly — PYPOST-1163. This story makes the existing collections.md
  **New tab** claim true for WebSocket.
- **Is Export Collection in scope?**
  Yes as inherited parity: request rows already offer it; WebSocket rows
  must not lose it once the menu works.

## References

- [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — research / FR-4
- [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) — WS-TM-2 dependency
- `ai-tasks/PYPOST-1156/10-requirements.md` — epic FR-4
- `ai-tasks/PYPOST-1156/20-architecture.md` — WS-TM-4 architecture notes
- `doc/user/collections.md` — user expectation for **New tab**
