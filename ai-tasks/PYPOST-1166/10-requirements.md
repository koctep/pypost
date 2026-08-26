# PYPOST-1166: Blank MCP Client draft tab shell

## Goals

[PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) (MCP-TM-1) already
lets a user choose **MCP Client** from `Ctrl+N` and tab-bar **+**. Confirming
that choice opens a distinct non-HTTP workspace tab. That tab is still a
placeholder: it is recognizably not an HTTP request, but it does not yet look
or behave like an MCP Client editor.

This story (MCP-TM-2) is the editor **draft shell** for that same tab kind.
After the user chooses **MCP Client**, they must land on an unsaved outbound
MCP Client workspace: a place to type a server URL, see Connect and Disconnect,
see connection state, and see where discovered tools will appear — even though
tool discovery and invoke come later.

The business goal is a first-class blank MCP Client session that matches how
blank HTTP and WebSocket drafts already work: create first, save later, and
do not resurrect unsaved drafts after restart. Closing the tab must end any
outbound session so a closed draft does not leave a live connection behind.

This story does not ship tool listing, invoke, headers, or Collections save.
Those are later MCP-TM stories.

## User Stories

- As a **developer testing a remote MCP server**, I want the tab that opens
  when I choose **MCP Client** to show a URL field, Connect / Disconnect, a
  connection state indicator, and an empty tool browser, so I can start
  outbound MCP work without using the HTTP request editor.
- As a **user who just opened a blank MCP Client tab**, I want the tab titled
  like a new MCP Client draft with an empty URL, so it is clearly unsaved
  and not a leftover HTTP request.
- As a **user who has not saved yet**, I want that draft omitted from session
  restore, so restarting PyPost does not reopen an unsaved MCP Client tab
  (same rule as unsaved WebSocket drafts).
- As a **user who closes an MCP Client tab**, I want the outbound session
  released, so closing the tab does not leave a connection running.
- As an **HTTP-first user**, I want HTTP and WebSocket blank tabs unchanged,
  so filling in the MCP Client shell does not alter my existing new-tab paths.
- As a **user who still needs list/call later**, I want the tool browser
  present but empty in this story, so later discovery can fill it without
  changing the tab kind again.

## Definition of Done

PYPOST-1166 is done when:

1. Opening a blank MCP Client tab creates an **MCP Client workspace**, not an
   **HTTP request workspace** (and not a WebSocket tab).
2. That tab is the dedicated MCP Client draft shell: tab title **New MCP
   Client**, empty URL bar, **Connect** and **Disconnect** controls, a
   connection state indicator, and an empty tool-browser placeholder.
3. The draft is excluded from session restore until the user first saves it
   to a collection (save itself is a later story; this story only enforces
   the unsaved-draft exclusion).
4. Closing the tab releases the outbound session for that draft so a closed
   tab does not leave a live connection behind (FR-4.2).
5. Confirming **MCP Client** from `Ctrl+N` / **+** still opens this same MCP
   Client workspace kind — the PYPOST-1165 placeholder contents are replaced,
   not a second tab type.
6. Blank HTTP and WebSocket tabs, Collections-opened HTTP/WebSocket items,
   and HTTP method **MCP** are unchanged.
7. The tab still counts as a real workspace tab (an MCP-Client-only tab
   strip is not treated as empty).

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

Users can already choose **MCP Client** at blank-tab creation, but the
confirm tab is a stub. They cannot enter a server URL, see connection
controls, or see where tools will appear. Competitive tools (Postman MCP
request, MCP Inspector) show that chrome as soon as the MCP request type
opens — connect is explicit; tools are a dedicated area.

Without a draft shell:

- The picker choice does not lead to a usable outbound MCP workspace.
- Later stories (discovery, invoke, headers, save) have no editor surface
  to attach to.
- Unsaved-draft restore rules and close/session-release contracts are
  undefined for this tab kind, unlike HTTP and WebSocket drafts.

### Business Need

A blank MCP Client tab must be an unsaved **session workspace**, not an
HTTP request and not a labeled empty page. Users need the connection bar
and an empty tool browser now; they do not yet need live tool listing or
invoke. Session restore must ignore the draft until first save. Closing
the tab must release the outbound session.

### Boundary with PYPOST-1165 and later stories

PYPOST-1165 and this story split the same way PYPOST-1157 and PYPOST-1158
split WebSocket: **choice first**, **draft editor second**.

| Concern | PYPOST-1165 | PYPOST-1166 | Later |
| --- | --- | --- | --- |
| Picker item **MCP Client** | In scope | Already present | Unchanged |
| Picker, identity, new-tab counting | In scope | Stay as shipped in 1165 | Unchanged |
| Distinct non-HTTP confirm tab | Placeholder MCP Client tab | Same kind, draft chrome | Same kind |
| URL bar, Connect / Disconnect, state | Out of scope | **In scope** | Unchanged |
| Empty tool-browser placeholder | Out of scope | **In scope** | MCP-TM-3 fills it |
| Draft excluded from session restore | Out of scope | **In scope** | Saved: MCP-TM-7 |
| Release outbound session on close | Out of scope | **In scope** | Unchanged |
| Live tool listing / refresh / errors | Out of scope | Out of scope | MCP-TM-3 |
| Invoke / result pane | Out of scope | Out of scope | MCP-TM-4 |
| Outbound headers / `{{ vars }}` | Out of scope | Out of scope | MCP-TM-5 |
| Collections save/open | Out of scope | Out of scope | MCP-TM-7 |

**Shell rule:** this story **replaces placeholder contents inside the
existing MCP Client workspace kind**. It must not silently open HTTP. It
must not invent a second confirm outcome.

Picker, identity, and new-tab counting stay as shipped in PYPOST-1165.
This story does not invent or require new counting keys.

### Scope (this task)

- Fill the blank MCP Client workspace with draft-shell chrome: empty URL
  bar, Connect / Disconnect, connection state indicator, empty tool
  browser placeholder.
- Opening a blank MCP Client tab still yields an MCP Client workspace, not
  an HTTP request workspace.
- Title the new draft **New MCP Client**.
- Exclude the unsaved draft from session restore until first save.
- Closing the tab releases any outbound session for that draft.
- Preserve picker, identity, new-tab counting, HTTP confirm, WebSocket
  confirm, and cancel from PYPOST-1165.
- Keep an open MCP Client tab counted as a real workspace tab.

Connect / Disconnect and the state indicator must be **visible and usable
as chrome**. Live initialize and tool listing (populating the browser) is
MCP-TM-3. Invoke may no-op until MCP-TM-4. A disconnected (or equivalent
idle) initial state is enough.

### Out of Scope

- Tool discovery (`list_tools`), refresh, and connect-failure messaging —
  MCP-TM-3 ([PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)).
- Interactive `call_tool`, schema forms, and result pane — MCP-TM-4
  ([PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)).
- Outbound headers table and environment templating — MCP-TM-5
  ([PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)).
- Migrating or removing HTTP method **MCP** — MCP-TM-6
  ([PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171)).
- Save / Save As, Collections tree items, restore of **saved** profiles —
  MCP-TM-7 ([PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)).
  This story only excludes **unsaved** drafts from restore.
- User documentation rewrite — MCP-TM-8
  ([PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)).
- Changing the protocol picker, default HTTP choice, or new-tab counting.
- Switching protocol on a tab after it is created.
- Changing how saved HTTP or WebSocket profiles open from Collections.
- Inbound MCP surfaces (**MCP Servers…**, **MCP Tool** checkbox, HTTP /
  WebSocket **MCP** sub-tabs).
- New outbound operation metrics (`connect` / `list_tools` / `call_tool`
  counters) — those belong with MCP-TM-3 / MCP-TM-4.
- Close-last-tab / empty-workspace picker —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Workspace tab** | One editor in the strip (HTTP, WebSocket, or MCP Client). |
| **MCP Client workspace** | Dedicated outbound MCP Client editor (peer of HTTP). |
| **HTTP request workspace** | HTTP editor; must not be the MCP Client confirm result. |
| **MCP Client draft** | Unsaved outbound MCP Client session in a workspace tab. |
| **URL bar** | Remote MCP server URL field (empty on a new draft). |
| **Connect / Disconnect** | Explicit controls to start or end the outbound session. |
| **Connection state** | Visible idle / connected / disconnected (or equivalent). |
| **Tool browser placeholder** | Empty area reserved for discovered remote tools. |
| **Outbound session** | Live client session for the tab; released on close. |
| **Session restore** | Startup reopen of tabs; unsaved drafts are omitted. |

### Functional Requirements

#### FR-1: Blank MCP Client tab is the MCP Client editor, not HTTP

- FR-1.1 Opening a blank MCP Client tab creates an **MCP Client workspace**.
- FR-1.2 That workspace is not an **HTTP request workspace** and not a
  WebSocket tab.
- FR-1.3 Choosing **MCP Client** from `Ctrl+N` or **+** still opens the
  same MCP Client workspace kind, now with draft chrome.
- FR-1.4 The tab strip title for a new draft is **New MCP Client**.

#### FR-2: Draft-shell chrome

- FR-2.1 The tab presents an empty URL bar for the remote server address.
- FR-2.2 The tab presents **Connect** and **Disconnect** controls.
- FR-2.3 The tab presents a connection state indicator. A new draft starts
  disconnected (idle), not connected.
- FR-2.4 The tab presents a tool-browser placeholder that is empty (no
  discovered tools in this story).
- FR-2.5 The shell is visually an MCP Client workspace (URL + connection
  chrome + tool area), not the HTTP method dropdown path and not the
  inbound **MCP** sub-tab.

#### FR-3: Unsaved drafts are not restored

- FR-3.1 An unsaved MCP Client draft is excluded from session restore
  until the user first saves it to a collection.
- FR-3.2 Restarting with only unsaved MCP Client drafts open must not
  reopen those drafts (same product rule as unsaved WebSocket drafts).
- FR-3.3 This story does not persist the draft to a collection. First save
  is MCP-TM-7; until then every blank MCP Client tab is a draft.

#### FR-4: Close releases the outbound session

- FR-4.1 Closing the MCP Client tab ends that tab's outbound work.
- FR-4.2 Closing the tab releases the outbound MCP session for that tab so
  a closed draft does not keep a connection alive.
- FR-4.3 An open MCP Client tab still counts as a real workspace tab, so
  close-last-tab logic does not treat an MCP-Client-only strip as empty
  and auto-open HTTP.

#### FR-5: Existing protocols stay the same

- FR-5.1 Choosing **HTTP Request** still opens a blank HTTP request tab.
- FR-5.2 Choosing **WebSocket** still opens a blank WebSocket tab.
- FR-5.3 Dismissing the picker still creates no tab.
- FR-5.4 Opening saved HTTP or WebSocket items from Collections is
  unchanged. HTTP method **MCP** is unchanged.

### Non-Functional Requirements

- **NFR-1 Consistency:** The blank MCP Client draft should feel analogous
  to blank HTTP and WebSocket drafts: named new tab, empty address,
  optional later save, no restore until save.
- **NFR-2 Discoverability:** After choosing **MCP Client**, the user must
  see URL and connection chrome without knowing HTTP method **MCP**.
- **NFR-3 Naming:** User-visible labels prefer **MCP Client** over
  unqualified **MCP** (outbound vs inbound).
- **NFR-4 Session hygiene:** Closing the tab must not leak an outbound
  session (FR-4).
- **NFR-5 Keyboard:** URL field and Connect / Disconnect remain reachable
  in the tab; this story does not add new global hotkeys.

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on: [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)
  (Done; placeholder MCP Client workspace and picker item already ship).
- Architecture pointer for later steps:
  `ai-tasks/PYPOST-1164/20-architecture.md` (research decomposition).
  Parent product spec:
  `ai-tasks/PYPOST-1165/10-requirements.md` (placeholder vs this shell).
  This story still runs its own Step 2.
- Pattern analog: WebSocket blank draft (WS-TM-2 / PYPOST-1158): unsaved
  draft chrome + restore exclusion.
- HTTP, WebSocket, and MCP Client remain separate editor experiences.
- v1 does not support switching protocol on an already open tab.
- Connect chrome is in scope; populating tools from a live server is not.
- User-facing copy uses **MCP Client**, **Connect**, **Disconnect**,
  **New MCP Client**.

## Q&A

- **Why is this not part of PYPOST-1165?**
  Same split as WebSocket: the picker must not silently open HTTP, but the
  dedicated editor is a separate story. 1165 shipped a distinguishable
  stub; 1166 fills the draft shell.

- **Does Connect have to talk to a real MCP server here?**
  No. Controls and state must be present. Live initialize and tool listing
  is MCP-TM-3. A new draft starts disconnected.

- **Why an empty tool browser if tools are later?**
  So the user sees where discovery will land, and MCP-TM-3 fills an
  existing surface instead of inventing a new tab layout.

- **Are unsaved drafts restored after restart?**
  No. Same rule as unsaved WebSocket drafts (PYPOST-1156 FR-2.5 /
  PYPOST-1164 FR-4.3). Saved-profile restore is MCP-TM-7.

- **Why release the session on close if Connect may not fully connect yet?**
  Closing the tab must always release session resources. If the user
  connected (now or in a later story on the same tab kind), close must
  not leave the session running. The business outcome is FR-4.2.

- **Can the user save the draft in this story?**
  No. Save / Save As is MCP-TM-7. Until then the tab is always a draft
  and must stay out of session restore.

- **Does this change `Ctrl+N` / `+` counting or picker items?**
  No. Picker, identity, and new-tab counting stay as shipped in
  PYPOST-1165.

- **Is HTTP method MCP removed here?**
  No. Migration is MCP-TM-6. Inbound MCP surfaces are unchanged.

- **Can the user switch this tab to HTTP after it opens?**
  Not in v1. Close the tab and open a new one with the correct protocol.

- **How do Jira acceptance-criteria names map to this document?**
  Jira AC aliases (not requirements of their own):
  - `add_blank_mcp_client_tab()` creates **McpClientTab** (not
    **RequestTab**) — FR-1.1 / FR-1.2 (MCP Client workspace vs HTTP
    request workspace).
  - Draft tab excluded from session restore until first save — FR-3.
  - `close_tab` calls `presenter.teardown()` — alias for FR-4.2 (closing
    the tab releases the outbound session).

## References

- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) — MCP-TM-1 picker + stub (Done)
- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — MCP Client UX research
- `ai-tasks/PYPOST-1164/10-requirements.md` — FR-2.1 chrome; FR-4.3 draft restore
- `ai-tasks/PYPOST-1164/20-architecture.md` — MCP-TM-2 acceptance; architecture pointer
- `ai-tasks/PYPOST-1165/10-requirements.md` — placeholder vs draft-shell split
- `ai-tasks/PYPOST-1165/20-architecture.md` — stub MCP Client workspace; 1166 fills chrome
- Jira AC aliases: `add_blank_mcp_client_tab()` / **McpClientTab** / **RequestTab**;
  `close_tab` / `presenter.teardown()` maps to FR-4.2
