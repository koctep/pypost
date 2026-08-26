# PYPOST-1158: Blank WebSocket draft tab

## Goals

PyPost already lets the user **choose WebSocket** when opening a blank tab
([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)). That choice
must land on a **usable unsaved WebSocket profile** in the workspace — the
same create → compose → save path HTTP drafts already have — without first
creating a Collections item.

Today, a full WebSocket editor exists for **saved** profiles. A blank
WebSocket tab from the protocol picker is not a working draft: it is not
the documented editor (connection bar, stream, composer, presets, MCP
preview), it is not independent of other open tabs, and it must not
reappear after restart until the user saves.

This story (WS-TM-2 under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) delivers that
**draft tab**: titled **New WebSocket**, with an empty URL field (no
host/path and no pre-filled scheme), full editor behavior on unsaved
work, no merge with other tabs, and no session restore until first
save. Closing a draft with edits uses the same unsaved-close prompt as
HTTP drafts until Save ships in PYPOST-1161.

The business goal is ad-hoc WebSocket testing and MCP-contract preview
from a blank tab, matching `doc/user/websocket.md` after protocol choice.

## User Stories

- As a **developer testing APIs**, I want a new WebSocket tab to open as
  an unsaved draft named **New WebSocket** with an empty URL field (I
  type the full address, including `ws://` or `wss://`), so I can reach
  an endpoint without a Collections item.
- As a **developer testing APIs**, I want Connect, the stream inspector,
  the composer, presets, and MCP preview to work on that draft the same
  way they work on a saved-profile tab, so I can try an endpoint before
  I save.
- As a **developer building MCP tools**, I want the MCP preview on the
  draft to show the agent contract for the in-tab settings, so I can
  review exposure before the first save (actual agent tools still need a
  saved, exposed profile — later stories).
- As a **user with several WebSocket tabs**, I want each new blank
  WebSocket tab to stay its own tab, so opening another draft does not
  jump me to an existing tab.
- As a **returning user**, I want unsaved WebSocket drafts **not** to
  come back after I quit and reopen PyPost, so session restore only
  brings back work I have saved to a collection.
- As a **user closing a WebSocket draft I edited**, I want the same
  unsaved-close choice as on an HTTP draft (**discard** the work or
  **keep the tab**), so I am not forced into a save path that this
  story does not ship.

## Definition of Done

PYPOST-1158 is done when:

1. Opening a blank WebSocket tab (the WebSocket outcome of the
   PYPOST-1157 protocol choice) shows a **WebSocket** workspace editor,
   not an HTTP request editor and not an empty placeholder.
2. The tab title is **New WebSocket**.
3. The connection URL field is empty: no host or path, and no pre-filled
   scheme. The user types a full address including `ws://` or `wss://`.
4. The draft is **not** a Collections item until the user later saves
   (save itself is [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161)).
5. On that draft, the user can **Connect** / **Disconnect**, inspect the
   live stream, compose and send messages, use presets (and sequences),
   and open **MCP preview** for the in-tab configuration.
6. Connecting from a draft counts toward the same concurrent-session
   ceiling as any other WebSocket session.
7. After the user quits with only unsaved WebSocket drafts open, those
   drafts are **not** restored on the next launch. Restore stays limited
   to previously saved profiles (and existing HTTP restore rules).
8. Opening another blank WebSocket tab always adds a **new** tab. It
   does not reuse or focus another open tab (saved or draft), even if
   titles or empty URLs match.
9. Opening a **saved** WebSocket profile from Collections still focuses
   an existing tab for that profile when one is already open (unchanged
   saved-profile behavior).
10. Until PYPOST-1161 ships Save, closing a WebSocket draft that has
    edits uses the **same unsaved-close prompt as HTTP drafts**:
    **discard** the work or **keep the tab**. This story does not add a
    WebSocket save path on close.

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

The documented WebSocket first-run path is: open a new tab, select
**WebSocket**, enter a URL, connect, inspect, compose, then save. The
protocol **choice** exists (PYPOST-1157). The **draft editor** on that
choice does not: users still cannot ad-hoc test `ws://` / `wss://`
without a collection item, and MCP preview cannot be exercised on
unsaved work. Saved-profile tabs also **deduplicate** by identity; a
blank draft must not inherit that merge rule, or a second "New
WebSocket" would steal focus from the first.

### Business Need

HTTP drafts already allow compose-before-save. WebSocket must match that
for:

- Ad-hoc endpoint testing without cluttering Collections.
- Interactive MCP authoring: configure in a blank tab, preview the
  contract, then save and expose (save/expose are later stories).
- Honest session restore: unsaved drafts are ephemeral; only saved
  profiles return after restart.

Without this story, PYPOST-1157's WebSocket option is not a real
workspace editor, and the epic still fails the WebSocket guide's step 1.

### Scope (this task)

- Present the **full WebSocket editor** on a blank, unsaved tab:
  connection bar (URL, Connect/Disconnect, state), handshake details
  (params, headers, subprotocols), stream inspector, composer, presets
  and sequences, and MCP preview of the in-tab draft.
- Default tab title **New WebSocket**.
- Empty connection URL at creation (no host/path and no pre-filled
  scheme); the user types a full `ws://` or `wss://` address.
- Handshake fields other than URL (params, headers, subprotocols) start
  at a new unsaved profile's factory defaults, not copied from another
  tab.
- Treat the tab as a **draft**: not a collection item yet; not restored
  after restart.
- Closing a draft with edits uses the HTTP unsaved-close prompt
  (discard vs keep tab) until PYPOST-1161 ships Save; no new save path
  on close.
- Keep each blank WebSocket tab **independent** of other open tabs
  (no focusing an existing tab when the user asked for a new draft).
- Reuse the same editor experience users already have on saved-profile
  tabs (behavior parity for connect, stream, compose, presets, preview).

### Out of Scope

- Protocol picker on `Ctrl+N` / **+** —
  [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)
  (already the way the user chooses WebSocket).
- Close-last-tab / empty-workspace picker —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- Collections **New tab** / rename / delete for WebSocket items —
  [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160).
- **Save** / **Save As** to a collection, overwrite prompts, and making
  the tab participate in restore **after** save —
  [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161).
- Context-aware WebSocket shortcuts and Help → Hotkeys —
  [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162).
- User documentation rewrite —
  [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).
- Switching protocol on a tab after it is created (v1: close and open a
  new tab with the correct protocol).
- Changing how saved profiles open or deduplicate from Collections.
- History replay opening WebSocket tabs.
- Changes to WebSocket transport bounds, stream buffer, heartbeats, or
  MCP **probe runtime** (agents still run only against **saved** exposed
  profiles). Enabling **Expose as MCP Tool** as a persisted collection
  setting is part of save (PYPOST-1161), not this story.
- An **MCP Client** workspace tab.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Workspace tab** | One editor in the tab strip. |
| **WebSocket profile draft** | Unsaved WebSocket profile living only in a tab. |
| **Saved WebSocket profile** | Collections item; opens with existing focus-if-open rule. |
| **Blank WebSocket tab** | Workspace tab holding a draft: title **New WebSocket**. |
| **Connection URL** | Empty at creation (no scheme, host, or path); user types a full `ws://` or `wss://` address. |
| **WebSocket editor** | Connection bar, handshake, stream, composer, presets, MCP preview. |
| **MCP preview** | In-tab view of the agent contract for current draft settings. |
| **Session restore** | Restart reopen of tabs; drafts are excluded until first save. |

### Functional Requirements

#### FR-1: Blank WebSocket tab is a real draft editor

- FR-1.1 After the user chooses **WebSocket** for a new blank tab, the
  workspace shows a WebSocket editor (not an HTTP request editor).
- FR-1.2 The tab title is **New WebSocket**.
- FR-1.3 The connection URL field is empty at creation: no host or path
  and no pre-filled scheme. The user types a full address including
  `ws://` or `wss://`.
- FR-1.4 Remaining handshake fields — **Params**, **Headers**, and
  **Subprotocols** — start at the product factory defaults for a **new
  unsaved WebSocket profile** (the same defaults as a profile that has
  never been saved or copied). They are not copied from another open
  tab. The URL is the only handshake field that starts blank rather
  than at those factory defaults.

#### FR-2: Draft is not a collection item

- FR-2.1 Creating the tab does not add an item to Collections.
- FR-2.2 The user can edit URL, handshake, composer, presets, and MCP
  preview fields on the draft without an implicit save to Collections.

#### FR-3: Live session features work on the draft

- FR-3.1 **Connect** and **Disconnect** work from the draft using the
  URL and handshake the user entered.
- FR-3.2 The stream inspector shows inbound and outbound frames for the
  draft session (filter, search, inspect, clear, export as already
  documented for WebSocket tabs).
- FR-3.3 The composer can draft and send text, JSON, and binary frames
  on the draft session.
- FR-3.4 Presets and sequences can be created, loaded, sent, and run on
  the draft (in-tab only until save).
- FR-3.5 Connection state is visible (disconnected / connecting /
  connected / closing / reconnecting) without relying on color alone.

#### FR-4: MCP preview on the draft

- FR-4.1 MCP preview renders the agent contract for the **current
  in-tab** draft configuration (URL, handshake, MCP-related fields the
  editor already exposes).
- FR-4.2 Preview on a draft does **not** require a Collections item.
- FR-4.3 Preview does **not** by itself register a live MCP tool for
  agents; tools remain tied to saved, exposed profiles.

#### FR-5: Drafts are excluded from session restore

- FR-5.1 Unsaved WebSocket draft tabs are not reopened when PyPost
  starts from a previous session.
- FR-5.2 Saved WebSocket profiles that were open remain restorable
  (no regression).
- FR-5.3 After the user later saves a draft (PYPOST-1161), restore of
  that **saved** tab is that story's concern; this story only guarantees
  **unsaved** drafts stay out of restore.

#### FR-6: No merge with other open tabs

- FR-6.1 Asking for a new blank WebSocket tab always creates a new tab.
- FR-6.2 A new draft must not focus or replace another draft, even if
  both are titled **New WebSocket** and both have an empty URL.
- FR-6.3 A new draft must not focus or replace a tab that already shows
  a **saved** profile.
- FR-6.4 Opening a saved profile from Collections still focuses an
  existing tab for **that** profile when one is already open.

#### FR-7: Session limits apply

- FR-7.1 Connecting from a draft consumes one concurrent WebSocket
  session slot, same as a saved-profile tab.
- FR-7.2 Exceeding the configured session ceiling shows the same class
  of error as connecting from a saved profile (disconnect unused
  sessions).

#### FR-8: Closing a dirty draft (until Save)

- FR-8.1 Until PYPOST-1161 ships Save, closing a WebSocket draft that
  has edits uses the **same unsaved-close prompt as HTTP drafts**: the
  user may **discard** the work (close the tab) or **keep the tab**.
- FR-8.2 That prompt is not a save path. This story does not introduce
  Save, Save As, or any other way to persist the draft on close.

### Non-Functional Requirements

- **NFR-1 Consistency:** Blank WebSocket UX must feel analogous to blank
  HTTP UX (open → compose → save later), and analogous to a
  saved-profile WebSocket tab for live session work.
- **NFR-2 Discoverability:** After choosing **WebSocket** on new tab,
  the user must see the documented WebSocket editor, not a blank or HTTP
  surface.
- **NFR-3 Accessibility:** Protocol and connection state must not rely
  on color alone (existing WebSocket state-badge rule).
- **NFR-4 Session limits:** Draft connects respect
  `ws_max_concurrent_sessions` like any other session.
- **NFR-5 Independence:** Multiple drafts in one workspace must not
  share live connection state.

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on WS-TM-1:
  [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)
  (protocol choice already opens a WebSocket blank tab).
- Research:
  [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156)
  FR-2 (blank WebSocket draft tab).
- HTTP and WebSocket remain separate editor experiences.
- v1 does not support switching protocol on an already open tab.
- Save to collection is **not** this story; drafts stay unsaved.
  Closing a dirty draft reuses the HTTP unsaved-close prompt (discard
  vs keep tab); it does not invent a WebSocket save path.
- MCP probe **runtime** is unchanged; this story only enables GUI
  preview on unsaved configuration.
- Default blank-tab protocol remains HTTP; this story covers the
  WebSocket **draft after** the user already chose WebSocket.

## Q&A

- **Why a draft tab instead of forcing Collections first?**
  Docs and HTTP parity require compose-before-save. Ad-hoc `ws://`
  testing and MCP preview need an unsaved path.
- **What is the default name and URL?**
  Title **New WebSocket**. The URL field is empty: no host/path and no
  pre-filled scheme. The user types a full address including `ws://` or
  `wss://`.
- **How do handshake fields start?**
  Only the URL starts blank. **Params**, **Headers**, and
  **Subprotocols** start at the factory defaults of a new unsaved
  WebSocket profile, not copied from another tab.
- **What happens if I close a draft I have edited?**
  Until PYPOST-1161 ships Save, the same unsaved-close prompt as HTTP
  drafts: **discard** or **keep the tab**. There is no save-on-close
  in this story.
- **Does Connect work before save?**
  Yes. The draft is a real session, subject to the same session ceiling.
- **Does MCP preview work before save?**
  Yes, for the in-tab contract. Live agent tools still need a saved
  exposed profile.
- **Are unsaved drafts restored after restart?**
  No. Only after first save (PYPOST-1161) does that profile join restore.
- **If I open two blank WebSocket tabs, do they merge?**
  No. Each draft is its own tab. Saved-profile open-from-Collections
  still focuses an existing tab for that saved item.
- **Does this story ship Save?**
  No. PYPOST-1161.
- **Does this story ship the protocol picker?**
  No. PYPOST-1157.
- **Can the user switch the tab to HTTP after it opens?**
  Not in v1. Close and open a new tab with the correct protocol.
- **Does close-last-tab create this draft?**
  Not in this story. PYPOST-1159.

## References

- [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — research
- [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) — protocol picker
- `ai-tasks/PYPOST-1156/10-requirements.md` — epic FR-2
- `doc/user/websocket.md` — editor, connect, compose, presets, MCP
- `doc/user/interface.md` — WebSocket editor layout
