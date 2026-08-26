# PYPOST-1161: WebSocket save-to-collection flow

## Goals

Users can already compose WebSocket profiles in workspace tabs — blank drafts
([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)) and isolated
copies opened from Collections
([PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160)) — but they
cannot **persist** those profiles to a collection the way HTTP requests can.
User-facing documentation (`doc/user/collections.md`, `doc/user/hotkeys.md`)
already describes **Save** and **Save As…** for WebSocket profiles with the
same shortcuts as HTTP (`Ctrl+S` / `Ctrl+Shift+S`). That promise is broken:
there is no profile-level save path from the WebSocket editor today.

This story (WS-TM-5 under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) closes the
**compose → save → collection item** loop for WebSocket. It delivers parity
with the HTTP save experience so users can organize live-stream and
MCP-oriented WebSocket profiles in Collections, reopen them across sessions,
and expose them to agents after save.

The business goal is a trustworthy, symmetric Collections workflow: a user who
creates or edits a WebSocket profile in a tab can save it once and find it in
the sidebar — with the workspace tab, Collections tree, session restore, and
MCP tool list all reflecting the persisted profile.

## User Stories

- As a **WebSocket user**, I want to **Save** a WebSocket profile from my
  workspace tab to a collection, so I can reuse the endpoint configuration
  later without recreating it.
- As a **WebSocket user**, I want **Save** on a blank draft to ask me for a
  profile name and target collection (or let me create a new collection), so
  first-time save works the same way as saving a new HTTP request.
- As a **WebSocket user**, I want **Save** on a profile that already exists in
  Collections to update that saved item in place, so edits in the tab become
  the new canonical version.
- As a **WebSocket user**, I want **Save As…** to always create a **new**
  collection profile and leave the original unchanged, so I can fork variants
  of the same endpoint safely.
- As a **WebSocket user**, I want overwrite and conflict prompts to match HTTP
  save behavior (including my **Confirm before overwrite** setting), so I am
  not surprised when replacing an existing profile or a newer on-disk version.
- As a **WebSocket user**, I want the Collections sidebar to show my saved
  WebSocket profile immediately after save (as `ws <name>`), so I can confirm
  where it landed without hunting.
- As a **WebSocket user**, I want my workspace tab title and profile identity
  to align with the saved item after save, so I know which collection entry
  the tab represents.
- As a **WebSocket user**, I want a WebSocket profile I saved in this session
  to be included in session restore on the next launch, so I pick up where I
  left off (unsaved drafts remain excluded until first save).
- As a **MCP user**, I want MCP tool discovery to refresh after I save a
  WebSocket profile with MCP exposure enabled, so agents see the updated
  profile without restarting PyPost.
- As a **WebSocket user**, I want **Save** and **Save As…** reachable from the
  **Actions** menu and via `Ctrl+S` / `Ctrl+Shift+S` while a WebSocket tab is
  focused, as documented in `doc/user/hotkeys.md`.

## Definition of Done

PYPOST-1161 is done when:

1. A WebSocket workspace tab offers **Save** and **Save As…** through the
   **Actions** menu (alongside Connect-oriented actions), matching the HTTP
   editor's save entry points.
2. `Ctrl+S` saves the active WebSocket profile; `Ctrl+Shift+S` runs **Save
   As…** — both work when a WebSocket tab is focused.
3. **Save** on a profile **not yet in any collection** opens a save dialog:
   the user supplies a profile name, picks an existing collection or creates a
   new one, and confirms. The profile is persisted and appears in the
   Collections tree.
4. **Save** on a profile **already stored in a collection** updates that
   saved item in place (same profile identity), including all editor-visible
   configuration: name, URL, handshake fields (params, headers, subprotocols),
   message presets, test sequences, and MCP-related fields.
5. When **Confirm before overwrite** is enabled in Settings, **Save** on an
   existing collection profile asks for confirmation before replacing it —
   same expectation as HTTP save.
6. When the on-disk saved version is newer than what the tab last loaded,
   **Save** warns before overwriting (stale-version protection), matching HTTP
   save behavior.
7. **Save As…** always creates a **new** collection profile with a **new**
   identity; the original saved profile (if any) and other open tabs bound to
   it are unchanged.
8. Cancelling any save dialog or overwrite prompt leaves the tab and
   Collections data unchanged.
9. After a successful **Save** or **Save As…**, the Collections sidebar shows
   the WebSocket profile under the target collection (`ws <name>`), and the
   target collection is expanded if the product already expands collections on
   save for HTTP items.
10. After a successful save, the workspace tab title reflects the saved profile
    name, and the tab's profile identity matches the persisted collection
    item.
11. After first save of a **blank draft**, the profile participates in session
    restore on the next launch (draft-only tabs remain excluded until saved).
12. After save, MCP tool lists refresh when MCP exposure applies — same
    practical outcome as saving an HTTP request that affects MCP tools.
13. Save and save-as actions are observable in the same product telemetry
    families used for HTTP save actions.
14. HTTP request save behavior is unchanged (no regression).

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

HTTP requests support a complete save workflow: **Actions → Save** or `Ctrl+S`
for first save or in-place update; **Save As…** or `Ctrl+Shift+S` for a new
collection item; collection picker and new-collection creation; optional
overwrite confirmation; stale-version warning; sidebar tree update; tab title
sync; session-restore inclusion after first save; MCP tool refresh.

WebSocket profiles can be stored in collections at the persistence layer, and
users can open, rename, and delete them from the sidebar
([PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160)). What is
missing is the **editor-to-collection save path** for workspace tabs:

| Capability | HTTP request today | WebSocket today |
| --- | --- | --- |
| **Actions → Save** | Yes | Not offered on WebSocket tabs |
| **Actions → Save As…** | Yes | Not offered |
| **`Ctrl+S` / `Ctrl+Shift+S`** | Yes (Request Editor) | Documented but not wired to profile save |
| **First-save collection picker** | Yes | Not offered |
| **Overwrite existing profile** | Yes, with optional confirm | Not offered from editor |
| **Save As → new profile** | Yes | Not offered |
| **Sidebar tree update after save** | Yes | No profile-level save to trigger it |
| **Tab title / identity after save** | Yes | Draft tabs keep ephemeral identity |
| **Session restore after first save** | Yes | Drafts excluded; no first-save promotion |
| **MCP tool refresh after save** | Yes | No profile-level save hook |

`doc/user/collections.md` steps 1–4 describe save for "a request or WebSocket
profile." `doc/user/hotkeys.md` lists **Save Profile** and **Save As Profile**
under **WebSocket Session**. Users following those guides cannot complete the
workflow on WebSocket tabs.

Without this story, the Tab Protocol Modes epic
([PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) still fails
FR-5 (WebSocket save flow) from
`ai-tasks/PYPOST-1156/10-requirements.md`, and the documented MCP authoring
path (configure in tab → save → enable MCP exposure) remains incomplete.

### Business Need

Collections are the organizational home for both HTTP requests and WebSocket
profiles. Users expect:

- **Persist work** — turn a draft or edited tab into a reusable collection
  item without export/import workarounds.
- **Predictable save semantics** — Save updates in place; Save As forks; prompts
  match HTTP so muscle memory transfers.
- **Visible confirmation** — the sidebar and tab chrome reflect what was saved.
- **Session continuity** — once saved, the profile reopens after restart like
  any other collection item.
- **Agent readiness** — saved MCP-exposed profiles appear in tool discovery
  immediately after save.

### Scope (this task)

- **Save** and **Save As…** for WebSocket profiles from workspace tabs
  (blank drafts, saved profiles opened from Collections, and isolated copies
  from **New tab**).
- Collection picker dialog for first save and Save As (existing collection or
  new collection), with profile name entry.
- In-place overwrite of an existing collection WebSocket profile, with the same
  confirmation and stale-version rules as HTTP save.
- Post-save updates: Collections tree, workspace tab title, tab profile
  identity, session-restore eligibility, MCP tool list refresh.
- **Actions** menu entries and `Ctrl+S` / `Ctrl+Shift+S` for WebSocket save
  while a WebSocket tab is focused.
- Save / save-as telemetry parity with HTTP.

### Out of Scope

- Blank WebSocket draft tab creation —
  [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) (dependency).
- Collections sidebar **New tab** / **Rename** / **Delete** menu parity —
  [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160) (related;
  save applies to tabs opened there but menu work is not delivered here).
- Protocol picker on `Ctrl+N` / **+** —
  [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157).
- Close-last-tab picker —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- Non-save WebSocket shortcuts (Connect, Send, Focus URL, etc.) and Help →
  Hotkeys **WebSocket Session** section registration —
  [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162) (Save shortcuts
  are in scope here per Jira acceptance criteria; other hotkeys are not).
- End-user documentation updates —
  [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) (this story
  makes existing `collections.md` / `hotkeys.md` save claims true).
- Saving individual message presets or sequences in isolation (composer
  **Save…** for presets remains an in-tab preset action, not a collection
  profile save).
- Import/export format changes, history replay, or MCP probe runtime behavior.
- Changing HTTP save behavior.
- Save-on-close or auto-save (explicit Save / Save As only).

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Collection** | Folder grouping HTTP requests and WebSocket profiles. |
| **WebSocket profile** | Saved connection configuration (URL, handshake, presets, sequences, MCP fields) stored under a collection. |
| **WebSocket profile draft** | Unsaved profile living only in a workspace tab (e.g. **New WebSocket** blank draft). |
| **HTTP request** | Reference behavior for save, save-as, overwrite prompts, and tree update. |
| **Workspace tab** | Editor strip tab showing a WebSocket draft or saved/copied profile. |
| **Save dialog** | Name + collection picker (existing or new collection) shown on first save and Save As. |
| **Collections tree row** | Sidebar item showing `ws <name>` for a saved WebSocket profile. |
| **MCP-exposed profile** | Saved WebSocket profile with MCP exposure enabled; appears in agent tool lists after save. |
| **Session restore** | Reopen of saved profiles on next launch; drafts excluded until first save. |

### Functional Requirements

#### FR-1: Save entry points on WebSocket tabs

- FR-1.1 A WebSocket workspace tab exposes **Save** and **Save As…** in an
  **Actions** menu accessible from the WebSocket editor chrome (analogous to
  the HTTP request editor).
- FR-1.2 `Ctrl+S` triggers **Save** and `Ctrl+Shift+S` triggers **Save As…**
  when a WebSocket tab is the active workspace tab.
- FR-1.3 Save actions read the **current editor state** (all persisted profile
  fields visible in the tab) at the moment the user saves — not a stale
  snapshot from tab open.

#### FR-2: First save (profile not in any collection)

- FR-2.1 **Save** on a profile with no collection backing opens a save dialog
  requiring a non-empty profile name.
- FR-2.2 The user selects an existing collection or enters a new collection
  name; empty collection names are rejected with the same feedback HTTP save
  uses.
- FR-2.3 Confirming persists the profile to the chosen collection and cancels
  leave no collection changes.
- FR-2.4 After success, the profile appears in the Collections tree under the
  target collection.

#### FR-3: Save overwrite (profile already in a collection)

- FR-3.1 **Save** on a profile whose identity already exists in a collection
  updates that collection item in place (same profile identity).
- FR-3.2 Overwrite includes all editor-visible persisted fields: name, URL,
  params, headers, subprotocols, presets, sequences, and MCP-related fields.
- FR-3.3 When **Confirm before overwrite** is enabled in Settings, the user
  must confirm before replacing the existing saved profile.
- FR-3.4 When the collection copy is newer than the tab's last-known saved
  baseline, the user receives a stale-version warning before overwrite is
  allowed — matching HTTP save expectations.
- FR-3.5 Declining any overwrite or stale prompt aborts the save without
  changing Collections or the tab.

#### FR-4: Save As

- FR-4.1 **Save As…** always opens the save dialog (name + collection picker).
- FR-4.2 Confirming creates a **new** collection profile with a **new**
  identity; the original saved profile (if any) is unchanged.
- FR-4.3 After success, the active workspace tab represents the **new** saved
  profile (title and identity align with the new collection item).
- FR-4.4 Other open tabs still bound to the original profile (e.g. isolated
  copies from **New tab**) are unaffected.

#### FR-5: Post-save workspace and sidebar alignment

- FR-5.1 After any successful save, the workspace tab title reflects the
  saved profile name.
- FR-5.2 After any successful save, the tab's profile identity matches the
  persisted collection item (so session restore, left-click open, and delete
  handling reference the correct saved profile).
- FR-5.3 The Collections sidebar shows the saved profile as `ws <name>` under
  the target collection without requiring a manual refresh.
- FR-5.4 The target collection is expanded in the sidebar when the product
  already expands collections on HTTP save.
- FR-5.5 After first save of a previously unsaved draft, the profile is
  eligible for session restore on the next application launch.

#### FR-6: MCP and collections integration

- FR-6.1 After save, MCP tool discovery refreshes when the saved profile
  affects exposed MCP tools — same practical outcome as saving an HTTP request
  that changes MCP tools.
- FR-6.2 Saving does not implicitly enable MCP exposure; it persists whatever
  MCP settings the user configured in the editor.

#### FR-7: Isolated and multi-tab scenarios

- FR-7.1 **Save** on an isolated copy opened via Collections **New tab**
  updates the backing saved profile (same identity as the collection item),
  matching HTTP **New tab** save semantics.
- FR-7.2 **Save As…** from any tab type (draft, saved, isolated copy) always
  creates a new collection item per FR-4.
- FR-7.3 Saving in one tab does not alter editor content or live connection
  state in other tabs unless they share the same saved identity and the user
  reloads or reopens (same expectation as HTTP).

### Non-Functional Requirements

- **NFR-1 Consistency:** WebSocket save and save-as must feel the same as
  HTTP save for dialog flow, prompts, shortcuts, and sidebar update — the
  primary reference behavior users already know.
- **NFR-2 Trust:** `doc/user/collections.md` and `doc/user/hotkeys.md` save
  instructions must match shipped behavior after this story (full doc pass
  remains PYPOST-1163).
- **NFR-3 Data integrity:** A cancelled or failed save must not partially
  update Collections or leave the tab in an ambiguous saved/unsaved state.
- **NFR-4 Metrics:** Save and save-as actions from WebSocket tabs are recorded
  in the same telemetry families as HTTP save actions, distinguishable by
  source where the product already attributes menu vs shortcut.
- **NFR-5 Performance:** Prefer updating the Collections tree incrementally
  when possible (as HTTP save-as does) rather than forcing a full sidebar
  rebuild on every save.

### Constraints and Assumptions

- Parent epic:
  [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on WS-TM-2:
  [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) — blank
  WebSocket draft tabs must exist before save-to-collection is meaningful.
- Related: WS-TM-4
  [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160) — isolated
  tab copies may hold unsaved edits until the user saves; this story provides
  that save path.
- Epic research:
  [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) FR-5
  (WebSocket save flow).
- HTTP save behavior (collection picker, overwrite confirm, stale warning,
  tree update, tab sync, MCP refresh) is the authoritative UX reference.
- WebSocket profiles are already a supported collection child type in storage;
  this story connects the **editor** to that persistence path.
- **Confirm before overwrite** in Settings applies to WebSocket profile
  overwrite the same way it applies to HTTP requests (single user preference).
- Preset-level **Save…** in the WebSocket composer saves a message preset
  within the tab; it is not a substitute for profile-level **Save** to a
  collection.

## Q&A

- **Why mirror HTTP save instead of inventing WebSocket-specific save UX?**
  Users already learned Save / Save As on HTTP requests. Collections docs
  describe one workflow for both item types. Parity reduces support burden and
  completes FR-5 of the epic.

- **Does Save on a blank draft create a collection item immediately?**
  Yes, after the user confirms the save dialog. Until then the tab remains a
  draft excluded from session restore.

- **Does Save on an isolated New tab copy create a new collection item?**
  No. **Save** updates the existing saved profile (same identity). Use **Save
  As…** to fork a new collection item.

- **What fields are included in a saved WebSocket profile?**
  All configuration the user can edit in the WebSocket tab that is meant to
  persist: name, URL, handshake fields, presets, sequences, and MCP exposure
  settings. Ephemeral session state (live stream contents, connection status)
  is not part of the saved profile.

- **What happens to MCP tools after I save with MCP exposure enabled?**
  Tool discovery refreshes so agents can see the updated saved profile without
  restarting the application.

- **Are unsaved drafts restored after restart?**
  No — unchanged from PYPOST-1158. Only profiles saved to a collection become
  restore-eligible.

- **Is the full WebSocket Session hotkeys help section in scope?**
  No. PYPOST-1162 registers Connect, Send, Focus URL, and the Help → Hotkeys
  section. This story delivers **Save** and **Save As…** shortcuts and menu
  entries only.

- **Does this story update user documentation?**
  Not directly — PYPOST-1163. This story makes existing save claims in
  `collections.md` and `hotkeys.md` accurate.

- **What is the relationship to preset Save in the composer?**
  Preset save updates in-tab message presets. Profile **Save** persists the
  whole WebSocket configuration to Collections. Both can coexist; profile save
  is what this story delivers.

## References

- [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — research / FR-5
- [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) — WS-TM-2 dependency (blank draft)
- [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160) — WS-TM-4 (isolated tab copies)
- [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162) — non-save WebSocket hotkeys
- [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) — user documentation
- `ai-tasks/PYPOST-1156/20-architecture.md` — WS-TM-5 epic decomposition
- `ai-tasks/PYPOST-1160/10-requirements.md` — collections context-menu parity
- `doc/user/collections.md` — save workflow user expectation
- `doc/user/hotkeys.md` — Save Profile / Save As Profile shortcuts
