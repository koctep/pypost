# PYPOST-1159: Tab entry-point parity

## Goals

`Ctrl+N` and the tab-bar **+** already show a **protocol picker** so the
user chooses **HTTP Request** or **WebSocket** before a blank tab opens
([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)). Choosing
**WebSocket** already opens a usable unsaved WebSocket draft
([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)).

Closing the **last** workspace tab does not. The product still replaces
that last tab with a blank **HTTP** tab and never asks which protocol the
user wants. Someone who just closed their only WebSocket tab (or their
only tab of any kind) is silently put on an HTTP editor.

This story (WS-TM-3 under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) closes that
gap: when the workspace would otherwise be empty after a close, the user
gets the **same protocol choice** as `Ctrl+N` and **+**. Restart must
still restore **saved** HTTP and WebSocket tabs exactly as today,
including mixed workspaces.

The business goal is one honest blank-tab rule: every path that creates a
**new blank tab** (keyboard, **+**, or last-tab replacement) asks for a
protocol. Restoring work the user already saved is not a blank-tab path
and must not change.

## User Stories

- As a **developer testing APIs**, I want closing my last tab to offer
  **HTTP Request** or **WebSocket** the same way `Ctrl+N` and **+** do, so
  I am not dropped onto an HTTP editor without a choice.
- As a **user who just closed a WebSocket tab**, I want that last-tab
  replacement to let me open another WebSocket draft, so finishing one
  session does not force me onto HTTP.
- As a **user who dismisses the picker** after closing the last tab, I
  want no replacement tab created, so the product does not invent an HTTP
  tab I did not ask for.
- As a **returning user**, I want restart to bring back the **saved**
  HTTP and WebSocket tabs I had open, so last-tab parity does not change
  session restore.
- As a **returning user with a mixed workspace**, I want both saved HTTP
  and saved WebSocket tabs restored together, so a workspace that mixed
  protocols still comes back intact.
- As a **product owner**, I want a completed last-tab replacement
  (user chose a protocol) recorded by **source** (this fallback, not
  `Ctrl+N` or **+**) and **protocol** (HTTP vs WebSocket), so blank-tab
  starts stay comparable across entry points.

## Definition of Done

PYPOST-1159 is done when:

1. Closing the last workspace tab presents the **same protocol picker** as
   `Ctrl+N` and tab-bar **+** **before** any replacement tab is created.
2. The picker lists **HTTP Request** first (default), then **WebSocket**.
3. Choosing **HTTP Request** opens a blank HTTP request tab (same kind of
   draft `Ctrl+N` / **+** already open for HTTP).
4. Choosing **WebSocket** opens a blank WebSocket draft tab (same kind of
   draft PYPOST-1158 already opens).
5. Dismissing the picker without a choice creates **no** replacement tab.
   The workspace may be empty.
6. Closing a tab while **other** workspace tabs remain does **not** show
   the picker and does not create a replacement tab.
7. If the last tab is a dirty unsaved WebSocket draft, the existing
   discard-or-keep prompt still runs **first**. The picker appears only
   after the tab is actually closed and the workspace would be empty.
8. Restart restore of **saved** HTTP request tabs and **saved** WebSocket
   profile tabs is unchanged.
9. A mixed saved workspace (HTTP and WebSocket tabs that were open and
   eligible to restore) still restores **both** kinds after restart.
10. Unsaved WebSocket drafts still do **not** come back after restart
    (PYPOST-1158 rule; this story must not regress it).
11. `Ctrl+N` and tab-bar **+** keep their current picker behavior; this
    story does not change those two entry points except that last-tab
    replacement now shares the same choose-then-open outcomes.
12. A completed last-tab replacement (user chose a protocol) is recorded
    in product telemetry with a **source** that identifies this fallback
    (not `shortcut` and not `plus_button`) and **protocol** (`http` or
    `websocket`).

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

PyPost already treats `Ctrl+N` and **+** as “choose protocol, then open a
blank tab.” Closing the last tab is still an implicit “always open HTTP.”
That third path contradicts the documented blank-tab workflow and the
“do not silently switch me to HTTP” expectation from the parent epic.

Session restore is a **different** path: it reopens **saved** work. That
path already restores HTTP and WebSocket profiles and must stay that way.
This story must not turn restore into a picker, and must not drop or
rewrite saved mixed workspaces.

### Business Need

Users need one rule for **new blank tabs**:

- Keyboard new tab, tab-bar **+**, and last-tab replacement all ask
  **HTTP Request** vs **WebSocket**.
- HTTP stays the default choice; WebSocket stays explicit.
- Cancel means “do not create a tab.”
- Restart still returns **saved** HTTP and WebSocket tabs, including
  mixed workspaces.

Without this story, protocol choice is only on the two voluntary new-tab
controls. Closing the last tab remains an HTTP trap, especially after a
WebSocket session.

### Scope (this task)

- When closing a tab would leave the workspace empty, show the **same
  protocol picker** used by `Ctrl+N` and **+** before creating a
  replacement tab.
- Keep the same picker outcomes: HTTP blank draft, WebSocket blank
  draft, or no tab on cancel.
- Keep unsaved-close handling for dirty WebSocket drafts **before** any
  replacement (discard vs keep tab).
- Leave restore of **saved** HTTP and WebSocket tabs unchanged.
- Keep mixed saved-workspace restore working (both protocols return).
- Keep unsaved WebSocket drafts out of restore.
- Record source and protocol when the user completes a last-tab
  replacement by choosing a protocol.

### Out of Scope

- Protocol picker on `Ctrl+N` / **+** —
  [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)
  (already shipped; this story reuses that choice, it does not redesign
  it).
- Blank WebSocket draft editor, default name, empty URL, and draft
  restore rules —
  [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)
  (already shipped; last-tab **WebSocket** must open that same draft).
- Collections **New tab** / rename / delete for WebSocket items —
  [PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160).
- WebSocket save / Save As to a collection —
  [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161).
- Context-aware WebSocket shortcuts and Help → Hotkeys —
  [PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162).
- User documentation rewrite —
  [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).
- Changing how saved HTTP or WebSocket profiles are restored (identity,
  disconnected WebSocket restore, which saved tabs return).
- Showing the protocol picker during session restore.
- Changing how saved WebSocket profiles open from Collections.
- History replay opening WebSocket tabs.
- Switching protocol on a tab after it is created (v1: close and open a
  new tab with the correct protocol).
- An **MCP Client** option in the picker.
- Changes to WebSocket transport, stream buffer, or session engine.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Workspace tab** | One editor in the tab strip (HTTP or WebSocket). |
| **Last tab** | The only remaining workspace tab; closing it would empty the strip. |
| **Empty-workspace replacement** | Offer of a new blank tab after the last tab is closed. |
| **Protocol picker** | Same HTTP vs WebSocket choice as `Ctrl+N` / **+**. |
| **HTTP Request** | Default picker option; opens a blank HTTP draft. |
| **WebSocket** | Opt-in picker option; opens a blank WebSocket draft. |
| **Saved profile tab** | HTTP or WebSocket tab tied to a collection item; restorable. |
| **Unsaved draft tab** | Blank tab not yet saved; not restored after restart. |
| **Mixed workspace** | Session with both saved HTTP and saved WebSocket tabs. |
| **Session restore** | Restart reopen of **saved** tabs; not a blank-tab path. |
| **New-tab source** | How the blank tab was requested (`Ctrl+N`, **+**, or last-tab fallback). |

### Functional Requirements

#### FR-1: Last-tab close uses the protocol picker

- FR-1.1 After the last workspace tab is closed, the product must present
  the protocol picker **before** creating any replacement tab.
- FR-1.2 That picker is the same choice as `Ctrl+N` and tab-bar **+**:
  **HTTP Request** first (default), then **WebSocket**.
- FR-1.3 This applies whether the closed last tab was HTTP or WebSocket,
  saved or draft.
- FR-1.4 Closing a tab when at least one other workspace tab remains must
  not show the picker and must not create a replacement tab.

#### FR-2: Same choose-then-open outcomes as existing blank-tab flow

- FR-2.1 Choosing **HTTP Request** opens a blank HTTP request tab, matching
  the HTTP outcome of `Ctrl+N` / **+**.
- FR-2.2 Choosing **WebSocket** opens a blank WebSocket draft tab, matching
  the WebSocket outcome already shipped in PYPOST-1158.
- FR-2.3 Dismissing the picker without a choice creates no tab. The
  workspace may remain empty.
- FR-2.4 `Ctrl+N` and tab-bar **+** keep their current picker behavior.

#### FR-3: Unsaved-close still happens before replacement

- FR-3.1 Closing a dirty unsaved WebSocket draft still uses the existing
  discard-or-keep prompt (PYPOST-1158).
- FR-3.2 If the user **keeps** the tab, no picker appears and the draft
  stays open.
- FR-3.3 If the user **discards** and that was the last tab, the protocol
  picker then appears (FR-1).

#### FR-4: Session restore of saved work is unchanged

- FR-4.1 Restart still restores **saved** HTTP request tabs that were
  eligible to restore before this story.
- FR-4.2 Restart still restores **saved** WebSocket profile tabs that were
  eligible to restore before this story.
- FR-4.3 Restore does **not** present the protocol picker.
- FR-4.4 Restore does **not** convert a saved WebSocket tab into an HTTP
  tab, or a saved HTTP tab into a WebSocket tab.

#### FR-5: Mixed-workspace restore must not regress

- FR-5.1 A session that had both saved HTTP tabs and saved WebSocket tabs
  open still restores **both** kinds after restart.
- FR-5.2 Unsaved WebSocket drafts still are **not** restored
  (PYPOST-1158). This story must not start restoring them.
- FR-5.3 Unsaved HTTP drafts follow existing HTTP restore rules; this
  story does not change HTTP draft restore.

#### FR-6: Telemetry on completed last-tab replacement

- FR-6.1 When the user completes a last-tab replacement by choosing a
  protocol, product telemetry records **source** as this empty-workspace
  fallback (distinct from `shortcut` and `plus_button`).
- FR-6.2 The same record includes **protocol** as `http` or `websocket`.
- FR-6.3 Dismissing the picker after last-tab close must not record a
  completed new-tab action.
- FR-6.4 Telemetry must not include request bodies, URLs, headers, or
  other payload content from this action.

### Non-Functional Requirements

- **NFR-1 Consistency:** Last-tab replacement must feel like `Ctrl+N` /
  **+**: same labels, same default, same cancel rule, same tab kinds.
- **NFR-2 Keyboard:** Closing the last tab is often a keyboard action.
  The picker must stay usable without a mouse (focus, move, confirm,
  dismiss), as already required for `Ctrl+N`.
- **NFR-3 Restore honesty:** Restart must not surprise the user with a
  picker or a silent protocol change of saved tabs.
- **NFR-4 Default path cost:** Confirming **HTTP Request** after last-tab
  close remains a short confirmation of the first option.
- **NFR-5 Telemetry:** Blank-tab counts stay attributable by source and
  protocol across `Ctrl+N`, **+**, and last-tab replacement (see FR-6).
- **NFR-6 Labels:** Protocol identity uses **HTTP Request** and
  **WebSocket**, not color alone.

### Constraints and Assumptions

- Parent epic:
  [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on WS-TM-1
  ([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)) and
  WS-TM-2
  ([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)); both
  are already shipped.
- Research:
  [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156)
  (epic FR-3 — tab entry-point parity).
- HTTP and WebSocket remain separate editor experiences.
- v1 default blank-tab protocol is **HTTP**; WebSocket is explicit.
- v1 does not support switching protocol on an already open tab.
- Cancel after last-tab close may leave the workspace empty. That matches
  cancel on `Ctrl+N` / **+** and avoids forcing an HTTP tab.
- Session restore is not a blank-tab entry point.
- User-facing picker copy stays **HTTP Request** and **WebSocket**.

## Q&A

- **Why is this a separate story from the picker?**
  `Ctrl+N` and **+** already ask for a protocol. Closing the last tab
  still forces HTTP. That leftover path is this story.
- **What if I close a tab that is not the last one?**
  Nothing new. No picker, no replacement tab.
- **What if I cancel the picker after closing the last tab?**
  No replacement tab is created. The workspace may be empty. The product
  does not insert a silent HTTP tab.
- **What if the last tab is a dirty WebSocket draft?**
  Discard-or-keep runs first. Keep: the draft stays, no picker. Discard
  on the last tab: then the picker.
- **Does restart show the picker?**
  No. Restore reopens saved work; it is not a new blank tab.
- **Do saved HTTP and WebSocket tabs still restore?**
  Yes. Same as today, including mixed workspaces.
- **Are unsaved WebSocket drafts restored?**
  No. That rule shipped in PYPOST-1158 and must stay.
- **Does this story change `Ctrl+N` or `+`?**
  No. Those entry points already use the picker. Last-tab replacement
  must match their outcomes.
- **Is Collections or Save in scope?**
  No. PYPOST-1160 and PYPOST-1161.
- **Are user docs in scope?**
  No. PYPOST-1163.
- **Can the user switch protocol after the replacement tab opens?**
  Not in v1. Close and open a new tab with the correct protocol.
- **Is MCP Client in the picker?**
  No.

## References

- [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — research
- [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) — protocol picker
- [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158) — WebSocket draft
