# PYPOST-1165: Extend protocol picker with MCP Client

## Goals

Epic [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) already
lets a user choose **HTTP Request** or **WebSocket** before a blank workspace
tab opens (`Ctrl+N` and tab-bar **+**). That picker shipped in
[PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) (WS-TM-1, Done).

Research in [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164)
found a third protocol gap: **outbound MCP client** work has no blank-tab
start path. Users who want to probe a remote MCP server still rely on the
hidden HTTP method **MCP**, or they cannot start at all from `Ctrl+N` / **+**.
Competitive tools (Postman MCP request, MCP Inspector) treat MCP client as
its own request type, chosen at creation — not as an HTTP method.

This story (MCP-TM-1) closes that first-step gap only: when the user asks
for a blank tab, they can choose **MCP Client** as the third protocol,
alongside **HTTP Request** and **WebSocket**. **HTTP Request** stays the
default so the common HTTP path remains the shortest option.

The business goal is a first-class, measurable way to *start* an MCP Client
blank tab from the same choose-then-open flow as HTTP and WebSocket. This
story does not ship the MCP Client editor. The dedicated draft shell is
[PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) (MCP-TM-2).

## User Stories

- As a **developer testing a remote MCP server**, I want `Ctrl+N` and **+**
  to offer **MCP Client** next to **HTTP Request** and **WebSocket**, so I
  can start outbound MCP work without creating a collection item first.
- As an **HTTP-first user**, I want **HTTP Request** to remain the first,
  default option, so my existing new-tab habit stays the shortest path.
- As a **user who opened a new tab by mistake**, I want cancelling the
  picker to create no tab, so my workspace is unchanged.
- As a **user who chose MCP Client**, I want the new tab to be recognizably
  *not* an HTTP request tab, so I am not silently dropped onto the HTTP
  editor after an explicit MCP Client choice.
- As a **product owner**, I want a completed new-tab action that chose
  MCP Client recorded with protocol `mcp_client` (and the same source as
  today: `shortcut` vs `plus_button`), so we can see how people start
  blank MCP Client tabs versus HTTP and WebSocket.

## Definition of Done

PYPOST-1165 is done when:

1. The blank-tab protocol picker lists three items, in this order:
   **HTTP Request**, **WebSocket**, **MCP Client**.
2. **HTTP Request** remains the first, default option (same keyboard
   confirm path as today: the first item is the default).
3. The product recognizes **MCP Client** as a first-class blank-tab
   protocol identity (`TabProtocol.MCP_CLIENT`, value `mcp_client`),
   peer to HTTP and WebSocket — not an unnamed string and not treated
   as HTTP.
4. Choosing **MCP Client** from `Ctrl+N` or **+** opens a new workspace
   tab that is **not** an HTTP request tab. A temporary placeholder tab
   is enough here; the dedicated MCP Client draft shell is PYPOST-1166.
5. Choosing **HTTP Request** still opens a blank HTTP request tab.
   Choosing **WebSocket** still opens a blank WebSocket tab.
6. Dismissing the picker without a choice creates no tab and leaves the
   workspace unchanged.
7. A completed new-tab action that chose MCP Client is recorded in
   product telemetry with **source** (`shortcut` or `plus_button`) and
   **protocol** `mcp_client` — not collapsed to `unknown` or `http`.
8. Opening saved HTTP or WebSocket items from Collections is unchanged.
   HTTP method **MCP** is unchanged (migration is a later story).

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

PYPOST-1157 shipped a two-item protocol picker: **HTTP Request** (default)
then **WebSocket**. Completing a choice records source and protocol
(`http`, `websocket`, or `unknown` for non-picker paths). The research
story reserved `mcp_client` for this follow-up; it is not a choosable
protocol today.

Without an **MCP Client** choice at blank-tab creation:

- Ad-hoc outbound MCP testing has no first-class start path from
  `Ctrl+N` / **+**.
- Users stay on the overloaded HTTP method **MCP** path (naming collision
  with inbound **MCP** surfaces).
- Later MCP Client editor stories have nothing to attach to: the picker
  cannot express the third protocol, and telemetry cannot attribute
  MCP Client new tabs.

### Business Need

Users must be able to choose **MCP Client** at the moment they open a
blank tab, with HTTP remaining the default. Product telemetry must
attribute that choice as `mcp_client` so MCP Client adoption is visible
next to HTTP and WebSocket.

This story delivers the **choice** and a visible confirm result: a new
non-HTTP tab. Follow-on [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
delivers the blank MCP Client draft shell (URL bar, Connect / Disconnect,
connection state, empty tool browser, draft restore rules).

### Why a protocol identity (not only a label)

The Jira criterion `TabProtocol.MCP_CLIENT` is a product requirement, not
an implementation preference: later MCP Client stories (draft shell,
collections, restore) must share one named protocol with the picker and
with new-tab metrics. If MCP Client is only a menu string, confirming it
can be mis-routed as HTTP (today any non-WebSocket confirm opens HTTP)
and telemetry cannot record `protocol=mcp_client`.

### Boundary with PYPOST-1166 (placeholder vs draft shell)

This story and PYPOST-1166 split the same way PYPOST-1157 and
PYPOST-1158 split WebSocket: **choice first**, **editor second**.

| Concern | PYPOST-1165 (this story) | PYPOST-1166 (next) |
| --- | --- | --- |
| Picker item **MCP Client** (third) | **In scope** | Already present |
| Protocol identity `mcp_client` | **In scope** | Used, not invented |
| New-tab metrics `protocol=mcp_client` | **In scope** | Unchanged |
| HTTP remains first / default | **In scope** | Unchanged |
| Confirm MCP Client → non-HTTP tab | **In scope** (placeholder OK) | Replaces placeholder |
| MCP Client editor chrome | **Out of scope** | **In scope** (URL, Connect, tools) |
| Draft excluded from session restore | **Out of scope** | **In scope** |
| Tool discovery / `call_tool` | **Out of scope** | Later stories (MCP-TM-3, MCP-TM-4) |

**Placeholder rule:** confirming **MCP Client** must not silently open an
HTTP request tab. A temporary stub tab that PYPOST-1166 replaces is
acceptable and expected. The stub exists only so the user sees a
distinct confirm outcome and so later stories have a tab kind to
replace. It is not the MCP Client draft shell.

### Scope (this task)

- Add **MCP Client** as the third item in the existing blank-tab
  protocol picker (**HTTP Request** \| **WebSocket** \| **MCP Client**).
- Keep **HTTP Request** first and default.
- Recognize **MCP Client** as a first-class protocol identity
  (`TabProtocol.MCP_CLIENT` / `mcp_client`).
- On confirm of MCP Client from `Ctrl+N` or **+**, open a new workspace
  tab that is not an HTTP request tab (placeholder sufficient).
- Record `protocol=mcp_client` on that completed new-tab action.
- Preserve HTTP confirm, WebSocket confirm, and cancel behavior from
  PYPOST-1157.
- Reuse the existing choose-then-open flow; do not add a second
  tab-creation path for MCP Client.

### Out of Scope

- Blank MCP Client draft shell (URL bar, Connect / Disconnect, state
  indicator, empty tool browser, draft restore exclusion) —
  [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166).
- Tool discovery (`list_tools`), interactive `call_tool`, outbound
  headers, collections save/open, and HTTP method **MCP** migration —
  later MCP-TM stories.
- Close-last-tab / empty-workspace fallback using the picker —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- User documentation rewrite for the three-item picker —
  MCP-TM-8 ([PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)).
- Switching protocol on a tab after it is created (v1: close and open a
  new tab with the correct protocol).
- Changing how saved HTTP or WebSocket profiles open from Collections.
- Inbound MCP surfaces (**MCP Servers…**, **MCP Tool** checkbox, HTTP /
  WebSocket **MCP** sub-tabs).
- New outbound MCP operation metrics (`connect` / `list_tools` /
  `call_tool` counters) — those belong with the editor stories, not
  with new-tab protocol attribution.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Workspace tab** | One editor in the tab strip (HTTP, WebSocket, or MCP Client). |
| **Protocol picker** | Choice shown before a blank tab is created. |
| **HTTP Request** | Default protocol option; opens a blank HTTP draft. |
| **WebSocket** | Second protocol option; opens a blank WebSocket tab. |
| **MCP Client** | Third protocol option; starts outbound MCP client work. |
| **MCP Client placeholder tab** | Temporary non-HTTP confirm result until PYPOST-1166. |
| **New-tab source** | How the user asked: keyboard shortcut or tab-bar **+**. |
| **Chosen protocol** | HTTP, WebSocket, or MCP Client recorded with a completed choice. |

### Functional Requirements

#### FR-1: MCP Client is a picker choice

- FR-1.1 The protocol picker shown on `Ctrl+N` and tab-bar **+** offers
  exactly three protocols in this story: **HTTP Request**, **WebSocket**,
  **MCP Client**.
- FR-1.2 **MCP Client** is the third item (after **WebSocket**).
- FR-1.3 `Ctrl+N` and **+** continue to share one choose-then-open
  sequence. MCP Client is not a separate File menu or Collections-only
  path in this story.

#### FR-2: HTTP Request remains the default

- FR-2.1 **HTTP Request** remains the first option in the protocol picker.
- FR-2.2 **HTTP Request** remains the default selection when the picker
  appears.
- FR-2.3 Choosing **HTTP Request** still opens a blank HTTP request tab.

#### FR-3: Cancel and existing protocols are unchanged

- FR-3.1 If the user dismisses the picker without choosing a protocol,
  no new tab is created and no new-tab metric is recorded.
- FR-3.2 Choosing **WebSocket** still opens a blank WebSocket tab, not
  an HTTP request tab.
- FR-3.3 Opening a saved HTTP or WebSocket profile from Collections
  stays on the existing saved-profile path (not the blank-tab picker).

#### FR-4: Confirming MCP Client is a distinct tab outcome

- FR-4.1 The user can choose **MCP Client** from the picker on `Ctrl+N`
  and on **+**.
- FR-4.2 Choosing **MCP Client** opens a new workspace tab that is **not**
  an HTTP request tab and is **not** a WebSocket tab.
- FR-4.3 That tab may be a placeholder. The dedicated MCP Client draft
  shell is PYPOST-1166; this story does not ship that editor's contents.
- FR-4.4 Confirming **MCP Client** must not silently open HTTP. Today a
  non-WebSocket confirm becomes HTTP; that fallback is unacceptable once
  MCP Client is a real choice.

#### FR-5: Protocol identity and telemetry

- FR-5.1 The product has a named blank-tab protocol identity for MCP
  Client: `TabProtocol.MCP_CLIENT` with value `mcp_client`, peer to the
  existing HTTP and WebSocket identities.
- FR-5.2 When the user completes a new-tab action by choosing MCP
  Client, product telemetry records **source** as `shortcut` (`Ctrl+N`)
  or `plus_button` (tab-bar **+**) and **protocol** as `mcp_client`.
- FR-5.3 `mcp_client` must be recorded as itself, not normalized to
  `unknown` or `http`.
- FR-5.4 Telemetry must not include request bodies, URLs, headers, or
  other payload content from this action (there is no URL yet).
- FR-5.5 Cancel still emits no new-tab metric.

### Non-Functional Requirements

- **NFR-1 Keyboard:** Because `Ctrl+N` is a keyboard action, the
  three-item picker must remain usable without a mouse (focus, move
  between options, confirm, dismiss). HTTP remains the Enter default.
- **NFR-2 Discoverability:** A user looking for outbound MCP client
  work must see an **MCP Client** option when they open a new tab via
  `Ctrl+N` or **+**.
- **NFR-3 Default path cost:** Choosing the default **HTTP Request**
  must remain a short confirmation of the first option.
- **NFR-4 Labels:** Protocol identity uses the names **HTTP Request**,
  **WebSocket**, and **MCP Client**, not color alone. Prefer "MCP Client"
  over unqualified "MCP" (outbound vs inbound disambiguation).
- **NFR-5 Telemetry:** New-tab counts stay attributable by source and
  protocol, including `mcp_client` (see FR-5).

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on: [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)
  (Done; picker with HTTP then WebSocket already ships).
- Architecture pointer for later steps:
  `ai-tasks/PYPOST-1164/20-architecture.md` (research decomposition).
  This story still runs its own Step 2.
- HTTP, WebSocket, and MCP Client remain separate editor experiences;
  this story adds a **choice at creation**, not a merged editor.
- v1 default blank-tab protocol is **HTTP**; MCP Client is explicit.
- v1 does not support switching protocol on an already open tab.
- A placeholder confirm tab for MCP Client is in scope; the draft shell
  is PYPOST-1166.
- User-facing copy of the picker uses **HTTP Request**, **WebSocket**,
  and **MCP Client**.

## Q&A

- **Why add MCP Client to this picker instead of a new menu?**
  Research (PYPOST-1164) chose one blank-tab entry point so HTTP,
  WebSocket, and MCP Client start the same way. A second creation path
  would split `Ctrl+N` / **+** and hide MCP Client from the documented
  new-tab habit.

- **Why is HTTP still the default?**
  Matches today's blank-tab behavior and PYPOST-1157. MCP Client is
  opt-in at creation.

- **What if the user cancels?**
  No tab is created; workspace and metrics stay as they were.

- **What happens when the user confirms MCP Client?**
  A new **non-HTTP** workspace tab opens. A placeholder is enough; the
  dedicated draft shell is PYPOST-1166.

- **Does this story ship the MCP Client editor?**
  No. That is PYPOST-1166. This story ships the choice, the protocol
  identity, metrics, and a distinguishable confirm outcome.

- **Why might this story need a temporary stub tab?**
  Confirming MCP Client must not fall through to HTTP. Until PYPOST-1166
  provides the real draft shell, a placeholder tab is the same pattern
  PYPOST-1157 used for WebSocket (placeholder tab; full draft in
  PYPOST-1158). PYPOST-1166 **replaces** that stub; it does not invent
  the picker item.

- **Is HTTP method MCP removed here?**
  No. Migration/removal is a later story (MCP-TM-6). This story does
  not change inbound MCP surfaces either.

- **Can the user switch protocol after the tab opens?**
  Not in v1. Close the tab and open a new one with the correct protocol.

- **Do Collections-opened profiles go through the picker?**
  No. Saved HTTP and WebSocket profiles keep the existing open path.

- **Must `Ctrl+N` and `+` behave the same?**
  Yes. One shared choose-then-open flow; MCP Client is a third option
  on that flow, not a new flow.

- **Why name `TabProtocol.MCP_CLIENT` / `mcp_client` in requirements?**
  So picker, confirm routing, and new-tab telemetry share one protocol
  identity. Without it, MCP Client can be mis-attributed as HTTP or
  `unknown`, and later stories have no stable protocol to extend.

## References

- [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) — WS-TM-1 picker (Done)
- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — MCP Client UX research
- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — blank MCP Client draft shell
- `ai-tasks/PYPOST-1164/10-requirements.md` — FR-1.1 / MCP-TM-1
- `ai-tasks/PYPOST-1164/20-architecture.md` — architecture pointer for Step 2
- `ai-tasks/PYPOST-1157/10-requirements.md` — two-item picker baseline
