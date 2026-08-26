# PYPOST-1169: Tool discovery and browser UI after Connect

## Goals

[PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) (MCP-TM-2)
already gives the MCP Client tab URL, Connect / Disconnect, connection
state, and an empty tool browser. [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)
(MCP-TM-5) already lets the user attach environment-resolved headers so a
protected server can authenticate the outbound session.

Connect still only changes local chrome. It does not talk to the remote
MCP server. The tool browser stays empty even when the user believes they
are connected. Developers cannot see which tools the server actually
offers.

This story (MCP-TM-3) is the first **live outbound** step on that tab:

1. Connect must reach the remote MCP server and ask it for its tool list.
2. The existing tool browser must show each tool's **name** and
   **description**.
3. If Connect fails, the user must see the failure — not a fake connected
   state with an empty list.

The business goal is a trustworthy connect-and-discover loop: after
Connect, the user knows whether the server answered and which tools it
advertises. Invoke (arguments form and result pane) is still later
(MCP-TM-4).

## User Stories

- As a **developer testing a remote MCP server**, I want Connect to
  discover the server's tools, so I can see what the endpoint offers
  without encoding a list-tools probe in an HTTP request body.
- As a **user looking at the tool browser**, I want each tool shown with
  its name and description, so I can tell tools apart before I invoke
  one.
- As a **user whose Connect fails**, I want a clear error in the tab, so
  I know the session is not connected (network, timeout, auth, or
  protocol problems).
- As a **user already connected**, I want to refresh the tool list, so I
  can pick up tools the server added without disconnecting.
- As a **user whose refresh fails**, I want to stay connected with the
  last-known tool list and see an error, so a bad re-list does not look
  like a failed Connect (disconnected, empty tools).
- As a **user authenticating with headers**, I want Connect to send the
  same resolved headers and URL already configured on the tab, so a
  header-gated server lists tools instead of rejecting the session.
- As an **HTTP-first user**, I want HTTP and WebSocket tabs unchanged, so
  this story only makes MCP Client Connect live.

## Definition of Done

PYPOST-1169 is done when:

1. Connect on the MCP Client tab talks to the remote MCP server and
   requests its tool list (`list_tools`).
2. After a successful Connect, the tool browser lists those tools with
   **name** and **description** (empty list is valid if the server has
   none).
3. Connect failures are shown to the user; the tab does not stay
   "connected" when discovery failed.
4. The user can refresh the tool list while connected. A failed refresh
   is shown in the tab, but it is **not** the same outcome as a failed
   Connect: the session **stays connected**, the previous tool list is
   **kept as last-known (stale, not cleared)**, and chrome stays
   **connected with an error** (not disconnected).
5. Disconnect (and closing the tab) still ends the outbound session;
   the tool browser is empty again when disconnected.
6. Resolved URL and headers from PYPOST-1167 are used on Connect (and
   refresh). Blank HTTP / WebSocket tabs, inbound MCP surfaces, picker,
   draft restore exclusion, and headers-table chrome stay unchanged.
7. Selecting a tool to fill arguments and invoke remains out of scope
   (MCP-TM-4).

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

Users can open an MCP Client draft, type a URL, set headers, and click
Connect. The chrome then looks connected, but nothing reached the remote
server. Competitive tools (Postman MCP request, MCP Inspector) treat
Connect as **load capabilities**: initialize the session and show tools.

Without this story:

- Connect is a misleading local toggle.
- The reserved tool browser never fills.
- Users fall back to HTTP method **MCP** with an empty body to list
  tools.
- MCP-TM-4 has no discovered tools to invoke.

### Business Need

Connect must be a real outbound action: reach the server, discover tools,
and show name/description in the browser. Failures must be visible.
Headers already on the tab must go with that call.

### Boundary with PYPOST-1166, PYPOST-1167, and later stories

| Concern | 1166 | 1167 | This story | Later |
| --- | --- | --- | --- | --- |
| Draft shell (URL, Connect, state, empty tools) | In scope | Present | Present | Unchanged |
| Headers + `{{ variable }}` on outbound calls | Out | In scope | **Used** on Connect | Unchanged |
| Live `list_tools` after Connect | Out | Out | **In scope** | Unchanged |
| Tool browser filled with name / description | Out | Out | **In scope** | Unchanged |
| Connect / refresh error messaging | Out | Out | **In scope** | Unchanged |
| Refresh tool list while connected | Out | Out | **In scope** | Unchanged |
| Invoke form / result pane | Out | Out | Out | MCP-TM-4 |
| Input schema shown for a selected tool | Out | Out | Out | MCP-TM-4 |
| Remove HTTP method **MCP** | Out | Out | Out | MCP-TM-6 |
| Collections save of discovered tools | Out | Out | Out | MCP-TM-7 |

**Shell rule:** this story **fills the existing tool browser** on the
existing MCP Client workspace. It must not invent a second tab kind.
Connect chrome from 1166 stays; this story makes Connect talk to the
server.

### Scope (this task)

- Connect reaches the remote MCP server and discovers tools
  (`list_tools`).
- Successful discovery populates the tool browser with each tool's name
  and description.
- An empty successful list is shown as empty tools, not as an error.
- Connect errors are visible to the user (including empty URL, network,
  timeout, auth, and protocol failures as the product already
  distinguishes them for the user).
- Connection state reflects the real outcome: connected only after
  successful discovery; failed Connect leaves the session not connected.
- Refresh re-discovers tools on a connected session without requiring a
  full Disconnect + Connect for a new list. A failed refresh leaves the
  session connected, keeps the previous list as last-known (stale), and
  shows an error — it does not drop to the failed-Connect (disconnected)
  chrome.
- Disconnect clears the tool list and returns the tab to disconnected.
- Connect (and refresh) use the tab's resolved URL and resolved headers.
- Keep picker, draft restore exclusion, close-releases-session, and
  headers table as shipped.

### Out of Scope

- Interactive `call_tool`, schema-guided argument forms, and result pane
  — MCP-TM-4 ([PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)).
- Showing input schema in the browser as a required field of this story
  (name and description are enough for discovery).
- Migrating or removing HTTP method **MCP** — MCP-TM-6
  ([PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171)).
- Save / Save As, Collections tree items, restore of **saved** profiles
  — MCP-TM-7 ([PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)).
- User documentation rewrite — MCP-TM-8
  ([PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)).
- Changing the protocol picker, default HTTP choice, or new-tab counting.
- Switching protocol on a tab after it is created.
- Inbound MCP surfaces (**MCP Servers…**, **MCP Tool** checkbox, HTTP /
  WebSocket **MCP** sub-tabs).
- Prompts, resources, protocol trace, SSE, or stdio transports.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **MCP Client workspace** | Dedicated outbound MCP Client editor. |
| **Remote MCP server** | Endpoint the user connects to by URL. |
| **Outbound session** | Live client session after successful Connect. |
| **Connect** | User action that starts the session and discovers tools. |
| **Disconnect** | User action that ends the session and clears tools. |
| **Refresh** | User action that re-lists tools on a connected session. |
| **Remote MCP tool** | One advertised tool: name and description. |
| **Tool browser** | List of discovered remote tools in the tab. |
| **Connect error** | User-visible reason Connect failed (session not connected). |
| **Refresh error** | User-visible reason a re-list failed while still connected; last-known tools remain. |
| **Connection state** | Visible idle / connecting / connected / failed. |
| **Resolved URL / headers** | Address and auth after environment templating. |

### Functional Requirements

#### FR-1: Connect discovers remote tools

- FR-1.1 Connect on the MCP Client tab contacts the remote MCP server
  using the tab's resolved URL.
- FR-1.2 That Connect requests the server's tool list (`list_tools`).
- FR-1.3 Connect sends the tab's resolved connection headers with that
  outbound work (PYPOST-1167).
- FR-1.4 Connect with an empty or unusable URL does not succeed; the
  user sees an error instead of a connected empty session.

#### FR-2: Tool browser shows name and description

- FR-2.1 After a successful Connect, the tool browser lists every
  returned tool.
- FR-2.2 Each listed tool shows its **name** and **description**.
- FR-2.3 If the server returns no tools, the browser is empty and that
  is success, not a Connect error.
- FR-2.4 While the tab is disconnected, the tool browser is empty (no
  leftover tools from a previous session).

#### FR-3: Failures are visible; state matches reality

- FR-3.1 Connect failures are shown to the user in the tab.
- FR-3.2 A failed Connect does not leave the tab in a connected state.
- FR-3.3 While Connect is in progress, the user can tell work is
  underway (not an instant fake success).
- FR-3.4 Hidden environment values stay masked in any error or status
  text (same product rule as HTTP and header preview).

#### FR-4: Refresh and Disconnect

- FR-4.1 While connected, the user can refresh the tool list without
  Disconnect.
- FR-4.2 Refresh talks to the same remote session's server and updates
  name/description in the browser.
- FR-4.3 A failed refresh is shown to the user in the tab. It is **not**
  a failed Connect (FR-3.2). Explicit outcome:
  - **Session:** stays connected. Refresh does not end the outbound
    session or leave the tab disconnected.
  - **Tool list:** the previous list is **kept** as last-known tools. It
    is **not cleared**. It is **stale**: the user must not treat it as a
    successful refresh. The visible refresh error is how the product
    marks that the list is not freshly confirmed.
  - **Chrome:** stays **connected with an error**. It must not match a
    failed Connect (not connected, empty tool browser).
- FR-4.4 Disconnect ends the outbound session, clears the tool browser,
  and returns connection state to disconnected.
- FR-4.5 Closing the tab still releases the outbound session
  (PYPOST-1166).

#### FR-5: Existing surfaces stay the same

- FR-5.1 HTTP and WebSocket tabs stay unchanged.
- FR-5.2 Picker, MCP Client draft chrome layout, unsaved-draft restore
  exclusion, and headers table stay as shipped.
- FR-5.3 Inbound MCP surfaces stay unchanged.
- FR-5.4 HTTP method **MCP** is not removed in this story.

### Non-Functional Requirements

- **NFR-1 Trust:** Connected means Connect succeeded (the server
  answered discovery). The chrome must not look connected after a
  **failed Connect**. A later **failed refresh** does not revoke
  connected: the user stays connected with an error and last-known
  tools, not a fake “fresh” list.
- **NFR-2 Discoverability:** After Connect, tools are visible without
  knowing the empty-body HTTP method **MCP** convention.
- **NFR-3 Consistency:** Connect → list tools matches how Postman /
  Inspector load capabilities, at name/description depth for v1.
- **NFR-4 Security:** Hidden environment keys stay masked in UI and
  logs (same policy as HTTP and MCP proxy sanitization).
- **NFR-5 Responsiveness:** The tab stays usable while Connect or
  refresh runs; the user is not left with a frozen window and no
  status.
- **NFR-6 Naming:** User-visible labels prefer **MCP Client**,
  **Connect**, **Disconnect**, and a clear refresh control over
  unqualified **MCP**.
- **NFR-7 Telemetry:** Connect and list-tools actions should be
  attributable separately from inbound MCP request counts (product
  telemetry already planned in research; this story is the first live
  outbound connect/list).

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on: [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
  and [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)
  (both Done).
- Parent product spec: `ai-tasks/PYPOST-1164/10-requirements.md`
  FR-2.2 (Connect discovers tools; browser shows name and description).
- Architecture pointer for later steps:
  `ai-tasks/PYPOST-1164/20-architecture.md` (research decomposition).
  This story still runs its own Step 2.
- v1 transport remains Streamable HTTP remote URLs.
- v1 discovery is tools only (`list_tools`); prompts and resources are
  later.
- User-facing copy uses **MCP Client**, **Connect**, **Disconnect**.

## Q&A

- **Why is this not part of PYPOST-1166?**
  1166 is the draft shell: chrome without a live server. This story is
  the first outbound round-trip so Connect can ship after the shell.

- **Why is this not part of PYPOST-1167?**
  1167 is auth headers and templating. Discovery is a separate user
  goal: see the remote catalog. Connect here must **use** those
  resolved headers.

- **Does Connect have to invoke a tool?**
  No. Invoke is MCP-TM-4. This story stops at listing name and
  description.

- **Must the browser show input schema?**
  No. Jira acceptance is name and description. Schema-guided forms are
  MCP-TM-4.

- **What if the server has no tools?**
  Success with an empty browser. That is not a Connect error.

- **Is Refresh required? Jira only lists Connect.**
  Yes for this story. Research MCP-TM-3 includes refresh so the user
  can reload capabilities without tearing down the session. See
  `ai-tasks/PYPOST-1164/20-architecture.md` (MCP-TM-3 acceptance).

- **Does a failed refresh disconnect like a failed Connect?**
  No. Failed Connect means the session never started: not connected,
  empty tools (FR-3.2). Failed refresh happens on an already connected
  session: stay connected, keep last-known tools as stale, show a
  refresh error. Chrome must not look like a failed Connect.

- **Can Connect succeed locally without contacting the server?**
  No. That is the defect this story removes.

- **Does this change inbound MCP Servers Tools…?**
  No. That catalog is tools PyPost exposes. This browser lists tools
  on the **remote** server the user connected to.

- **How do Jira acceptance-criteria names map to this document?**
  Jira AC aliases (not requirements of their own):
  - Connect triggers `list_tools` against the remote MCP server —
    FR-1.
  - Tool list populated with name/description — FR-2.
  - Connect errors surfaced to the user — FR-3.

## References

- [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169) — this
  story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent
  epic
- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — MCP-TM-2
  draft shell (Done)
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — MCP-TM-5
  headers / templating (Done)
- [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170) — MCP-TM-4
  invoke (out of scope)
- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — MCP
  Client UX research
- `ai-tasks/PYPOST-1164/10-requirements.md` — FR-2.2 discovery
- `ai-tasks/PYPOST-1164/20-architecture.md` — MCP-TM-3 acceptance;
  Step 2 pointer
- `ai-tasks/PYPOST-1166/10-requirements.md` — shell vs live Connect
- `ai-tasks/PYPOST-1167/10-requirements.md` — headers used on Connect
