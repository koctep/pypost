# PYPOST-1167: Outbound headers + environment templating

## Goals

[PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) (MCP-TM-2)
already opens a blank MCP Client draft: URL, Connect / Disconnect, connection
state, and an empty tool browser. That shell still has no place to attach
**Authorization** or other connection headers. Developers testing a
header-gated MCP server cannot use their active environment the way they
already do on HTTP requests (`Authorization: Bearer {{ token }}`).

Research in [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164)
called this out as a product gap: outbound MCP work today can *show* headers
on the HTTP method **MCP** editor, but those values never reach the remote
server. Protected MCP endpoints fail as if no credentials were sent.

This story (MCP-TM-5) closes that auth gap for outbound MCP:

1. The MCP Client editor gains a headers table (same job as HTTP **Headers**).
2. Header names and values resolve `{{ variable }}` placeholders from the
   active environment before the client talks to the server.
3. Every outbound MCP call actually **sends** those resolved headers — both
   from the MCP Client tab and from the still-live HTTP method **MCP** path
   until MCP-TM-6 retires it.

The business goal is environment-resolved auth parity with HTTP requests and
with MCP proxy upstream headers: a Bearer token or API key in the environment
must authenticate the outbound MCP session.

This story does not ship tool listing, invoke UI, Collections save, or
removal of HTTP method **MCP**.

## User Stories

- As a **developer authenticating to an MCP server**, I want a headers table
  on the MCP Client editor, so I can set `Authorization` and other connection
  headers without using the HTTP request editor.
- As a **developer who stores secrets in the environment**, I want header
  values (and the server URL) to accept `{{ variable }}` placeholders from
  the active environment, so Bearer tokens and API keys work the same as on
  HTTP requests.
- As a **developer connecting or sending to a protected MCP server**, I want
  those resolved headers to actually go out with the call, so the remote
  server sees the credentials I configured.
- As a **user still sending HTTP method MCP**, I want the Headers I already
  filled on that request to reach the remote MCP server, so existing probes
  stop failing auth until MCP-TM-6 migrates that path.
- As a **user with hidden environment keys**, I want secret values to stay
  masked in the editor preview, so tokens are not shown in plaintext.
- As an **HTTP-first user**, I want HTTP and WebSocket header behavior
  unchanged, so this story only adds outbound MCP header support.

## Definition of Done

PYPOST-1167 is done when:

1. The MCP Client editor includes a headers table where the user can add,
   edit, and remove named connection headers (parity with HTTP **Headers**).
2. Header names and values support `{{ variable }}` placeholders from the
   active environment. The server URL on the MCP Client tab resolves the
   same way when the user connects or sends.
3. When an outbound MCP call runs, the **resolved** headers are sent to the
   remote MCP server (not merely stored on the tab).
4. Sending an HTTP method **MCP** request also sends that request's
   resolved headers to the remote MCP server (closes the current auth gap
   until MCP-TM-6).
5. Hidden environment variables stay masked in header preview (same product
   rule as HTTP templating).
6. Blank HTTP and WebSocket tabs, inbound MCP surfaces, picker identity,
   draft restore exclusion, and close-session rules from PYPOST-1166 stay
   unchanged.

## Task Description

### Programming Language

Python — PyPost desktop client and automated tests.

### Problem

Users can open an MCP Client draft and type a server URL, but they cannot
attach connection headers or reuse environment secrets. Competitive tools
(Postman MCP request, MCP Inspector) treat outbound auth headers as part of
the connection, not as HTTP-only chrome.

Separately, the hidden HTTP method **MCP** path already *looks* like it
supports headers: the HTTP editor has a Headers table and templating. At
send time those resolved headers are dropped, so header-gated MCP servers
reject the call. Users believe they configured auth; the server never sees
it.

Without this story:

- MCP Client tabs cannot authenticate to protected servers.
- Environment variables used for HTTP auth do not apply to outbound MCP.
- HTTP method **MCP** remains a false promise until migration.

### Business Need

Outbound MCP must send environment-resolved connection headers, matching
HTTP request header templating. The MCP Client draft is the primary surface.
Until method **MCP** is removed, that legacy send path must honor headers
too.

### Boundary with PYPOST-1166 and later stories

| Concern | PYPOST-1166 | PYPOST-1167 | Later |
| --- | --- | --- | --- |
| Draft shell (URL, Connect, state, empty tools) | In scope | Already present | Unchanged |
| Headers table on MCP Client editor | Out of scope | **In scope** | Unchanged |
| `{{ variable }}` resolution for headers / URL | Out of scope | **In scope** | Unchanged |
| Resolved headers sent on outbound MCP calls | Out of scope | **In scope** | MCP-TM-3/4 use it |
| HTTP method **MCP** header gap | Out of scope | **In scope** (fix) | MCP-TM-6 retires path |
| Live tool listing / refresh / errors | Out of scope | Out of scope | MCP-TM-3 |
| Invoke form / result pane | Out of scope | Out of scope | MCP-TM-4 |
| Collections save/open of header rows | Out of scope | In-memory on draft | MCP-TM-7 persists |
| Remove HTTP method **MCP** | Out of scope | Out of scope | MCP-TM-6 |

**Shell rule:** this story **adds headers and templating to the existing
MCP Client workspace**. It must not invent a second tab kind. Connect
chrome from 1166 stays; this story makes auth headers part of that
connection.

### Scope (this task)

- Headers table on the MCP Client editor (add / edit / remove name-value
  rows; empty extra row when the last row is filled — same interaction as
  HTTP **Headers**).
- Resolve `{{ variable }}` placeholders from the active environment in
  header names and values before an outbound MCP call.
- Resolve `{{ variable }}` placeholders in the MCP Client URL at connect /
  send time (parity with HTTP URL templating).
- Send the resolved headers with outbound MCP calls from the MCP Client
  tab.
- Send resolved headers with HTTP method **MCP** Send (auth gap fix).
- Mask hidden environment values in header preview.

### Out of Scope

- Tool discovery (`list_tools`), refresh, and connect-failure messaging —
  MCP-TM-3 ([PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)).
- Interactive `call_tool`, schema forms, and result pane — MCP-TM-4
  ([PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)).
  When invoke later runs, it must use this story's header-aware outbound
  path; this story does not build the invoke UI.
- Migrating or removing HTTP method **MCP** — MCP-TM-6
  ([PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171)).
- Save / Save As, Collections tree items, restore of **saved** profiles —
  MCP-TM-7 ([PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)).
  Header rows live on the unsaved draft; persistence is MCP-TM-7.
- User documentation rewrite — MCP-TM-8
  ([PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)).
- Changing the protocol picker, default HTTP choice, or new-tab counting.
- Switching protocol on a tab after it is created.
- Inbound MCP surfaces (**MCP Servers…**, **MCP Tool** checkbox, HTTP /
  WebSocket **MCP** sub-tabs).
- Changing HTTP or WebSocket header tables themselves.
- SSE / stdio transports, prompts, resources, protocol trace.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **MCP Client workspace** | Dedicated outbound MCP Client editor. |
| **MCP Client draft** | Unsaved session; holds URL and header rows until save. |
| **Connection header** | Named outbound HTTP header for the MCP session. |
| **Headers table** | Editor surface for connection header rows. |
| **Active environment** | Source of `{{ variable }}` values for URL and headers. |
| **Resolved headers** | Header set after template substitution, sent to the server. |
| **Outbound MCP call** | Connect, list, call, or method **MCP** Send that sends headers. |
| **Hidden variable** | Environment secret shown masked in preview. |

### Functional Requirements

#### FR-1: Headers table on the MCP Client editor

- FR-1.1 The MCP Client editor presents a headers table for connection
  headers.
- FR-1.2 The user can add, edit, and remove header name and value rows.
- FR-1.3 Filling the last row offers a new empty row (same interaction as
  HTTP **Headers**).
- FR-1.4 The table is part of the MCP Client workspace, not the HTTP
  method dropdown and not the inbound **MCP** sub-tab.

#### FR-2: Environment templating

- FR-2.1 Header names and values accept `{{ variable }}` placeholders from
  the active environment.
- FR-2.2 The MCP Client URL accepts the same placeholders and is resolved
  when the user connects or sends.
- FR-2.3 Resolution uses the **active** environment (same product rule as
  HTTP requests).
- FR-2.4 Hover / preview of a placeholder shows the resolved value;
  hidden variables stay masked.

#### FR-3: Resolved headers are sent outbound

- FR-3.1 When the MCP Client tab performs an outbound MCP call, it sends
  the resolved header set to the remote MCP server.
- FR-3.2 Headers that exist only in the editor and are never forwarded
  are not acceptable: the remote server must receive the resolved names
  and values.
- FR-3.3 If there are no header rows, the call still proceeds (no
  required auth header in v1).

#### FR-4: HTTP method MCP send-time header gap

- FR-4.1 Until MCP-TM-6 removes HTTP method **MCP**, Send on that path
  must include the request's resolved Headers when talking to the remote
  MCP server.
- FR-4.2 This story does not remove method **MCP** from the HTTP editor.

#### FR-5: Existing surfaces stay the same

- FR-5.1 HTTP and WebSocket header tables and templating stay unchanged.
- FR-5.2 Picker, MCP Client draft chrome, unsaved-draft restore exclusion,
  and close-releases-session from PYPOST-1166 stay unchanged.
- FR-5.3 Inbound MCP surfaces stay unchanged.

### Non-Functional Requirements

- **NFR-1 Consistency:** MCP Client headers should feel like HTTP
  **Headers**: name-value table, `{{ variable }}`, environment-driven
  send.
- **NFR-2 Auth correctness:** A configured Authorization (or similar)
  header must reach the remote MCP server; silent drop is a defect.
- **NFR-3 Security:** Hidden environment keys stay masked in preview and
  logs (same policy as HTTP and MCP proxy sanitization).
- **NFR-4 Naming:** User-visible labels prefer **MCP Client** and
  **Headers** over unqualified **MCP**.
- **NFR-5 Keyboard:** Header rows remain reachable in the tab; this story
  does not add new global hotkeys (HTTP `Ctrl+H` for Headers is not
  required on MCP Client in v1 unless it already applies to the tab).

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Depends on: [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
  (Done; MCP Client draft shell already ships).
- Parent product spec: `ai-tasks/PYPOST-1164/10-requirements.md` FR-2.5.
- Architecture pointer for later steps:
  `ai-tasks/PYPOST-1164/20-architecture.md` (research decomposition).
  This story still runs its own Step 2.
- MCP-TM-3 Connect may land in parallel; Connect/invoke must use
  header-aware outbound calls once this story ships.
- HTTP method **MCP** remains until MCP-TM-6; this story only makes its
  headers actually go out.
- v1 transport remains Streamable HTTP remote URLs.
- User-facing copy uses **MCP Client**, **Headers**, **Connect**,
  **Disconnect**.

## Q&A

- **Why is this not part of PYPOST-1166?**
  1166 is the draft shell (URL and connection chrome). Headers and
  environment templating are a separate auth story so the shell can ship
  without blocking on send-time header forwarding.

- **Does Connect have to list tools here?**
  No. This story makes headers editable, resolved, and forwarded on
  outbound MCP calls. Live `list_tools` is MCP-TM-3. If Connect already
  talks to a server, it must send resolved headers.

- **Why fix HTTP method MCP if we will remove it?**
  Users still rely on that path until MCP-TM-6. The product currently
  pretends headers work and then drops them. Closing that gap is an
  acceptance criterion of this story.

- **Are header rows saved to the collection?**
  Not in this story. They live on the unsaved draft. MCP-TM-7 persists
  saved MCP Client profiles.

- **Does this change inbound MCP Servers proxy headers?**
  No. Inbound / proxy configuration is unchanged. The goal is outbound
  client parity with how HTTP (and proxy upstream) already resolve
  environment headers.

- **What if a placeholder is missing from the environment?**
  Same product behavior as HTTP request templating (unresolved or error
  on send — do not invent a new MCP-only rule).

- **How do Jira acceptance-criteria names map to this document?**
  Jira AC aliases (not requirements of their own):
  - Headers table in MCP Client editor — FR-1.
  - `{{ var }}` template resolution for headers — FR-2.
  - Outbound client run accepts a headers mapping — FR-3 (resolved
    headers are passed through to the remote call).
  - Fix HTTP method **MCP** header gap — FR-4.

## References

- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — this story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — MCP-TM-2
  draft shell (Done)
- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — MCP Client
  UX research
- `ai-tasks/PYPOST-1164/10-requirements.md` — FR-2.5 outbound headers
- `ai-tasks/PYPOST-1164/20-architecture.md` — MCP-TM-5 acceptance; Step 2
  pointer
- `ai-tasks/PYPOST-1166/10-requirements.md` — draft shell vs this story
- `doc/user/templating.md` — `{{ variable }}` and hidden-key masking
- `doc/user/requests.md` — HTTP Headers table interaction
