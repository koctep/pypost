# PYPOST-1164: Research and decompose MCP client tab mode UX

## Goals

Epic [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) (blank-tab protocol selector)
adds a user-facing choice between HTTP Request and WebSocket when opening a workspace tab
([PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) research, implementation stories
PYPOST-1157 … PYPOST-1163). During that research, user feedback identified a third protocol gap:
**outbound MCP client** workflows are not represented as a workspace tab mode.

Today, calling a remote MCP server interactively is possible only through a hidden affordance —
the **MCP** item in the HTTP request method dropdown (`doc/user/requests.md` L6–7). That path uses
`MCPClientService` for a single-shot `list_tools` (empty body) or `call_tool` (JSON body with
`name` / `arguments`). It shares the HTTP request editor chrome (Params, Headers, Body, Script,
**MCP** sub-tab for *inbound* tool exposure). The naming collision between outbound client calls
and inbound "Expose as MCP Tool" metadata confuses users and blocks a first-class MCP exploration
workflow comparable to Postman's MCP request type or the official MCP Inspector.

Separately, PyPost already operates as an **inbound MCP server** (local collection tools and
upstream proxy via **MCP Servers…**) and exposes **MCP** sub-tabs on HTTP requests and WebSocket
profiles for agent-facing tool configuration. None of these surfaces provide an interactive
**outbound** client experience (connect → discover tools → invoke with schema-guided inputs →
inspect JSON-RPC results).

The business goal of PYPOST-1164 is to **research, specify, and decompose** MCP client tab mode
so a follow-up implementation epic can:

1. Add **MCP Client** as a third blank-tab protocol alongside HTTP and WebSocket.
2. **Migrate** the HTTP request method **MCP** into that dedicated mode (per user input during
   PYPOST-1156 grilling).
3. Clarify product boundaries between outbound client, inbound server, and proxy configuration.

## User Stories

- As a **developer testing a remote MCP server**, I want a dedicated MCP Client workspace tab,
  so that I can connect, list tools, and call them interactively without hacking the HTTP request
  body format.
- As a **PyPost user familiar with HTTP tabs**, I want MCP Client tabs to follow the same
  create → configure → send → inspect pattern as HTTP and WebSocket tabs, so that learning cost
  stays low.
- As a **developer evaluating a third-party MCP endpoint**, I want schema-guided argument forms
  generated from `list_tools`, so that I do not hand-author JSON `call_tool` payloads.
- As a **developer authenticating to MCP servers**, I want outbound connection headers resolved
  from my active environment, so that Bearer tokens and API keys work the same as HTTP requests.
- As a **collections user**, I want saved MCP client profiles openable from the sidebar, so that
  frequently tested servers are one click away (parity with HTTP requests and WebSocket profiles).
- As a **power user**, I want `Ctrl+N` and the tab-bar **+** to offer **MCP Client** alongside
  HTTP and WebSocket, so that ad-hoc MCP exploration does not require creating a collection item
  first.
- As a **developer migrating existing workflows**, I want collection items that used HTTP method
  **MCP** to open in the new MCP Client editor (or be migrated transparently), so that saved
  probes like `examples/collections/mcp.json` keep working.
- As a **developer configuring PyPost-as-server**, I want **MCP Servers…** and the request
  **MCP Tool** checkbox to remain clearly separate from outbound client tabs, so that inbound
  exposure and outbound testing are not conflated.
- As a **developer proxying upstream MCP**, I want to test the upstream interactively from a
  client tab without starting a PyPost proxy row, so that I can validate upstream behavior before
  wiring proxy configuration.
- As a **returning user**, I want MCP Client tab restore rules to be predictable (saved profiles
  vs unsaved drafts), so that session behavior matches HTTP and WebSocket expectations from
  PYPOST-1156.

## Definition of Done (PYPOST-1164 — research task)

PYPOST-1164 is done when:

1. All current MCP UX surfaces are audited and documented (audit table in Task Description).
2. Doc/code gaps are enumerated with severity.
3. MCP client tab mode is defined at product level vs existing surfaces (inbound server, proxy,
   HTTP method MCP, MCP sub-tabs).
4. Competitive/pattern notes and protocol-picker UX options are captured (business level).
5. Relationship to PYPOST-1157 … PYPOST-1163 blank-tab `TabProtocol` work is stated (product
   level — detailed architecture is Step 2).
6. Child implementation stories are proposed as a markdown table (Jira creation deferred).
7. `ai-tasks/PYPOST-1164/10-requirements.md` and `00-roadmap.md` exist and Step 1 remains
   `[/]` pending orchestrator review.

## Task Description

### Programming Language

Python is the implementation language for the PyPost desktop client (PySide6 UI, presenters,
core services) and automated test suites. English Markdown is used for workflow and user
documentation artifacts.

### Problem

PyPost ships outbound MCP client capability (`MCPClientService`, HTTP method **MCP**) and inbound
MCP server capability (**MCP Servers…**, proxy mode, collection tool exposure) but no workspace
tab mode for interactive outbound MCP client workflows. The HTTP method **MCP** overloads the
request editor, provides no tool browser, ignores configured Headers at runtime, supports only
`list_tools` / `call_tool` over Streamable HTTP, and shares the **MCP** sub-tab name with inbound
tool-exposure settings — the opposite direction of data flow.

### Scope (this task)

- Audit all MCP-related UX surfaces and the outbound `mcp_client_service` path.
- Document doc/code gaps.
- Define MCP client tab mode vs existing surfaces at a functional/product level.
- Capture competitive UX patterns and protocol-picker extension options (business only).
- State relationship to PYPOST-1157 … PYPOST-1163 protocol-picker work (product level).
- Propose child implementation stories (requirements scope only — architecture is Step 2).

### Out of scope (this task)

- UI implementation, code changes, or architecture decisions (Step 2+).
- Changes to inbound MCP server runtime (local collection server, proxy forwarding).
- Changes to WS-9 WebSocket MCP probe tools.
- stdio MCP transport in the desktop GUI (noted as a future consideration; desktop apps like
  Postman support stdio — PyPost has no stdio client path today).
- `list_prompts`, `get_prompt`, `list_resources`, `read_resource` in v1 client tab (noted as
  stretch / follow-up — competitive tools expose these; current `MCPClientService` does not).
- Jira issue creation for child stories (deferred to Step 2 / epic planning).

### MCP UX Surface Audit

PyPost uses "MCP" in several distinct product roles. The table below maps each surface, its
direction (inbound = PyPost acts as server; outbound = PyPost acts as client), and whether it
provides interactive outbound client UX.

| Surface | Entry point | Direction | User goal | Interactive outbound client? | Notes |
| --- | --- | --- | --- | --- | --- |
| **HTTP method MCP** | Request editor method combo → **MCP** | Outbound | Single `list_tools` or `call_tool` to a URL | **Partial** | Empty body → `list_tools`; JSON `{"name","arguments"}` → `call_tool`. Placeholder hints in `request_editor.py`. Executes via `RequestService._execute_mcp` → `MCPClientService`. |
| **Request MCP sub-tab** | Request editor → **MCP** tab + **MCP Tool** checkbox | Inbound | Configure PyPost-exposed tool (description, params, agent preview) | **No** | `expose_as_mcp`, `mcp_description`, `mcp_params`, `list_tools` contract preview. Unrelated to calling remote servers. |
| **WebSocket MCP sub-tab** | WebSocket editor → **MCP** tab | Inbound | Configure WS-9 probe tool exposure | **No** | `expose_as_mcp`, description, bounded probe preview. |
| **MCP Servers… dialog** | Environment bar → **MCP Servers…** | Inbound (config) | Manage PyPost-hosted endpoints (local collection or upstream proxy) | **No** | Add/Edit/Start/Stop rows; **Tools…** (local only, read-only catalog of collection `expose_as_mcp` requests); **Activity…** (inbound call log). Proxy rows cannot open Tools overview. |
| **MCP Server Tools…** | Environment bar button | Inbound (read-only) | Shortcut to scoped tool catalog | **No** | Opens manager for selected server's exposed tools. |
| **MCP Activity dialog** | MCP Servers → **Activity…** | Inbound (observability) | Review inbound `call_tool` / proxy traffic | **No** | Per-server activity log with sanitization. |
| **`MCPClientService`** | Used by HTTP method MCP only | Outbound | Protocol handshake + `list_tools` / `call_tool` | **Headless** | Streamable HTTP only; no headers param; new session per invocation; 25s total timeout. |
| **MCP Proxy runtime** | Started from MCP Servers proxy row | Inbound → outbound bridge | Forward agent traffic to upstream MCP | **No** | `MCPProxyServerImpl` — not an interactive tester; headers templated from environment. |
| **Collections — MCP method request** | Open saved request with `method: "MCP"` | Outbound (stored) | Re-run list/call probe | **Partial** | Opens HTTP `RequestTab`; same limitations as method MCP. Example: `examples/collections/mcp.json` "List Tools". |
| **Collections — MCP Tool flag** | `expose_as_mcp: true` on HTTP/WS items | Inbound (metadata) | Agent discovers tool when PyPost server runs | **No** | Consumed by inbound server / WS-9 probe — not client tab. |
| **Blank workspace tab** | `Ctrl+N`, **+** | — | Start new work | **No** | Always HTTP `RequestTab` today; WebSocket after PYPOST-1157…1158; no MCP Client path. |

### Supporting code facts (current state)

- `RequestEditor` method combo includes **MCP** alongside GET/POST/… (`request_editor.py` L97).
  Selecting MCP changes body placeholder to describe list/call JSON convention (L256–259).
- `RequestService._execute_mcp` renders URL, headers, and body from templates but passes **only
  the URL** to `MCPClientService.run` — resolved **Headers are not forwarded** to the MCP HTTP
  client (auth gap for protected MCP endpoints).
- `MCPClientService` supports only **Streamable HTTP** (`streamable_http_client`); no SSE
  upstream client path (contrast: `MCPProxyServerImpl` supports both upstream transports).
- Each **Send** on method MCP performs a full initialize + single operation; no persistent
  session or connection state in the UI.
- Params tab on method MCP requests is unused by `_execute_mcp` (URL query params are not the
  MCP transport concern; only templated URL string is used).
- Inbound **MCP** sub-tab on HTTP requests is visible regardless of method; a user on method MCP
  can still check **MCP Tool** — a confusing inbound/outbound mix on the same tab.
- `McpToolsOverviewDialog` lists tools PyPost **exposes**, not tools on a **remote** server.
- `doc/user/requests.md` documents method MCP in two lines; no interactive client workflow,
  tool browser, or migration path is described.
- `doc/user/mcp-tools.md` covers inbound exposure only; outbound client testing is out of scope.
- `doc/dev/mcp_integration.md` and `doc/dev/mcp_proxy.md` describe inbound server/proxy; outbound
  client is limited to `mcp_client_service.py` module docstring ("testing MCP endpoints").

### MCP Client Tab Mode — Product Definition

**MCP Client tab mode** is a distinct workspace editor for **outbound** interaction with a
remote MCP server over Streamable HTTP (v1 minimum). A user:

1. Opens a blank **MCP Client** tab (or a saved MCP client profile from Collections).
2. Enters the server URL (e.g. `http://127.0.0.1:1080/mcp`), optional auth headers, and
   connects.
3. Discovers tools via `list_tools` and browses name, description, and input schema.
4. Selects a tool, fills arguments via a schema-guided form (or raw JSON fallback).
5. Invokes `call_tool` and inspects the structured result in a response pane.
6. Optionally saves the connection profile to a collection for reuse.

**Not MCP Client tab mode** (remain separate product surfaces):

| Surface | Role | Why separate |
| --- | --- | --- |
| HTTP/WebSocket **MCP** sub-tab + **MCP Tool** checkbox | Inbound tool authoring for agents | Opposite data flow; rename consideration is a follow-up, not merged into client tab |
| **MCP Servers…** | PyPost as inbound server / proxy admin | Server lifecycle, ports, collection binding — not outbound exploration |
| **MCP Proxy** configuration | Bridge for external agents | Agents connect to PyPost; user does not "send" from proxy row |
| HTTP method **MCP** | Legacy outbound shortcut | **To be migrated** into MCP Client tab mode and removed from method dropdown |

### Boundary: MCP Client Tab vs HTTP Method MCP (migration intent)

Per user input (PYPOST-1164 Jira description): when MCP Client tab mode ships, HTTP method **MCP**
should be **retired** from the request editor. Functional migration requirements:

- Saved collection requests with `method: "MCP"` open as MCP Client tabs (or auto-convert on
  import/open).
- `list_tools` semantics (empty operation) and `call_tool` semantics (tool name + arguments)
  remain available without hand-encoding JSON in a Body tab.
- Existing examples (`examples/collections/mcp.json`) and contributor fixtures remain valid.

### Relationship to PYPOST-1157 … PYPOST-1163 (TabProtocol — product level)

[PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) / [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)
introduce blank-tab protocol selection with two choices today: **HTTP Request** and **WebSocket**
(`TabProtocol.REQUEST`, `TabProtocol.WEBSOCKET` — naming from Step 2 architecture).

**Product-level relationship:**

1. **MCP Client is the third `TabProtocol` choice** in the same blank-tab picker:
   **HTTP Request | WebSocket | MCP Client** (exact labels deferred to Step 2).
2. **Implementation depends on WS-TM-1 (PYPOST-1157)** — the protocol picker and
   `open_blank_tab(protocol, source)` entry point must exist before adding a third option; MCP
   stories should not fork a second picker.
3. **MCP Client is a separate workspace editor**, analogous to WebSocket Session vs HTTP Request
   — not a method on the HTTP request editor.
4. **Default blank-tab protocol remains HTTP** (consistent with FR-1.4 from PYPOST-1156); MCP
   Client requires explicit user choice at tab creation (v1).
5. **Session restore rules** should mirror WebSocket draft conventions from PYPOST-1156: unsaved
   MCP Client drafts excluded from startup restore until first save (proposal — Step 2 confirms).
6. **Metrics attribution** (`track_gui_new_tab_action(source, protocol)`) should gain an
   `mcp_client` protocol label when WS-TM-1 metrics work lands.
7. **Epic placement**: PYPOST-1164 is linked under PYPOST-1155 in Jira; child stories may live
   in PYPOST-1155 or a sibling epic — Step 2 / epic planning decides.

### Doc / Code Gap Analysis

| Source | States | Actual behavior | Severity |
| --- | --- | --- | --- |
| `doc/user/requests.md` L6–7 | Choose method **MCP** to call MCP endpoints from PyPost | Works only as single-shot list/call; no tool browser; headers ignored at runtime | **High** — implies full client UX; documents wrong abstraction |
| `doc/user/requests.md` L71–75 | **MCP Tool** checkbox + **MCP** tab for inbound exposure | Accurate for inbound; coexists confusingly when method is **MCP** (outbound) | **Medium** — naming collision |
| `doc/user/mcp-tools.md` | Inbound exposure workflow only | No outbound client tab documented | **High** — gap for users testing remote servers |
| `doc/user/interface.md` L53–54 | Workspace tabs hold "request or WebSocket session" | No MCP Client editor type | **High** — will be stale after implementation |
| `doc/user/interface.md` L37–41 | **MCP Servers…** for inbound endpoints | Accurate; does not clarify vs outbound client | **Medium** — needs disambiguation |
| `doc/dev/mcp_integration.md` | Inbound MCP server architecture | Outbound client only mentioned via `RequestService` / method MCP | **Medium** |
| `doc/dev/mcp_proxy.md` | Proxy forwarding | No interactive upstream testing UI | **Low** — expected |
| `request_editor.py` | **MCP** in method combo | Overloaded editor; inbound MCP sub-tab on same form | **High** — product debt |
| `RequestService._execute_mcp` | Resolves headers from request | Headers not passed to `MCPClientService` | **Critical** — auth broken for header-gated MCP servers |
| `MCPClientService` | Streamable HTTP client | No SSE client; no prompts/resources | **Medium** — transport and capability gap |
| `McpServersDialog` **Tools…** | Tool list | Local inbound catalog only; error for proxy rows | **Low** — correct for inbound; users may expect remote list |
| `examples/collections/mcp.json` | MCP method requests for probing | Valid today; needs migration story to MCP Client profiles | **Medium** |
| PYPOST-1156 requirements | Protocol picker: HTTP \| WebSocket | MCP Client not included | **Expected** — PYPOST-1164 scope |

### Competitive / Pattern Research Notes

Industry tools treat **MCP client** as a first-class request type distinct from HTTP and from
inbound server configuration:

| Product / tool | Pattern | Relevance to PyPost |
| --- | --- | --- |
| **Postman MCP request** | New request type alongside HTTP/WebSocket/GraphQL; **Load Capabilities** enumerates tools, resources, prompts; invoke from tabs; remote URL over HTTP | Closest analog for PyPost MCP Client tab; supports team collections |
| **MCP Inspector** (official) | `npx @modelcontextprotocol/inspector`; browser UI; tools/resources/prompts with invoke forms; raw JSON-RPC pane | Gold standard for capability depth; PyPost should match core tool invoke loop |
| **MCP Workbench** | CLI + browser inspector; protocol log; contract testing | Protocol log pattern useful for power-user debugging (stretch) |
| **ProtoMCP** | Browser Postman-style; multi-server; schema-generated forms; live trace | Reinforces schema-driven forms + trace as expected UX |
| **MCP-TUI** | Terminal UI; saved connections; stdio/SSE/HTTP transports | stdio gap noted for desktop; SSE transport parity matters |

**Common patterns to adopt (functional level):**

1. **Dedicated editor** — not an HTTP method variant.
2. **Connect → discover → invoke** — persistent connection optional; at minimum explicit Connect.
3. **Schema-driven argument forms** from `list_tools` input schemas.
4. **Separate panes** for tool list, invocation form, and response / protocol trace.
5. **Environment-resolved auth headers** on outbound connections.
6. **Clear labeling** — "MCP Client" vs "MCP Server" / "Expose as MCP Tool".

### UX Options — Protocol Picker Extension (business level)

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| **A — Extend WS-TM-1 popup menu** | Add **MCP Client** as third item in `NewTabProtocolPicker` menu after WebSocket | Single entry point; matches PYPOST-1157 design; one metrics path | Must coordinate with PYPOST-1157; three-item menu slightly denser |
| **B — Dedicated menu item** | File → New → MCP Client Tab | Discoverable in menu bar | Splits tab creation; `Ctrl+N` still needs picker for parity |
| **C — Collections only** | No blank tab; open MCP profiles from sidebar only | Smaller scope | Fails ad-hoc testing goal; inconsistent with HTTP/WS blank-tab epic |
| **D — Keep HTTP method MCP** | No new tab; improve method MCP in place | No migration | Rejected by user input; does not resolve naming collision or UX depth |

**Recommendation (requirements level):** Option **A** — extend the blank-tab protocol picker
delivered by PYPOST-1157. Options B/C/D are inferior or explicitly rejected.

### Main Entities (Business Perspective)

| Entity | Role in this feature |
| --- | --- |
| **Workspace tab** | Container holding HTTP request, WebSocket session, or MCP Client session editor |
| **Protocol / mode** | User's choice among HTTP Request, WebSocket, and MCP Client at blank-tab creation |
| **MCP Client session** | Outbound connection context: server URL, headers, connection state, discovered tools |
| **MCP Client draft** | Unsaved MCP Client session in a workspace tab |
| **Saved MCP Client profile** | Persisted connection defaults in a collection (URL, headers, last-selected tool — exact fields in Step 2) |
| **Remote MCP tool** | Tool definition from server's `list_tools` (name, description, input schema) |
| **Tool invocation** | User-provided arguments → `call_tool` → structured result |
| **Inbound MCP endpoint** | PyPost-hosted server row in **MCP Servers…** (unchanged) |
| **MCP-exposed request/profile** | Collection item marked for inbound agent use (unchanged) |

### Functional Requirements

#### FR-1: MCP Client as a workspace protocol

- FR-1.1 Users opening a new blank workspace tab must be able to choose **MCP Client** alongside
  HTTP Request and WebSocket (after PYPOST-1157 protocol picker ships).
- FR-1.2 MCP Client must be visually distinct from HTTP Request and WebSocket editors (dedicated
  chrome; no HTTP method dropdown with **MCP**).
- FR-1.3 Default blank-tab protocol remains **HTTP**; MCP Client requires explicit choice at
  creation (v1).
- FR-1.4 Protocol switching on a blank, unsaved tab after creation is out of scope for v1 (same
  rule as PYPOST-1156 FR-1.3).

#### FR-2: MCP Client session editor

- FR-2.1 MCP Client tab presents: server URL field, connection control (Connect / Disconnect),
  connection state indicator, tool browser, invocation area, and response/result pane.
- FR-2.2 On Connect, the client performs MCP initialize and `list_tools`; discovered tools appear
  in the tool browser with name and description.
- FR-2.3 Selecting a tool shows its input schema; users can invoke via generated form fields with
  raw JSON fallback for edge schemas.
- FR-2.4 Invoke runs `call_tool` and displays structured results (content blocks, errors, timing).
- FR-2.5 Outbound connection headers support `{{ variable }}` templating from the active
  environment (parity with HTTP request headers).
- FR-2.6 v1 transport minimum: **Streamable HTTP** remote URLs. SSE upstream support is a
  follow-up story (service gap today).

#### FR-3: Migrate HTTP method MCP

- FR-3.1 HTTP request method dropdown **must not** include **MCP** after migration ships.
- FR-3.2 Opening a saved collection item with `method: "MCP"` opens an MCP Client tab with
  equivalent URL and call semantics.
- FR-3.3 Import/export and fixtures using `method: "MCP"` remain valid (convert-on-open or
  document migration script — Step 2 decides).
- FR-3.4 `list_tools` / `call_tool` behavior today (empty → list; JSON body → call) must remain
  reachable without Body-tab JSON encoding.

#### FR-4: Tab entry-point parity

- FR-4.1 `Ctrl+N`, tab-bar **+**, and close-last-tab fallback must offer MCP Client when
  PYPOST-1159-style entry-point parity extends to the third protocol.
- FR-4.2 Opening a saved MCP Client profile from Collections uses deduplicating focus by profile
  id (mirror WebSocket/HTTP patterns).
- FR-4.3 Unsaved MCP Client drafts are excluded from session restore until first save (proposal,
  consistent with WebSocket draft rule in PYPOST-1156).

#### FR-5: Inbound surface clarity (no regression)

- FR-5.1 **MCP Servers…**, **MCP Tool** checkbox, and HTTP/WebSocket **MCP** sub-tabs continue
  to serve inbound exposure unchanged.
- FR-5.2 User-facing copy distinguishes **MCP Client** (outbound testing) from **MCP Servers**
  (inbound hosting) and **Expose as MCP Tool** (inbound authoring).

#### FR-6: Collections parity (saved profiles)

- FR-6.1 Users can save an MCP Client draft to a collection (Save / Save As).
- FR-6.2 Saved MCP Client profiles appear in the Collections tree and open in MCP Client tabs.
- FR-6.3 Collections context menu supports New tab / Rename / Delete for MCP Client items
  (mirror PYPOST-1160 WebSocket parity pattern).

#### FR-7: Documentation truthfulness

- FR-7.1 `doc/user/requests.md` no longer documents method **MCP** as the primary outbound path.
- FR-7.2 New or updated user doc describes MCP Client tab workflow (connect, list, invoke).
- FR-7.3 `doc/user/interface.md` lists MCP Client as a workspace editor type.
- FR-7.4 `doc/user/mcp-tools.md` (or sibling page) clarifies inbound vs outbound MCP surfaces.

### Non-Functional Requirements

- **NFR-1 Consistency:** MCP Client blank-tab UX must feel analogous to HTTP and WebSocket
  (create → configure → act → inspect → optional save).
- **NFR-2 Discoverability:** Users testing remote MCP servers must not need knowledge of JSON
  body conventions or the method dropdown.
- **NFR-3 Security:** Outbound headers and responses respect hidden-key masking in UI and logs
  (consistent with MCP proxy sanitization policy).
- **NFR-4 Timeouts:** Connection and operation timeouts must be user-understandable (today: 25s
  total in `MCPClientService` — may need settings exposure).
- **NFR-5 Metrics:** Connect, list_tools, and call_tool actions attributable in product telemetry
  separately from inbound `mcp_requests_received_total`.
- **NFR-6 Naming:** Avoid overloading "MCP" without qualifier in UI labels (prefer "MCP Client",
  "MCP Servers", "Expose as MCP Tool").

### Constraints and Assumptions

- MCP Client tab mode is **outbound only**; inbound server/proxy architecture is stable.
- **WS-TM-1 (PYPOST-1157)** protocol picker is a hard dependency for blank-tab MCP Client.
- HTTP method **MCP** migration is **in scope** for the implementation epic (user mandate).
- stdio transport, prompts, resources, and protocol trace viewer are **v1 out of scope** unless
  a child story explicitly expands scope.
- `MCPClientService` is the starting backend but likely insufficient alone (headers, SSE, session
  lifecycle) — Step 2 addresses extension vs replacement.
- Epic PYPOST-1155 title says "WebSocket"; MCP Client stories may warrant epic rename or sibling
  epic — planning decision, not blocking research.

### Proposed Child Story Breakdown (follow-up implementation epic)

Stories use provisional IDs **MCP-TM-1 … MCP-TM-8** until Jira issues are created. Suggested
epic: extend PYPOST-1155 or new "Tab protocol modes" epic — Step 2 decides.

| Story | Summary | Depends on | Acceptance criteria (summary) |
| --- | --- | --- | --- |
| **MCP-TM-1** | Extend protocol picker with **MCP Client** | WS-TM-1 (PYPOST-1157) | Third menu item; `mcp_client` protocol in new-tab metrics; HTTP default unchanged |
| **MCP-TM-2** | Blank MCP Client draft tab shell | MCP-TM-1 | URL bar, Connect/Disconnect, state badge, empty tool browser; draft excluded from session restore |
| **MCP-TM-3** | Tool discovery (`list_tools`) and browser UI | MCP-TM-2 | Tool list with name/description; refresh; error states for connect failures |
| **MCP-TM-4** | Interactive `call_tool` + response pane | MCP-TM-3 | Schema-guided form + JSON fallback; structured result display; timing |
| **MCP-TM-5** | Outbound headers + environment templating | MCP-TM-2 | Headers table; `{{ var }}` resolution; fixes `_execute_mcp` header gap |
| **MCP-TM-6** | Migrate/remove HTTP method **MCP** | MCP-TM-4 | Method removed from combo; collection `method: "MCP"` opens MCP Client tab; fixtures updated |
| **MCP-TM-7** | Collections save/open + context menu parity | MCP-TM-2 | Save/Save As; tree item type; New tab / Rename / Delete |
| **MCP-TM-8** | User documentation alignment | MCP-TM-1 … MCP-TM-7 | `requests.md`, `interface.md`, `mcp-tools.md` updated; inbound/outbound disambiguated |

**Stretch (post-v1, not in initial epic estimate):**

| Story | Summary |
| --- | --- |
| MCP-TM-9 | SSE upstream transport for MCP Client |
| MCP-TM-10 | Prompts and resources panes (`list_prompts`, `list_resources`, …) |
| MCP-TM-11 | Protocol trace / JSON-RPC log pane (Inspector-style) |
| MCP-TM-12 | stdio MCP server connection from desktop GUI |

**Suggested implementation order:** MCP-TM-1 → MCP-TM-2 → MCP-TM-5 → MCP-TM-3 → MCP-TM-4 →
MCP-TM-6 → MCP-TM-7 → MCP-TM-8 (MCP-TM-5 can parallel MCP-TM-3 once MCP-TM-2 exists).

## Q&A

| Question | Answer |
| --- | --- |
| Is MCP Client tab the same as **MCP Servers…**? | **No.** MCP Servers hosts inbound endpoints for agents. MCP Client tab calls remote servers outbound. |
| Should HTTP method **MCP** remain alongside the new tab? | **No** — user input mandates migration into MCP Client tab mode. |
| Does MCP Client replace the inbound **MCP** sub-tab on requests? | **No** — inbound "Expose as MCP Tool" stays on HTTP/WebSocket editors. Consider clearer labels in a separate copy story. |
| Relationship to MCP Proxy? | Proxy forwards inbound agent traffic upstream. MCP Client tab tests upstream directly without starting a proxy row. |
| Does WS-TM-1 need to ship first? | **Yes** — extend its picker; do not build a second tab-creation path. |
| Are prompts/resources required for v1? | **No** — `list_tools` + `call_tool` match current `MCPClientService` and minimum viable parity with method MCP. |
| What happens to `examples/collections/mcp.json`? | Migrate-on-open or collection format update in MCP-TM-6; must keep contributor probe workflow. |
| stdio transport? | **Out of scope v1** — PyPost desktop has no stdio client; Postman supports it as a follow-up. |
| Session restore for unsaved MCP Client tabs? | **Excluded until save** (proposed, aligned with WebSocket draft rule). |

## References

- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — this research story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic (blank-tab protocol selector)
- [PYPOST-1156](https://pypost.atlassian.net/browse/PYPOST-1156) — WebSocket tab mode research (template)
- [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) … [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163) — TabProtocol / WS-TM stories
- `doc/dev/mcp_integration.md`, `doc/dev/mcp_proxy.md`
- `doc/user/requests.md`, `doc/user/mcp-tools.md`, `doc/user/interface.md`
- `pypost/ui/widgets/request_editor.py`, `pypost/core/mcp_client_service.py`
- `pypost/ui/dialogs/mcp_servers_dialog.py`, `pypost/ui/presenters/mcp_controls_presenter.py`
- `examples/collections/mcp.json`
- [Postman MCP requests](https://learning.postman.com/docs/postman-ai/mcp-requests/overview) — competitive reference
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) — competitive reference
