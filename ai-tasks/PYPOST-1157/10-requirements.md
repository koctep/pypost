# PYPOST-1157: Blank-tab protocol selector UX

## Goals

Today, `Ctrl+N` and the tab-bar **+** always open a blank HTTP request tab.
User documentation tells people to open a new tab and select **WebSocket**
mode, but that choice does not exist. WebSocket workspace tabs are reachable
only from a saved Collections profile or from session restore. Ad-hoc
WebSocket testing therefore requires a collection item first, unlike the HTTP
blank-tab workflow (open → compose → save).

This story (WS-TM-1 under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) closes that
first-step gap: when the user asks for a blank workspace tab via `Ctrl+N` or
**+**, they see a **protocol picker** and choose **HTTP Request** or
**WebSocket** *before* any new editor appears. **HTTP Request** remains the
default so the common HTTP path stays the shortest option.

The business goal is a first-class, documented way to start a blank tab of
the intended protocol from the tab bar — not a new editor, not Collections
changes, and not an MCP Client tab.

## User Stories

- As a **developer testing APIs**, I want `Ctrl+N` and **+** to let me
  **choose** **HTTP Request** or **WebSocket** before a tab opens, then
  **start** that protocol in a new workspace tab, so I do not need a
  Collections item first.
- As a **new PyPost user**, I want a visible **WebSocket** choice when I
  open a new tab, so that the WebSocket guide's step 1 matches the product.
- As an **HTTP-first user**, I want **HTTP Request** to be the default
  (first) option, so that my existing new-tab habit stays the shortest path.
- As a **user who opened a new tab by mistake**, I want cancelling the
  protocol picker to create no tab, so that my workspace is unchanged.
- As a **product owner**, I want completed new-tab actions recorded by
  entry source (`Ctrl+N` vs **+**) and chosen protocol (HTTP vs WebSocket),
  so that we can see how people start blank tabs.

## Definition of Done

PYPOST-1157 is done when:

1. Pressing `Ctrl+N` shows the protocol picker **before** a new workspace
   tab or editor is created.
2. Clicking the tab-bar **+** shows the same protocol picker **before** a
   new workspace tab or editor is created.
3. The picker lists **HTTP Request** as the first, default option, then
   **WebSocket**.
4. Choosing **HTTP Request** opens a blank HTTP request tab (the same kind
   of draft the product opens today after `Ctrl+N` / **+**).
5. Choosing **WebSocket** opens a new **WebSocket** blank tab, not an HTTP
   request tab. A placeholder tab is enough here; the full WebSocket draft
   editor is [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158).
6. Dismissing the picker without a choice creates no tab and leaves the
   workspace unchanged.
7. `Ctrl+N` and **+** share one choose-then-open blank-tab flow so later
   entry points can reuse the same protocol choice.
8. A completed new-tab action (user chose a protocol) is recorded in
   product telemetry with **source** (`shortcut` or `plus_button`) and
   **protocol** (`http` or `websocket`).
9. Opening a saved WebSocket profile from Collections is unchanged.

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

PyPost already has a WebSocket workspace editor, but the two primary
"new blank tab" actions (`Ctrl+N` and tab-bar **+**) always create an HTTP
request draft. There is no user-visible protocol choice at creation time.
`doc/user/websocket.md` step 1 tells users to open a new tab and select
**WebSocket** mode. That control is missing, so the documented first-run
WebSocket path is blocked unless the user already has a saved profile.

### Business Need

Users must be able to choose **HTTP Request** vs **WebSocket** at the
moment they open a blank tab, with HTTP remaining the default. Without
that choice:

- The WebSocket guide's first step does not match the product.
- Ad-hoc WebSocket work is forced through Collections.
- HTTP and WebSocket creation paths are not analogous.

This story delivers the protocol **choice** on the two primary entry
points and an on-screen WebSocket confirm result: a new **WebSocket**
blank tab (placeholder is enough). Follow-on stories deliver the full
blank WebSocket draft editor, other entry points, save, shortcuts, and
documentation.

### Scope (this task)

- Show a **protocol picker** when the user presses `Ctrl+N` or clicks
  tab-bar **+**.
- Present **HTTP Request** first (default) and **WebSocket** second.
- Create no tab if the user cancels or dismisses the picker.
- Open a blank HTTP request tab when the user chooses **HTTP Request**.
- Open a **WebSocket** blank tab when the user chooses **WebSocket** (not
  an HTTP request tab; a placeholder is enough until PYPOST-1158).
- Use one shared choose-then-open flow for both `Ctrl+N` and **+**.
- Record source and protocol on a completed new-tab choice.

### Out of Scope

- Blank WebSocket draft editor, default name, empty URL, and session-restore
  rules for drafts — [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158).
- Close-last-tab / empty-workspace fallback using the picker —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- Collections **New tab** / rename / delete for WebSocket items —
  [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160).
- WebSocket save / Save As to a collection —
  [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161).
- Context-aware WebSocket shortcuts and Help → Hotkeys —
  [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162).
- User documentation rewrite —
  [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).
- An **MCP Client** option in the picker (later story; not this epic).
- Switching protocol on a tab after it is created (v1: close and open a
  new tab with the correct protocol).
- Changing how saved WebSocket profiles open from Collections.
- History replay opening WebSocket tabs.
- Changes to WebSocket transport, stream buffer, or session engine.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Workspace tab** | One editor in the tab strip (HTTP request or WebSocket). |
| **Protocol picker** | Choice shown before a blank tab is created. |
| **HTTP Request** | Default protocol option; opens a blank HTTP draft. |
| **WebSocket** | Opt-in protocol; confirming it opens a blank WS tab. |
| **New-tab source** | How the user asked: keyboard shortcut or tab-bar **+**. |
| **Chosen protocol** | HTTP or WebSocket recorded with a completed choice. |

### Functional Requirements

#### FR-1: Picker before any new blank tab

- FR-1.1 `Ctrl+N` must present the protocol picker before a new workspace
  tab or editor is created.
- FR-1.2 Tab-bar **+** must present the same protocol picker before a new
  workspace tab or editor is created.
- FR-1.3 The picker offers exactly two protocols in this story:
  **HTTP Request** and **WebSocket**.

#### FR-2: HTTP Request is the default

- FR-2.1 **HTTP Request** is the first option in the protocol picker.
- FR-2.2 **HTTP Request** is the default selection when the picker appears.
- FR-2.3 Choosing **HTTP Request** opens a blank HTTP request tab, matching
  today's blank-tab kind.

#### FR-3: Cancel creates no tab

- FR-3.1 If the user dismisses the picker without choosing a protocol, no
  new tab is created.
- FR-3.2 After cancel, the existing tab strip, focused tab, and unsaved
  work are unchanged.

#### FR-4: WebSocket is a first-class choice

- FR-4.1 The user can choose **WebSocket** from the picker on `Ctrl+N`
  and on **+**.
- FR-4.2 Choosing **WebSocket** opens a new workspace tab that is a
  **WebSocket** blank tab, not an HTTP request tab.
- FR-4.3 That tab may be a placeholder. The full WebSocket draft editor
  is PYPOST-1158; this story does not ship that editor's contents.

#### FR-5: One shared blank-tab flow

- FR-5.1 `Ctrl+N` and tab-bar **+** must use the same choose-then-open
  sequence after the picker (same protocols, same cancel rule, same HTTP
  and WebSocket outcomes).
- FR-5.2 Later blank-tab entry points (for example close-last-tab in
  PYPOST-1159) are expected to reuse this same sequence; this story does
  not change those other entry points yet.
- FR-5.3 Opening a saved WebSocket profile from Collections stays on the
  existing saved-profile path (not the blank-tab picker).

#### FR-6: Telemetry on completed choice

- FR-6.1 When the user completes a new-tab action by choosing a protocol,
  product telemetry records the **source** as `shortcut` (`Ctrl+N`) or
  `plus_button` (tab-bar **+**).
- FR-6.2 The same record includes **protocol** as `http` or `websocket`.
- FR-6.3 Telemetry must not include request bodies, URLs, headers, or
  other payload content from this action (there is no URL yet).

### Non-Functional Requirements

- **NFR-1 Keyboard:** Because `Ctrl+N` is a keyboard action, the protocol
  picker must be usable without a mouse (focus, move between options,
  confirm, dismiss).
- **NFR-2 Discoverability:** A first-time user following
  `doc/user/websocket.md` step 1 must see a **WebSocket** option when they
  open a new tab via `Ctrl+N` or **+**.
- **NFR-3 Default path cost:** Choosing the default **HTTP Request** must
  remain a short confirmation of the first option, not a multi-step form.
- **NFR-4 Labels:** Protocol identity uses the names **HTTP Request** and
  **WebSocket**, not color alone.
- **NFR-5 Telemetry:** New-tab counts stay attributable by source and
  protocol (see FR-6).

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on: none. Research:
  [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156).
- HTTP and WebSocket remain separate editor experiences; this story adds
  a **choice at creation**, not a merged editor.
- v1 default blank-tab protocol is **HTTP**; WebSocket is explicit.
- v1 does not support switching protocol on an already open tab.
- **MCP Client** is not a picker option in this story.
- User-facing copy of the picker uses **HTTP Request** and **WebSocket**.

## Q&A

- **Why a picker instead of always HTTP?**
  Docs promise a WebSocket choice on new tab; Collections-only WebSocket
  blocks ad-hoc work.
- **Why is HTTP the default?**
  Matches today's blank-tab behavior; WebSocket is opt-in at creation
  (epic FR-1.4).
- **What if the user cancels?**
  No tab is created; workspace stays as it was.
- **What happens when the user confirms WebSocket?**
  A new **WebSocket** blank tab opens (not an HTTP request tab). A
  placeholder is enough; the full draft editor is PYPOST-1158.
- **Does this story ship the WebSocket draft editor?**
  No. That is PYPOST-1158. This story ships the choice plus the
  WebSocket blank-tab confirm outcome (and the HTTP blank-tab outcome).
- **Does close-last-tab use the picker?**
  No. That is PYPOST-1159.
- **Is MCP Client in the picker?**
  No. Later story; this epic is HTTP vs WebSocket only.
- **Can the user switch protocol after the tab opens?**
  Not in v1. Close the tab and open a new one with the correct protocol.
- **Do Collections-opened WebSocket profiles go through the picker?**
  No. Saved profiles keep the existing open path.
- **Must `Ctrl+N` and `+` behave the same?**
  Yes. One shared choose-then-open flow so later entry points can reuse it.

## References

- [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — research
- `ai-tasks/PYPOST-1156/10-requirements.md` — epic FRs (FR-1, NFR-5)
- `doc/user/websocket.md` — step 1 gap (select **WebSocket** mode)
- `doc/user/interface.md` — `Ctrl+N` / **+** new tab
- `doc/user/hotkeys.md` — `Ctrl+N` currently described as draft request tab
