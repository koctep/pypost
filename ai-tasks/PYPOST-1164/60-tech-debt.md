# PYPOST-1164: Technical Debt Analysis

## Scope Note

PYPOST-1164 is a research and decomposition story with no production code — Steps 3, 4, and 5
each confirmed that fact. This step records **pre-existing product/code debt discovered during the
MCP UX audit** and routes it to the child implementation stories (MCP-TM-1 … MCP-TM-8) proposed
in Step 2. The child stories were created in Jira during Phase D, before
commit: MCP-TM-1 … MCP-TM-8 are
[PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) …
[PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172), and the
Follow-up Tasks table below carries their browse links.

## Shortcuts Taken

1. **v1 protocol choice is creation-time only.** FR-1.4 and the architecture decision register
   defer post-creation protocol switching on blank tabs to a future release. Users who pick the
   wrong protocol must close the tab and open a new one — same v1 rule as PYPOST-1156 WebSocket
   research.
2. **HTTP method MCP retained in codebase until MCP-TM-6.** Research documents migration intent
   (convert-on-open) but does not remove the overloaded method dropdown entry — that ships with
   the dedicated MCP Client editor.
3. **No Step-3 red tests in PYPOST-1164.** Red tests are delegated to each child story's own
   Step 3 per the table in `20-architecture.md` — same precedent as PYPOST-1156.
4. **Stretch capabilities explicitly deferred.** SSE upstream transport (MCP-TM-9), prompts/resources
   panes (MCP-TM-10), protocol trace viewer (MCP-TM-11), and stdio client (MCP-TM-12) are noted
   in requirements but excluded from the v1 epic estimate.
5. **Epic placement decided as option (a).** MCP-TM-1 … MCP-TM-8 were created under Epic
   [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155). The rename-vs-sibling
   call was deferred twice (`20-architecture.md` L160, L511). Closed in
   [PYPOST-1174](https://pypost.atlassian.net/browse/PYPOST-1174): keep this parent;
   title **Tab protocol modes — blank-tab protocol selector**; labels not websocket-only.
6. **MCP Client hotkeys deferred without an owner.** `20-architecture.md` L155 and L510 push
   them to "post-v1 unless bundled — document in MCP-TM-8", but MCP-TM-8 is a documentation
   story and the stretch list (MCP-TM-9 … MCP-TM-12) omits them. Now tracked in
   [PYPOST-1175](https://pypost.atlassian.net/browse/PYPOST-1175).

## Code Quality Issues

Pre-existing issues in the codebase (not introduced by PYPOST-1164):

| Issue | Location | Impact |
| --- | --- | --- |
| **`_execute_mcp` ignores resolved headers** | `RequestService._execute_mcp` (`request_service.py` L102–134) | **Critical** — URL, headers, and body are templated but only URL is passed to `MCPClientService.run`; Bearer/API-key auth broken for header-gated MCP endpoints |
| **HTTP method MCP overloads request editor** | `RequestEditor` method combo (`request_editor.py` L97) | **High** — outbound list/call via Body JSON convention; no tool browser; coexists with inbound **MCP** sub-tab on same form |
| **`MCPClientService` lacks headers param** | `mcp_client_service.py` | **High** — Streamable HTTP only; new session per `run()`; no SSE upstream client path (contrast: `MCPProxyServerImpl`) |
| **Inbound/outbound naming collision** | Request editor **MCP** sub-tab + method **MCP** | **Medium** — users can enable **MCP Tool** (inbound) while method is **MCP** (outbound) |
| **HTTP-only blank-tab factory** | `TabsPresenter.add_new_tab()` → `_create_request_tab()` | No protocol-aware entry API; MCP Client requires WS-TM-1 picker first |
| **`_current_tab()` returns `RequestTab \| None` only** | `tabs_presenter.py` | Global shortcuts silently no-op on WebSocket tabs; MCP Client tab kind must be added when editor ships |
| **Collections context menu incomplete for non-request items** | `collection_tree_actions._resolve_item_target()` | Resolves `RequestData` and collection `str` only — blocks MCP Client New tab / rename / delete (pattern debt from WebSocket audit) |
| **`McpToolsOverviewDialog` lists inbound tools only** | `mcp_servers_dialog.py` | Users may expect remote server tool list; outbound browser must be new UI |
| **Doc/code gaps on outbound MCP** | `doc/user/requests.md`, `doc/user/mcp-tools.md`, `doc/user/interface.md` | **High** — method MCP documented as primary outbound path; no MCP Client editor type; inbound-only `mcp-tools.md` |

## Missing Tests

Not applicable directly (no code produced by PYPOST-1164). The Step 3 delegation pattern assigns
red tests to child stories — see `20-architecture.md` "Proposed red tests per child story" table.
Notable gaps in the **current** codebase (to be closed by child stories):

| Gap | Owner |
| --- | --- |
| No test proving `_execute_mcp` forwards headers to MCP HTTP client | [PYPOST-1173](https://pypost.atlassian.net/browse/PYPOST-1173), then MCP-TM-5 |
| No `McpClientTab` / presenter integration tests | MCP-TM-2 … MCP-TM-4 |
| No migration test for `method: "MCP"` collection open | MCP-TM-6 |
| No collections context-menu tests for `McpClientConnection` | MCP-TM-7 |

## Performance Concerns

None identified for the research deliverables. Tab-scoped MCP `ClientSession` holders (MCP-TM-3)
should call `teardown()` on tab close to avoid leaked async resources — same pattern as
`WebSocketPresenter`. The existing 25s total timeout in `MCPClientService` may need settings
exposure (NFR-4) — defer to MCP-TM-3/4 implementation.

## Follow-up Tasks

Pre-existing debt discovered during research, mapped to child stories under Epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)
(**Tab protocol modes — blank-tab protocol selector**, option (a) / PYPOST-1174):

| Debt area | Description | Owner |
| --- | --- | --- |
| Protocol picker — third item | Blank tab has no **MCP Client** choice; depends on WS-TM-1 | [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) (MCP-TM-1) |
| Metrics `protocol=mcp_client` | `track_gui_new_tab_action` lacks third protocol label | [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) (MCP-TM-1) |
| Blank MCP Client draft tab | No `add_blank_mcp_client_tab()`; no dedicated editor chrome | [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) (MCP-TM-2) |
| Tool discovery UI | No `list_tools` browser for remote servers | [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169) (MCP-TM-3) |
| Outbound operation metrics | No `mcp_client_connect_total` / `list_tools` / `call_tool` counters | [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169), [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170) (MCP-TM-3, MCP-TM-4) |
| Schema-guided `call_tool` | No invoke form or structured result pane for outbound client | [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170) (MCP-TM-4) |
| Header forwarding / auth gap | `_execute_mcp` and `MCPClientService` drop outbound headers | [PYPOST-1173](https://pypost.atlassian.net/browse/PYPOST-1173) (immediate fix on the current method-MCP path), [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) (MCP-TM-5, new editor) |
| HTTP method MCP removal | Method combo entry and `_execute_mcp` dispatch still present | [PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171) (MCP-TM-6) |
| Legacy collection migration | `method: "MCP"` items (e.g. `examples/collections/mcp.json`) open as HTTP tabs | [PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171) (MCP-TM-6) |
| Collections save/open parity | No `mcp_clients[]` collection field or tree item type | [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172) (MCP-TM-7) |
| Context menu parity | `_resolve_item_target` cannot resolve `McpClientConnection` | [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172) (MCP-TM-7) |
| User documentation | Outbound client workflow undocumented; method MCP over-documented | [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168) (MCP-TM-8) |
| Inbound/outbound copy clarity | **MCP Servers** vs **MCP Client** vs **Expose as MCP Tool** labels | [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168) (MCP-TM-8) |

### Follow-ups raised by independent review (2026-08-25)

Filed outside Epic [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) because they are
not blocked by the MCP Client tab work:

| Item | Description | Ticket |
| --- | --- | --- |
| Outbound header drop | Live defect on the shipped method-MCP path: resolved headers never reach `MCPClientService.run`, and History records headers that were not sent. Previously reachable only via MCP-TM-5, which sits behind three unstarted stories. | [PYPOST-1173](https://pypost.atlassian.net/browse/PYPOST-1173) (Debt, High, 3 SP) |
| Epic placement | Option (a): keep MCP stories on PYPOST-1155; rename that epic (not a sibling). | [PYPOST-1174](https://pypost.atlassian.net/browse/PYPOST-1174) |
| MCP Client hotkeys | Deferred "post-v1" with no owning story and no stretch row; `_current_tab()` will no-op shortcuts on MCP tabs exactly as it does on WebSocket tabs. | [PYPOST-1175](https://pypost.atlassian.net/browse/PYPOST-1175) (Story, Medium, 3 SP) |

PYPOST-1174 epic title: **Tab protocol modes — blank-tab protocol selector**.

### New debt surfaced by this research (documentation)

1. **`doc/user/requests.md` L6–7** documents method **MCP** as the outbound path — will be
   stale and misleading after MCP Client tab ships; correction owned by MCP-TM-8 (with method
   removal in MCP-TM-6).
2. **`doc/user/interface.md` L53–54** lists only HTTP request and WebSocket session workspace
   editors — must add MCP Client after implementation.
3. **`doc/dev/mcp_integration.md`** describes inbound server architecture only; outbound client
   limited to module docstring — dev doc expansion deferred to implementation epic (MCP-TM-8 or
   follow-up dev-doc story).

**Pre-existing test failures:** none apply — no test suite was run during this research task.

None of the follow-ups above block Step 8 (Dev Docs) or COMMIT for PYPOST-1164 itself. They are
the intended output of the decomposition: pre-existing debt routed to named implementation
stories rather than fixed in the research task.
