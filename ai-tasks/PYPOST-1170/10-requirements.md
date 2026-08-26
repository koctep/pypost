# PYPOST-1170: Interactive call_tool and response pane

## Goals

[PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169) (MCP-TM-3)
already makes Connect a real outbound action: the MCP Client tab reaches
the remote server, lists tools, and shows each tool's **name** and
**description**. Headers and environment templating already travel with
that session ([PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)).

Discovery still stops at the catalog. The user cannot pick a tool, supply
arguments from the advertised input schema, invoke it, or inspect what
came back. They still fall back to encoding `call_tool` in an HTTP body
(or a competing inspector) to exercise a remote tool.

This story (MCP-TM-4) is the **invoke-and-inspect** step on that same
tab:

1. After tools are listed, the user **selects** a tool from the existing
   browser.
2. They fill arguments from the tool's advertised **input schema**, or
   use a **JSON fallback** when the schema is missing or too complex for
   a field form.
3. They **invoke** the selected tool (`call_tool`) on the connected
   session.
4. They see a **structured result** and **how long** the invoke took.

The business goal is a trustworthy connect → discover → invoke loop:
after Connect, the user can actually call a listed tool and judge the
outcome without leaving the MCP Client tab. Collections save, retiring
HTTP method **MCP**, and user-doc rewrite remain later stories.

## User Stories

- As a **developer testing a remote MCP server**, I want to select a
  listed tool and invoke it from the MCP Client tab, so I can exercise
  the endpoint without encoding `name` / `arguments` in an HTTP body.
- As a **user filling tool arguments**, I want a form driven by the
  tool's advertised input schema, so I do not have to guess field names
  and types.
- As a **user whose tool takes nested or unusual arguments**, I want a
  JSON fallback editor, so I can still send a valid payload when a
  simple field form is not enough.
- As a **user invoking a tool with no arguments**, I want to invoke
  without filling a dummy form, so empty-schema tools remain usable.
- As a **user looking at the outcome**, I want a structured result pane
  with elapsed time, so I can tell success, tool/server errors, and
  slowness apart.
- As a **user whose invoke fails**, I want a clear error in the tab
  while staying connected, so a bad call does not look like a failed
  Connect (disconnected, empty tools).
- As a **user already connected with headers**, I want Invoke to use the
  same session, URL, and resolved headers as Connect, so a header-gated
  server accepts the call the same way it accepted the list.
- As a **user who switches tools**, I want the argument area to match
  the newly selected tool, so leftover fields from the previous tool
  are not sent by mistake.
- As an **HTTP-first user**, I want HTTP and WebSocket tabs unchanged,
  so this story only adds invoke on the MCP Client tab.

## Definition of Done

PYPOST-1170 is done when:

1. On a **connected** MCP Client tab with a discovered tool list, the
   user can **select** a tool from the existing tool browser.
2. Selecting a tool shows a **schema-guided argument form** built from
   that tool's advertised input schema (required vs optional is visible).
3. A **JSON fallback editor** is available for arguments the form cannot
   represent (missing schema, nested/complex structure, or paste-in
   payload).
4. The user can **Invoke**; that action calls the selected tool
   (`call_tool`) on the connected outbound session.
5. After invoke, a **result pane** shows a **structured** outcome
   (success content and errors are distinguishable) and **elapsed time**.
6. Invoke failures are shown in the tab; the session **stays connected**
   and the tool list is **kept**. Chrome must not match a failed Connect
   (not connected, empty tools).
7. Disconnect (and closing the tab) still ends the session as in
   PYPOST-1169; the invoke area and result pane do not keep a live
   session after disconnect.
8. Resolved URL and headers already on the tab are used for invoke
   (same as Connect). Blank HTTP / WebSocket tabs, inbound MCP surfaces,
   picker, draft restore exclusion, headers-table chrome, Connect /
   Refresh / list behavior stay unchanged.
9. Migrating or removing HTTP method **MCP**, Collections save of last
   tool/args, and user-doc rewrite remain out of scope.

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

Users can connect and see which tools a remote MCP server advertises.
They cannot call those tools from the MCP Client tab. Competitive tools
(Postman MCP request, MCP Inspector) treat **Load Capabilities** as the
start of an invoke loop: pick a tool, fill schema-driven inputs, run,
inspect the structured result and timing.

Without this story:

- Discovery is a dead end: the catalog cannot be exercised.
- Users fall back to HTTP method **MCP** with a JSON body to
  `call_tool`.
- MCP-TM-6 cannot retire that method until the dedicated tab can invoke.

### Business Need

The MCP Client tab must complete the outbound loop: select a discovered
tool, supply arguments from the advertised schema (or JSON fallback),
invoke, and inspect a structured result with timing. Failures must be
visible without tearing down Connect.

### Boundary with PYPOST-1166, PYPOST-1167, PYPOST-1169, and later

| Concern | 1166 | 1167 | 1169 | This story | Later |
| --- | --- | --- | --- | --- | --- |
| Draft shell (URL, Connect, empty tools) | In | Present | Present | Present | Unchanged |
| Headers + `{{ variable }}` on outbound | Out | In | Used | **Used** on Invoke | Unchanged |
| Live `list_tools` + name / description | Out | Out | In | Present | Unchanged |
| Select tool from the browser | Out | Out | Out | **In scope** | Unchanged |
| Schema-guided argument form | Out | Out | Out | **In scope** | Unchanged |
| JSON fallback for complex args | Out | Out | Out | **In scope** | Unchanged |
| Invoke (`call_tool`) | Out | Out | Out | **In scope** | Unchanged |
| Structured result pane + timing | Out | Out | Out | **In scope** | Unchanged |
| Invoke error messaging | Out | Out | Out | **In scope** | Unchanged |
| Remove HTTP method **MCP** | Out | Out | Out | Out | MCP-TM-6 |
| Collections save of last tool / args | Out | Out | Out | Out | MCP-TM-7 |
| User documentation rewrite | Out | Out | Out | Out | MCP-TM-8 |

**Shell rule:** this story **uses the existing MCP Client workspace and
tool browser**. It must not invent a second tab kind. Connect / Refresh
from 1169 stay; this story adds select → fill → invoke → inspect.

### Scope (this task)

- Select a discovered tool from the existing tool browser while
  connected.
- Show that tool's advertised input schema as a guided argument form
  (field names, types the schema describes at field level, required vs
  optional).
- Provide a JSON fallback editor for missing, empty-of-fields, nested,
  or otherwise form-unfriendly schemas, and for pasting a full argument
  object.
- Tools with no argument schema (or an empty object schema) are
  invokable without dummy fields.
- Invoke sends `call_tool` for the selected tool with the filled
  arguments on the **already connected** session.
- Invoke uses the tab's resolved URL and resolved headers (same policy
  as Connect).
- A structured result pane shows success content vs errors, plus
  elapsed time for that invoke.
- Invoke in progress is visible; the window is not frozen with no
  status.
- Failed invoke is visible and **does not** disconnect or clear tools.
- Changing the selected tool replaces the argument area so the previous
  tool's values are not submitted.
- Disconnect (and tab close) still ends the outbound session; invoke is
  not available while disconnected.
- Keep picker, draft restore exclusion, headers table, Connect /
  Refresh, and name/description browser as shipped.

### Out of Scope

- Live Connect / `list_tools` / refresh / connect-error chrome —
  already shipped in MCP-TM-3
  ([PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)).
- Headers table and `{{ variable }}` resolution — already shipped in
  MCP-TM-5
  ([PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)).
- Migrating or removing HTTP method **MCP** — MCP-TM-6
  ([PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171)).
- Save / Save As, Collections tree items, restore of **saved** profiles,
  persisting last-selected tool and arguments — MCP-TM-7
  ([PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)).
- User documentation rewrite — MCP-TM-8
  ([PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)).
- Pre-filling arguments from a legacy HTTP method **MCP** body
  (convert-on-open) — that mapping ships with MCP-TM-6.
- Changing the protocol picker, default HTTP choice, or new-tab
  counting.
- Switching protocol on a tab after it is created.
- Inbound MCP surfaces (**MCP Servers…**, **MCP Tool** checkbox, HTTP /
  WebSocket **MCP** sub-tabs).
- Prompts, resources, protocol trace / raw JSON-RPC log, SSE, or stdio
  transports.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **MCP Client workspace** | Dedicated outbound MCP Client editor. |
| **Outbound session** | Live client session after successful Connect. |
| **Remote MCP tool** | Advertised tool: name, description, input schema. |
| **Tool browser** | List of discovered remote tools (select source). |
| **Selected tool** | The tool the user is about to invoke. |
| **Input schema** | Advertised argument contract for the selected tool. |
| **Argument form** | Schema-guided fields the user fills before invoke. |
| **JSON fallback** | Raw argument editor when the form is not enough. |
| **Invoke** | User action that calls the selected tool. |
| **Tool result** | Structured outcome of invoke (content or error). |
| **Result pane** | Place the user inspects the outcome and timing. |
| **Elapsed time** | How long that invoke took, shown to the user. |
| **Invoke error** | User-visible reason invoke failed; session stays up. |
| **Resolved URL / headers** | Address and auth after environment templating. |

### Functional Requirements

#### FR-1: Select a discovered tool

- FR-1.1 While connected with a non-empty tool list, the user can
  select a tool from the existing tool browser.
- FR-1.2 Selection is not available (or has no effect toward invoke)
  while the tab is disconnected; there is no leftover selected tool
  from a previous session after Disconnect.
- FR-1.3 If Refresh removes the selected tool from the list, selection
  and the argument area clear; the session stays connected.
- FR-1.4 If Refresh keeps the selected tool, selection remains; the
  argument area stays bound to that tool (the user is not silently
  switched to another tool).

#### FR-2: Schema-guided arguments and JSON fallback

- FR-2.1 Selecting a tool shows an argument area driven by that tool's
  advertised **input schema**.
- FR-2.2 The form exposes field-level names and which fields are
  **required** vs optional, when the schema describes them that way.
- FR-2.3 A **JSON fallback** editor is available when the schema is
  absent, has no field-level shape, or is nested/complex beyond a
  simple field form, and when the user pastes a full argument object.
- FR-2.4 A tool with no arguments (missing or empty argument schema) is
  invokable without requiring dummy fields or dummy JSON.
- FR-2.5 Switching the selected tool replaces the argument area so
  values from the previous tool are not submitted with the new name.
- FR-2.6 Invoke from the form is blocked with a visible error when
  **required** form fields are empty. Invoke from JSON is blocked with
  a visible error when the text is not a valid JSON object. Neither
  case sends a call.

#### FR-3: Invoke on the connected session

- FR-3.1 Invoke runs `call_tool` for the **selected** tool with the
  arguments from the form or JSON fallback.
- FR-3.2 Invoke uses the same outbound session, resolved URL, and
  resolved headers as Connect (PYPOST-1167 / PYPOST-1169).
- FR-3.3 Invoke while disconnected does not succeed; the user sees an
  error and the tab does not look connected.
- FR-3.4 Invoke with no selected tool does not succeed; the user sees
  an error.
- FR-3.5 While invoke is in progress, the user can tell work is
  underway. A second Invoke does not start until the in-flight one
  finishes (or is no longer the active call).
- FR-3.6 Hidden environment values stay masked in any error, status, or
  result text (same product rule as HTTP and header preview).

#### FR-4: Structured result pane and timing

- FR-4.1 After a completed invoke, the result pane shows a
  **structured** outcome: success content is readable as the tool's
  returned payload (not only an undifferentiated blob), and tool or
  protocol errors are clearly errors.
- FR-4.2 The result pane shows **elapsed time** for that invoke.
- FR-4.3 A new successful or failed invoke **replaces** the previous
  result (including timing) so the pane always reflects the latest
  completed call.
- FR-4.4 Starting a new invoke makes it obvious the previous result is
  no longer the current outcome (in-progress, not a stale success).
- FR-4.5 Disconnect clears the result pane together with tools and
  selection; a closed session must not look like it still has a live
  last result.

#### FR-5: Invoke failures vs Connect / Refresh failures

- FR-5.1 Invoke failures are shown to the user in the tab (network,
  timeout, protocol, tool error, validation — as the product already
  distinguishes them for the user).
- FR-5.2 A failed invoke is **not** a failed Connect (PYPOST-1169
  FR-3.2). Explicit outcome:
  - **Session:** stays connected. Invoke does not end the outbound
    session or leave the tab disconnected.
  - **Tool list:** kept. It is **not cleared**.
  - **Chrome:** stays **connected with an error** in the result / invoke
    area. It must not match a failed Connect (not connected, empty tool
    browser).
- FR-5.3 A failed invoke is also **not** a failed Refresh: tools stay
  as last confirmed by Connect/Refresh; the error is about the call,
  not about re-listing.

#### FR-6: Existing surfaces stay the same

- FR-6.1 HTTP and WebSocket tabs stay unchanged.
- FR-6.2 Picker, MCP Client draft chrome layout, unsaved-draft restore
  exclusion, headers table, Connect, Disconnect, Refresh, and
  name/description tool browser stay as shipped.
- FR-6.3 Inbound MCP surfaces stay unchanged.
- FR-6.4 HTTP method **MCP** is not removed in this story.

### Non-Functional Requirements

- **NFR-1 Trust:** Connected still means Connect succeeded. A failed
  **invoke** does not revoke connected or empty the tool list. The
  result pane must not present a failed call as a successful payload.
- **NFR-2 Discoverability:** After Connect, invoking a listed tool does
  not require knowing the HTTP method **MCP** JSON body convention.
- **NFR-3 Consistency:** Select → fill schema (or JSON) → invoke →
  inspect matches Postman / Inspector tool-run depth for v1 (tools
  only; no prompts, resources, or protocol trace).
- **NFR-4 Security:** Hidden environment keys stay masked in UI and
  logs (same policy as HTTP and MCP proxy sanitization).
- **NFR-5 Responsiveness:** The tab stays usable while invoke runs; the
  user is not left with a frozen window and no status.
- **NFR-6 Naming:** User-visible labels prefer **MCP Client**,
  **Invoke** (or equivalent clear run control), and **result** over
  unqualified **MCP** or raw protocol method names as the only chrome.
- **NFR-7 Telemetry:** Invoke (`call_tool`) should be attributable
  separately from Connect / list-tools and from inbound MCP request
  counts.

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on: [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)
  (MCP-TM-3, Done). Headers used on invoke already shipped in
  [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167).
- Parent product spec: `ai-tasks/PYPOST-1164/10-requirements.md`
  FR-2.3 (schema-guided form + JSON fallback) and FR-2.4 (invoke,
  structured results, timing).
- Architecture pointer for later steps:
  `ai-tasks/PYPOST-1164/20-architecture.md` (research decomposition).
  This story still runs its own Step 2.
- v1 transport remains Streamable HTTP remote URLs.
- v1 invoke is tools only (`call_tool`); prompts and resources are
  later.
- User-facing copy uses **MCP Client**, **Connect**, **Disconnect**,
  and a clear invoke control.

## Q&A

- **Why is this not part of PYPOST-1169?**
  1169 is discovery: Connect must list tools and show name/description.
  Invoke is a separate user goal: exercise a listed tool and inspect
  the result.

- **Does Invoke have to list tools again?**
  No. Invoke uses the connected session and the already discovered
  catalog. Refresh remains the way to re-list.

- **Must every schema become a full form?**
  No. Simple field-level schemas drive the form. Nested, free-form, or
  missing schemas use the JSON fallback. Empty-argument tools invoke
  without dummy input.

- **Is JSON only for errors, or also a power-user path?**
  Both. It is the fallback when the form cannot represent the contract,
  and it is how the user pastes a complete argument object.

- **Does a failed invoke disconnect like a failed Connect?**
  No. Failed Connect means the session never started: not connected,
  empty tools. Failed invoke happens on an already connected session:
  stay connected, keep tools, show the error in the invoke / result
  area.

- **Does Disconnect keep the last result?**
  No. Ending the session clears selection, argument area, and result
  pane so a disconnected tab does not look like it still has a live
  last call.

- **Does this migrate HTTP method MCP?**
  No. That is MCP-TM-6. This story makes the dedicated tab able to
  invoke so that migration can retire the method later.

- **Does this save last-selected tool and arguments?**
  No. Persistence is MCP-TM-7. This story is the live invoke loop on
  the unsaved (or already opened) tab.

- **Does this change inbound MCP Servers Tools…?**
  No. That catalog is tools PyPost exposes. This pane invokes tools on
  the **remote** server the user connected to.

- **How do Jira acceptance-criteria names map to this document?**
  Jira AC aliases (not requirements of their own):
  - Schema-guided argument form from tool inputSchema — FR-2.
  - JSON fallback editor for complex args — FR-2.3.
  - Structured result pane with timing — FR-4.

## References

- [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170) — this
  story (MCP-TM-4)
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent
  epic
- [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169) — MCP-TM-3
  discovery (Done)
- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — MCP-TM-2
  draft shell (Done)
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — MCP-TM-5
  headers / templating (Done)
- [PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171) — MCP-TM-6
  migrate HTTP method **MCP** (out of scope)
- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — MCP
  Client UX research
- `ai-tasks/PYPOST-1164/10-requirements.md` — FR-2.3 / FR-2.4 invoke
- `ai-tasks/PYPOST-1164/20-architecture.md` — MCP-TM-4 acceptance;
  Step 2 pointer
- `ai-tasks/PYPOST-1169/10-requirements.md` — discovery vs invoke
  boundary
