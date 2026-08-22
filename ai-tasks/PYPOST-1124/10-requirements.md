# PYPOST-1124: Product research and UX discovery for WebSocket support

## Goals

PyPost is a desktop API client whose product promise is "test APIs, then turn the requests you
already have into safe MCP tools for a local AI agent" (`README.md`, "Vision"). That promise is
currently limited to one-shot request/response protocols: the method selector offers only
`GET`, `POST`, `PUT`, `DELETE`, `PATCH`, and `MCP`
(`pypost/ui/widgets/request_editor.py:97`), and every send produces exactly one response object
(`pypost/models/response.py`). A developer whose API has a real-time surface — order books,
chat, notifications, live telemetry, agent event streams — must leave PyPost and use a second
tool for that half of the API.

Epic PYPOST-1123 ("WebSocket Protocol Support") closes that gap. PYPOST-1124 is the first story
of the epic and is deliberately a **discovery story, not a code change**.

**Why discovery before implementation (the business reason):** WebSocket is not "another HTTP
method". It replaces PyPost's central assumption — *one send, one response, then the worker is
finished* (`pypost/core/qt/worker.py:23-35`) — with a long-lived, bidirectional session that
outlives a single user action. That single change ripples through the request model, collection
persistence, the tab and response panes, history, environments and secret masking, the MCP tool
contract, and headless daemon operation. Committing engineering capacity to the epic without an
agreed product scope and interaction model would produce either a throwaway prototype or an
expensive rewrite of shared code paths. This story buys a cheap, written agreement on *what*
WebSocket support means in PyPost — and converts it into an executable Jira backlog under
PYPOST-1123 — before any of that shared code is touched.

**Secondary business value:** competitors already ship this. Postman, Insomnia, and Hoppscotch
have had WebSocket clients for years, and Bruno — the local-first client PyPost is closest to in
philosophy — shipped WebSocket support in v2.13.0. WebSocket is now table stakes for an API
client, and its absence is a visible reason to keep a second tool installed.

**Programming language:** Markdown. PYPOST-1124 produces documents only. The engineering
stories it defines target the existing PyPost stack — Python 3.11+ with PySide6
(`README.md`, `doc/dev/architecture.md`) — and each of those stories will record its own
implementation language at its own Step 1.

## Task Description

PYPOST-1124 is the discovery story of Epic PYPOST-1123. Its subject is the product definition of
WebSocket support in PyPost; its output is documentation plus an executable Jira backlog.

**Inputs.** The epic statement in PYPOST-1123, the current PyPost product and its documentation,
and the publicly documented behavior of comparable API clients.

**Work.** Establish the user need and the journeys it serves; benchmark competing clients;
specify the required protocol behavior and the desktop interaction model as observable
behavior; decide (or explicitly defer) how the capability coexists with collections,
environments, secret masking, history, scripting, MCP tooling, the headless daemon, settings,
and observability; then decompose the epic into ordered engineering stories and create them in
Jira under PYPOST-1123.

**Hard constraints.** No production code, no dependency changes, and no files outside
`ai-tasks/PYPOST-1124/`. No architecture: naming, interfaces, module ownership, concurrency,
and persistence design belong to later steps and to the implementation stories themselves.
Everything asserted about PyPost must be traceable to this repository; everything asserted about
competitors must be traceable to a cited public source.

**Success looks like** a product owner able to state the epic's scope in one sentence, a tech
lead able to begin architecture without re-running discovery, and an engineer able to pick up
the first Jira story without asking what it means.

## Baseline: what PyPost does today

Every statement below was verified against this repository. The discovery must build on these
facts rather than restate assumptions from other tools.

- **Protocols** — `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, and `MCP` only; no `ws://` or
  `wss://` (`pypost/ui/widgets/request_editor.py:97`, `doc/user/requests.md`).
- **Request record** — a request carries method, URL, headers, params, body and body type, a
  post-request script, MCP metadata, and a retry policy (`pypost/models/models.py:65-88`).
- **Response record** — one status code, headers, one body, one elapsed time, one size
  (`pypost/models/response.py`).
- **Execution** — the background worker is one-shot; a fresh instance is created per send and
  must not be reused (`pypost/core/qt/worker.py:23-35`).
- **Streaming today** — a response body may arrive in chunks that are appended to the response
  pane through a debounced buffer, then replaced by the full body
  (`doc/dev/response-streaming-display.md`).
- **Nearest real-time feature** — Server-Sent Events are handled as a bounded *probe*: at most
  five events over roughly ten seconds, summarized into a static body. It is not a live session
  (`pypost/core/http_client.py:28-31`, `doc/dev/request_execution.md`).
- **Editor layout** — one tab per request draft, with Params / Headers / Body / Script / MCP
  sub-tabs and a response pane below showing status, time, size, and `Ctrl+F` search
  (`doc/user/interface.md`, `pypost/ui/widgets/request_editor.py:137-210`).
- **In-flight UX** — while a request runs, the Send button becomes **Stop**, then
  **Stopping...** (`pypost/ui/presenters/tabs_presenter.py:441,454`).
- **Collections** — a collection holds a list of requests and is persisted as one JSON file per
  collection id, with import/export and conflict resolution
  (`pypost/models/models.py:91-95`, `doc/dev/collection_storage.md`,
  `doc/dev/collection_import.md`).
- **Environments** — named variable sets with hidden keys, resolved through `{{ ... }}`
  interpolation and expression functions
  (`pypost/models/models.py:97-103`, `doc/user/environments.md`, `doc/user/templating.md`).
- **Secrets** — hidden values render as `********` in the UI and are replaced with `***` before
  history is written; encryption at rest is optional
  (`doc/dev/sensitive_data_masking_policy.md`, `doc/user/environments.md`).
- **History** — an entry is shaped around a single exchange, with one status code and one
  round-trip duration; the sidebar filters by URL only
  (`pypost/models/models.py:105-115`, `pypost/ui/widgets/history_panel.py:65-67`).
- **Scripting** — a post-request Python script runs **once**, after the response, with
  `request`, `response`, and `pypost` in scope
  (`pypost/core/script_executor.py`, `doc/user/scripts.md`).
- **Agent integration** — a saved request can be exposed as an MCP tool with a description and
  typed parameters; each endpoint binds one collection and one environment
  (`pypost/models/models.py:79-82`, `doc/user/mcp-tools.md`, `doc/dev/mcp_server_registry.md`).
- **Export helper** — **Copy cURL** turns a saved request into a shell command and is
  HTTP-specific (`pypost/core/curl_generator.py`, `doc/user/history-and-curl.md`).
- **Settings** — global request timeout, response size cap, default retry policy, MCP and
  metrics binding, logging, and encryption (`pypost/models/settings.py`).
- **Headless mode** — a daemon runs metrics and enabled MCP servers with no GUI and no display
  server (`doc/dev/daemon.md`).
- **Automation** — stable widget identities back agent-driven and end-to-end UI tests
  (`pypost/ui/widget_ids.py`, `doc/dev/ui_identity.md`, `doc/dev/agent_e2e.md`).
- **Observability** — Prometheus counters cover GUI actions, requests, errors, MCP, and masking
  (`pypost/core/metrics_registry.py`, `doc/prometheus_monitoring.md`).

Three consequences follow, and the discovery must resolve each of them explicitly:

1. **Session vs. exchange.** Nothing in the product currently models a connection that stays open
   across many user actions. "Send" and "response" are the only vocabulary users have.
2. **Secrets and agents assume a single exchange.** Masking, history, and the MCP tool contract
   all describe one request and one response.
3. **The desktop shell is tuned for short interactions.** Tabs, the response pane, history, and
   hotkeys were designed for sub-second round trips, not for a stream that runs for hours.

## User Stories

Roles follow the ones already used in PyPost documentation and prior task artifacts: **API
developer** (primary desktop user), **QA / integration engineer**, **operator** (runs PyPost or
its daemon as a service), **AI-agent owner** (uses PyPost's MCP tools), and **product owner /
tech lead** (the direct consumer of this story's output).

### Stories about the discovery itself (this story)

- As a **product owner**, I want an agreed, written definition of what "WebSocket support" means
  in PyPost, so the epic can be funded and scheduled against a fixed scope instead of an idea.
- As a **tech lead**, I want the protocol behavior and the interaction model specified before
  implementation, so shared code paths (request model, storage, tabs, history, MCP) are changed
  once rather than repeatedly.
- As a **tech lead**, I want a competitive benchmark of Postman, Insomnia, Bruno, and Hoppscotch,
  so PyPost adopts the ergonomics users already expect and deliberately chooses where to differ.
- As an **engineer**, I want the epic decomposed into ordered, independently reviewable Jira
  stories with clear boundaries, so I can pick up work without re-deriving the whole design.
- As a **product owner**, I want the discovery to state explicit non-goals, so scope creep during
  implementation is a visible decision rather than an accident.

### Stories about the capability being discovered (the epic)

- As an **API developer**, I want to open a `ws://` or `wss://` endpoint from PyPost and keep the
  session open, so I can debug a real-time API without installing another tool.
- As an **API developer**, I want to attach headers, query parameters, authentication, and
  subprotocols to the opening handshake, so I can reach endpoints that require them.
- As an **API developer**, I want to see connection state at a glance — connecting, open,
  closing, closed, failed, reconnecting — with the reason when a session ends, so I can tell a
  server rejection apart from a network drop.
- As an **API developer**, I want to compose and send messages as plain text, JSON, or binary
  (entered as hexadecimal or base64), so I can exercise APIs that are not JSON-only.
- As an **API developer**, I want every sent and received message in one timestamped stream that
  I can search, filter by direction and type, pause, resume, and clear, so a busy stream stays
  readable while I reproduce a defect.
- As an **API developer**, I want to save frequently used messages with the connection and resend
  them in one click, so subscribing or authenticating does not mean retyping a payload.
- As a **QA engineer**, I want to run a saved ordered sequence of messages with delays, so I can
  reproduce a multi-step protocol exchange the same way every time.
- As an **API developer**, I want `{{ variable }}` placeholders to work in the connection URL,
  headers, and message payloads exactly as they do for HTTP requests, so one saved connection
  serves local, staging, and production environments.
- As an **API developer**, I want hidden environment values to stay masked in the message stream
  and in anything persisted, so debugging a live session does not leak a token.
- As an **API developer**, I want to save a WebSocket connection into a collection alongside my
  HTTP requests, so related API surfaces stay in one place and travel through export/import.
- As an **API developer**, I want the connection to recover automatically after a transient drop,
  with the retry behavior visible and bounded, so a short network blip does not end a long
  debugging session silently.
- As an **API developer**, I want a heartbeat (ping/pong) I can configure, so idle sessions stay
  open through proxies that close quiet connections.
- As an **operator**, I want long-lived sessions to be observable and bounded in resource use, so
  a forgotten open tab cannot degrade the application or a headless deployment.
- As an **AI-agent owner**, I want the discovery to state clearly whether and how WebSocket
  sessions are reachable from MCP tooling, so I know what my agent can and cannot do.
- As an **existing user**, I want HTTP and MCP behavior, saved collections, and my existing files
  to keep working unchanged, so adopting a new protocol costs me nothing.

## Competitive Baseline

Benchmarked as part of this story; sources are listed under [References](#references). The
findings below are the evidence base for the requirements that follow.

### Postman

- Two request types: raw WebSocket and Socket.IO, each opened in its own tab.
- Params and Headers tabs configured like a REST request; connection settings cover certificate
  verification, handshake request timeout, reconnection attempts, reconnection interval, and a
  maximum message size (0 meaning unlimited).
- Request details **cannot be changed while connected** — the user must disconnect first.
- Composer supports Text, JSON, XML, HTML, and Binary (entered as base64 or hexadecimal), with
  syntax highlighting and a Beautify action.
- A unified message timeline lists incoming, outgoing, and network messages with local
  timestamps, plus a connection-status badge, search, an "All Messages" scope, and Clear.
- Per-message tooling: copy or save one message, read size / timestamp / MIME metadata, compare
  the timing of two messages, expand a message to toggle text/hexadecimal, wrap lines, search
  inside it, reformat it, and fold blocks by line number.
- Messages can be saved with the request, then loaded and resent from a saved-messages pane.

### Insomnia

- WebSocket sits alongside REST, GraphQL, and gRPC in the same request interface, reusing its
  authentication, header, and message-format configuration.
- Messages are sent as JSON or raw; received messages appear in an Events panel with detailed
  previews for both directions, and handshake details are kept in the connection timeline.
- Environment variables and template tags work in WebSocket URLs and message bodies.
- Custom WebSocket protocols are documented as unsupported.

### Hoppscotch

- WebSocket is one of several real-time clients offered next to Server-Sent Events, Socket.IO,
  and MQTT.
- The connection form is a URL field plus an explicit protocols field, with Connect and
  Disconnect controls; blank or invalid protocol entries are called out as a common failure.
- A Communication tab holds the message input and Send action; a Logs pane shows the exchange.

### Bruno

- WebSocket support shipped in Bruno v2.13.0, after a long-running request opened in 2023.
- The community request that fed it asked for `ws://` and `wss://` requests, Text/JSON/XML/Binary
  formatting, open/close/error connection status, message history logging and filtering, and
  optional Socket.IO support — a useful checklist of what users consider the minimum bar.
- The stated motivation is that a local-first client is preferable for debugging sensitive
  real-time traffic — the same positioning PyPost holds.

### Capability matrix

| Capability | Postman | Insomnia | Hoppscotch | Bruno |
| --- | --- | --- | --- | --- |
| Raw WebSocket client | Yes | Yes | Yes | Yes (v2.13.0) |
| Socket.IO client | Yes | No | Yes | Requested |
| Handshake headers / params | Yes | Yes | Partial | Yes |
| Explicit subprotocol input | Yes | Not supported | Yes | — |
| Binary as hex / base64 | Yes | Raw | — | Requested |
| Unified message stream | Yes | Events pane | Logs pane | Yes |
| Search in stream | Yes | — | — | Requested |
| Filter by direction / type | Yes | Partial | — | Requested |
| Clear stream | Yes | — | — | — |
| Per-message inspector | Yes | Preview | — | — |
| Saved message presets | Yes | — | — | — |
| Reconnect settings | Yes | — | — | — |
| Variables / templating | Yes | Yes | Yes | Yes |

Legend: **Yes** documented, **Partial** limited form, **—** not found in the cited sources,
**Requested** raised in the tool's public feature request but not confirmed as shipped.

### What the benchmark implies for PyPost

Four patterns recur often enough to treat as user expectations, and one gap is a deliberate
opportunity for PyPost:

- **Connect/Disconnect replaces Send.** A WebSocket tab has a persistent connection control and
  a separate per-message send action. Users expect these to be distinct.
- **One unified, timestamped stream.** Sent, received, and connection-lifecycle events belong in
  a single chronological list, not in separate panes.
- **The composer is a first-class editor**, with format selection and formatting help, not a
  single-line input.
- **Connection parameters are frozen while connected.** Postman states this explicitly; making
  it explicit avoids a whole class of "I changed the header but nothing happened" confusion.
- **Opportunity:** none of the four combines a WebSocket client with local-first storage, hidden
  variable masking, and MCP tooling. PyPost's differentiator is not "we also have WebSocket" but
  "real-time sessions inherit the same environments, secret handling, and agent story as the
  rest of your API surface."

## Functional Requirements

### FR-1 — Discovery deliverables (the output of this story)

- FR-1.1 The story must produce a product discovery document that states the problem, the target
  users, the user journeys, the agreed scope, and the explicit non-goals of WebSocket support in
  PyPost.
- FR-1.2 The story must produce a specification (RFC) of the required protocol behavior and the
  required user-experience paradigms, at the level of observable behavior and user-visible
  contracts, sufficient for engineers to design against without re-running discovery.
- FR-1.3 The story must produce interaction-model guidance for the PySide6 desktop client:
  layout of the session surface, control placement, state indication, and behavior of each
  documented control, expressed as textual wireframes or an equivalent unambiguous description.
- FR-1.4 The story must produce an implementation breakdown covering, at minimum, the networking
  engine, the data model and persistence, the user-interface components, and the test harness,
  and must create the corresponding Jira stories/tasks under Epic PYPOST-1123.
- FR-1.5 Every product claim about PyPost's current behavior in those documents must be traceable
  to a repository file or an existing document in `doc/`.
- FR-1.6 Every competitive claim must be traceable to a cited public source.
- FR-1.7 The deliverables must record open questions and the decisions taken, so later steps can
  see what was settled and what was deferred.

### FR-2 — User workflows the discovery must define

Each workflow must be described end to end: entry point, the states the user passes through,
what is shown, what is persisted, and how the workflow ends.

- FR-2.1 **Interactive debugging** — open a session, send ad-hoc messages, read replies, close.
- FR-2.2 **Subscription and stream monitoring** — subscribe once, then watch a long-running
  stream, keeping it readable while messages keep arriving.
- FR-2.3 **Event triggering** — send a specific message (often a saved one) to provoke
  server-side behavior, and correlate the response that follows.
- FR-2.4 **Automated message sequences** — replay an ordered set of messages with delays to
  reproduce a multi-step exchange deterministically.
- FR-2.5 **Environment and variable integration** — use environment variables and template
  expressions in the connection target, handshake data, and message payloads; capture values
  received from the stream back into the environment where that is in scope.
- FR-2.6 **Session lifecycle management** — reconnect, deliberate disconnect, unexpected drop,
  automatic recovery, and what happens to the stream and to the tab on application exit.

### FR-3 — Competitive and industry analysis

- FR-3.1 The discovery must benchmark at least Postman, Insomnia, Bruno, and Hoppscotch.
- FR-3.2 The benchmark must cover connection ergonomics, connection-state presentation, message
  composition, message-stream handling, saved messages, and connection settings.
- FR-3.3 The benchmark must conclude with a table-stakes list (features PyPost must match) and a
  differentiation list (features PyPost will deliberately do differently or not at all), each
  item justified.

### FR-4 — Protocol and functional scope the discovery must specify

Stated as required user-visible behavior. Mechanisms, libraries, and internal structure are
architecture decisions and are out of scope for this document.

- FR-4.1 **Endpoint** — `ws://` and `wss://` targets, including URLs supplied through variables.
- FR-4.2 **Handshake configuration** — custom headers, query parameters, authentication data,
  and requested subprotocols; the negotiated subprotocol must be reported back to the user.
- FR-4.3 **Connection states** — the discovery must enumerate the states a session can be in and
  the transitions between them, and must define what the user sees in each state, including the
  reason a session closed or failed.
- FR-4.4 **Message directions and kinds** — outgoing and incoming application messages, plus
  connection-lifecycle events, must be distinguishable in the stream.
- FR-4.5 **Encodings** — plain text, JSON, and binary payloads entered and displayed as
  hexadecimal or base64; the discovery must define how a received payload's presentation is
  chosen and how the user overrides it.
- FR-4.6 **Heartbeat** — configurable ping/pong keep-alive with a defined default, defined
  visibility in the stream, and defined behavior when a peer does not answer.
- FR-4.7 **Reconnect** — bounded automatic reconnection with configurable attempts and interval,
  a visible reconnecting state, and a rule for what happens to stream contents across a
  reconnect.
- FR-4.8 **Saved message presets** — named messages stored with the connection, loadable and
  resendable, and included in collection export/import.
- FR-4.9 **Message sequences** — an ordered list of messages with per-step delays that can be
  started, observed, and stopped.
- FR-4.10 **Limits** — the discovery must define bounds for retained stream length, per-message
  size, and total session memory, and the user-visible behavior when a bound is reached (PyPost
  already caps HTTP response bodies at 50 MB — `pypost/models/settings.py:64`).
- FR-4.11 **Editing while connected** — the discovery must state which connection settings may
  be changed during an open session and which require a reconnect, and how the UI communicates
  that.

### FR-5 — UI/UX and desktop ergonomics the discovery must specify

- FR-5.1 **Where a session lives** — how a WebSocket session occupies the workspace relative to
  today's request tabs, and how multiple concurrent sessions are presented and switched between.
- FR-5.2 **Connection controls** — how connect/disconnect is expressed and how it relates to the
  existing Send/Stop control (`pypost/ui/presenters/tabs_presenter.py:441,454`).
- FR-5.3 **State indicators** — persistent, glanceable indication of session state, including on
  the tab itself, so a user with several sessions can see which one dropped.
- FR-5.4 **Message stream inspector** — chronological list with timestamps and direction; search;
  filter by direction and by message type; pause and resume auto-scroll or intake; clear; expand
  a single message; and copy a single message.
- FR-5.5 **Message composer** — multi-line editor with format selection, reusing the existing
  body-editor ergonomics where appropriate (`doc/dev/body_format_selector.md`,
  `doc/dev/body_editor_validation.md`).
- FR-5.6 **Saved messages and sequences surface** — where presets and sequences are listed,
  created, edited, and run.
- FR-5.7 **Long-session ergonomics** — behavior under sustained high message rates, so the UI
  stays responsive; PyPost already coalesces streamed HTTP chunks on a debounce for this reason
  (`doc/dev/response-streaming-display.md`).
- FR-5.8 **Keyboard access** — which actions get shortcuts and how they fit the existing scheme
  (`doc/user/hotkeys.md`, `pypost/ui/hotkeys.py`).
- FR-5.9 **Automation identity** — every new key surface must be assigned a stable widget
  identity so agent-driven and end-to-end tests can address it
  (`pypost/ui/widget_ids.py`, `doc/dev/ui_identity.md`).
- FR-5.10 **Errors and empty states** — what the user sees before the first connection, on
  handshake rejection, on an unexpected drop, and when a filter matches nothing.

### FR-6 — Coexistence with existing PyPost capabilities

The discovery must state, for each item, whether it is in scope for the epic, deferred, or
explicitly excluded — and what the user-visible consequence is.

- FR-6.1 **Collections** — whether a WebSocket connection is stored in the same collections as
  HTTP requests, and how it appears in the collection tree
  (`pypost/models/models.py:91-95`, `doc/dev/collection_storage.md`).
- FR-6.2 **Import/export compatibility** — how existing collection files continue to load, and
  what an older PyPost build does with a file that contains a WebSocket entry
  (`doc/dev/collection_import.md`, `doc/dev/collection_export.md`).
- FR-6.3 **Environments and templating** — where `{{ ... }}` placeholders are resolved for a
  session and at what moment (connection time versus per message)
  (`doc/user/templating.md`, `doc/dev/template_service.md`).
- FR-6.4 **Hidden values** — how masking applies to handshake data, message payloads, the
  message stream, logs, and anything persisted
  (`doc/dev/sensitive_data_masking_policy.md`, `doc/dev/hidden_variables.md`).
- FR-6.5 **History** — whether sessions appear in history at all, given that a history entry
  currently records one status code and one round-trip time
  (`pypost/models/models.py:105-115`).
- FR-6.6 **Scripting** — whether the post-response script model applies to a stream, and if so
  at which point it runs (`pypost/core/script_executor.py`, `doc/user/scripts.md`).
- FR-6.7 **MCP and agents** — whether a session, a saved message, or a sequence can be exposed
  as an MCP tool, given that the current contract is a single call returning a single result
  (`pypost/core/mcp_tool_contract.py`, `doc/user/mcp-tools.md`). A clear "not in this epic" is
  an acceptable answer if it is recorded.
- FR-6.8 **Headless daemon** — whether sessions are relevant to headless operation
  (`doc/dev/daemon.md`).
- FR-6.9 **Copy as cURL** — what the equivalent share/export affordance is for a session, if any
  (`pypost/core/curl_generator.py`).
- FR-6.10 **Settings** — which new controls belong in global settings versus per connection
  (`pypost/models/settings.py`, `doc/dev/settings_dialog.md`).
- FR-6.11 **Observability** — which user and session events must be countable, consistent with
  the existing metric families (`pypost/core/metrics_registry.py`, `doc/dev/logging.md`).

### FR-7 — Implementation breakdown and Jira creation

- FR-7.1 The breakdown must partition the epic into implementable stories with explicit
  boundaries, so two stories do not both own the same behavior.
- FR-7.2 The breakdown must cover at least: networking/session engine, data model and
  persistence, user-interface components, and test harness.
- FR-7.3 Each proposed story must carry a business-readable goal, a scope statement, and
  acceptance criteria expressed as observable behavior.
- FR-7.4 The breakdown must state the dependency order and identify which stories can proceed in
  parallel.
- FR-7.5 Each proposed story must be independently deliverable and reviewable, and must keep the
  application working when merged on its own.
- FR-7.6 The corresponding issues must exist in Jira under Epic PYPOST-1123 when the story is
  complete, with no required component missing.
- FR-7.7 Follow-up work identified but deliberately excluded from the epic must be recorded as
  such, so it is not silently lost.

## Non-functional Requirements

### For the discovery deliverables

- **Verifiability** — every requirement the discovery states must be expressed so that a reviewer
  can decide whether an implementation satisfies it.
- **Traceability** — claims about PyPost cite repository paths; claims about competitors cite
  public sources.
- **No implementation lock-in** — the deliverables describe required behavior and user-visible
  contracts, leaving mechanism, structure, and dependencies to the architecture step.
- **Completeness against the epic** — every objective in PYPOST-1123 and PYPOST-1124 is either
  addressed or explicitly deferred with a reason.
- **Language and format** — English, Markdown, maximum 100 characters per line, LF endings, no
  trailing whitespace, final newline (`lsr-markdown`, `lsr-requirements`).

### That the discovery must impose on the capability

- **Security and privacy** — hidden environment values must never appear unmasked in the message
  stream, logs, metrics labels, exported files, or persisted session data; `wss://` certificate
  validation behavior must be explicit and secure by default, consistent with PyPost's
  "secrets stay hidden" principle (`README.md`, `doc/dev/mcp_secrets_policy.md`).
- **Responsiveness** — the desktop UI must remain interactive during sustained message traffic
  and while a session is connecting, closing, or reconnecting; no user action may block on the
  network.
- **Bounded resource use** — an open or forgotten session must have bounded memory and CPU cost,
  including when the peer is silent and when it floods.
- **Reliability** — session state shown to the user must match actual state; closing a tab or the
  application must release the connection deterministically.
- **Backward compatibility** — existing collections, environments, settings, history, MCP
  endpoints, and the headless daemon must keep working without a migration step.
- **Observability** — session lifecycle and failures must be diagnosable from logs and countable
  in metrics, following existing conventions (`doc/dev/logging.md`,
  `doc/prometheus_monitoring.md`), and must never log payload content that may contain secrets.
- **Testability** — the required behavior must be verifiable by automated tests that do not
  depend on a public internet endpoint, and every new key UI surface must be addressable by a
  stable identity (`doc/dev/gui_testing.md`, `doc/dev/ui_identity.md`).
- **Accessibility and ergonomics** — state must be conveyed by more than color alone, and the
  primary actions must be reachable from the keyboard.
- **Portability** — behavior must hold on the desktop platforms PyPost already supports, with no
  new mandatory system service.

## Scope

### In scope for PYPOST-1124

- Product research into the user need for WebSocket support in PyPost and the journeys it serves.
- Competitive benchmarking of Postman, Insomnia, Bruno, and Hoppscotch.
- Definition of the required protocol behavior and user-visible session contracts.
- Definition of the desktop interaction model and interface guidelines for PySide6.
- Decisions (or explicit deferrals) on coexistence with collections, environments, secrets,
  history, scripting, MCP, the daemon, settings, and observability.
- An ordered implementation breakdown and creation of the corresponding Jira issues under
  PYPOST-1123.
- Recording open questions, risks, and deferred follow-ups.

### Non-goals for PYPOST-1124

- Writing production code, adding dependencies, or changing any file outside
  `ai-tasks/PYPOST-1124/`.
- Choosing libraries, module layout, threading or concurrency mechanisms, data schemas, or
  persistence formats — these belong to the architecture step and to the implementation stories.
- Building prototypes or user-interface mockup assets beyond textual wireframes and interaction
  guidelines.
- Delivering any part of the WebSocket capability itself.
- Redesigning HTTP request handling, the collection tree, the environment manager, or the MCP
  stack beyond what coexistence requires.
- Re-planning the epic's sprint scheduling or estimating capacity.

### Candidate non-goals for the epic (to be confirmed by the discovery)

Recorded here as the starting position so that any inclusion is a deliberate, visible decision:

- Socket.IO, MQTT, gRPC streaming, and raw TCP/UDP clients.
- Server-Sent Events beyond the existing bounded probe (`pypost/core/http_client.py:28-31`).
- Acting as a WebSocket *server* or mock endpoint.
- Load or performance testing of real-time endpoints.
- Team synchronization, sharing, or cloud storage of sessions.
- Recording and replaying entire captured sessions as regression fixtures.

## Assumptions and Constraints

- PYPOST-1124 is a 5-point Story of Medium priority under Epic PYPOST-1123 and is the epic's
  first deliverable; no implementation story exists yet.
- The epic targets the existing desktop product; PyPost stays local-first and single-user, and
  no server-side component is introduced.
- The implementation stack is fixed: Python 3.11+ and PySide6 (`README.md`,
  `doc/dev/architecture.md`). The discovery must not propose a different UI toolkit.
- PyPost's layering rules apply to whatever the epic builds: `models/` uses the standard library
  only, `core/` stays free of Qt, Qt integration lives in `core/qt/`, and `ui/` depends on the
  others (`doc/dev/architecture.md`).
- Existing on-disk data must keep loading. Collection files are per-collection JSON documents
  with no schema-version field (`doc/dev/collection_storage.md`,
  `pypost/core/collection_export.py`), so compatibility is a product constraint, not an
  afterthought.
- "WebSocket" in this document means the standard `ws://`/`wss://` protocol, not Socket.IO or
  any other framing layer built on top of it.
- The user is not available to answer questions during this run; where a product decision is
  required, the discovery records the decision, the reasoning, and its reversibility, rather
  than blocking.
- Competitive findings reflect the sources cited at the time of writing; vendor features change,
  so the benchmark is dated evidence rather than a permanent contract.
- Naming, interfaces, module ownership, concurrency, and persistence design are deliberately
  absent from this document and are decided at the architecture step.

## Business Entities and Interactions

Business-domain entities. These are not tables, classes, or files.

- **WebSocket connection profile** — the saved, reusable description of a real-time endpoint: a
  name, a target, handshake data, subprotocols, heartbeat and reconnect preferences, and its
  saved messages. It is the WebSocket peer of a saved HTTP request and lives inside a
  **collection**.
- **Session** — one live instance of a connection profile. It has a state, a start and end, an
  end reason, and it owns a message stream. A profile may be opened many times; a session exists
  only while the user keeps it open.
- **Message** — one unit exchanged in a session, with a direction (outgoing or incoming), a
  timestamp, a payload, and a presentation format. Messages are what the user reads and searches.
- **Connection event** — a lifecycle occurrence inside a session: handshake accepted or rejected,
  heartbeat exchanged, reconnect attempted, session closed with a reason. Shown in the same
  stream as messages so cause and effect stay adjacent.
- **Message stream** — the ordered, filterable record of the messages and connection events of
  one session, and the user's primary inspection surface.
- **Saved message preset** — a named, reusable payload stored on a connection profile, so common
  operations (authenticate, subscribe, ping) are one click rather than retyping.
- **Message sequence** — an ordered list of preset or inline messages with delays, run as a unit
  to reproduce a multi-step exchange.
- **Heartbeat policy** — the user's keep-alive preference for a profile.
- **Reconnect policy** — the user's bounded automatic-recovery preference for a profile.
- **Environment** — the existing named variable set, including hidden values, that supplies
  values to the target, handshake data, and payloads (`pypost/models/models.py:97-103`).
- **Collection** — the existing container that stores requests and, by extension, connection
  profiles, and carries them through export and import.
- **Discovery artifact set** — this story's own product: the discovery document, the RFC, the
  interaction guidelines, and the Jira breakdown.
- **Implementation backlog** — the ordered set of Jira stories created under PYPOST-1123.

Interactions in one line: an **API developer** opens a **session** from a **connection profile**
stored in a **collection**, resolved against the active **environment**; the session produces a
**message stream** of **messages** and **connection events**; the developer sends **saved message
presets** or a **message sequence** into it; **heartbeat** and **reconnect policies** keep the
session alive; **hidden values** stay masked throughout; and the whole capability is delivered by
the **implementation backlog** this story creates.

## User Scenarios

### S-1 First real-time debugging session

1. A developer creates a WebSocket entry, enters a `wss://` target that uses `{{ host }}`, and
   adds an authorization header sourced from a hidden environment variable.
2. They connect. The interface shows the session moving to an open state and records the
   handshake — including the negotiated subprotocol — at the top of the stream.
3. They type a JSON message and send it. The outgoing message appears immediately, and replies
   arrive below it with timestamps and a distinct direction indicator.
4. The hidden token is masked everywhere it is displayed and everywhere it is stored.
5. They disconnect. The stream stays readable, and the closing reason is recorded.

### S-2 Monitoring a busy subscription

1. A developer connects and sends a subscription message.
2. Messages arrive continuously. The interface stays responsive.
3. They pause the stream to read one message, then filter to incoming messages of one kind.
4. They search for a correlation identifier and expand the matching message.
5. They clear the stream and resume, keeping the session open throughout.

### S-3 Triggering an event and correlating the result

1. A developer keeps a session open while exercising the system elsewhere.
2. They load a saved message preset and send it to trigger server-side behavior.
3. The resulting server messages appear in the stream next to the trigger, so cause and effect
   are visible together.
4. They copy one message out for a defect report; masked values remain masked in the copy.

### S-4 Reproducing a multi-step exchange

1. A QA engineer defines an ordered message sequence with per-step delays.
2. They run it against the open session and watch each step land in the stream.
3. A step fails; the run reports which step and why, and the sequence can be stopped.
4. They re-run the same sequence against a different environment without editing payloads.

### S-5 Surviving a network drop

1. A long session is interrupted by a transient network failure.
2. The interface shows a reconnecting state with attempt progress, rather than appearing open.
3. Reconnection succeeds within the configured bounds; the stream records the gap and the
   recovery so the developer knows messages may have been missed.
4. When the bound is exhausted, the session ends with a clear reason and no silent retrying.

### S-6 Reusing a connection across environments

1. A developer saves a connection profile into an existing collection next to related HTTP
   requests.
2. They switch the active environment and connect again; the target, handshake data, and payload
   placeholders resolve against the new environment.
3. They export the collection and import it on another machine; the connection profile, its
   saved messages, and its sequences survive the round trip.
4. Opening the same collection in a build without WebSocket support does not corrupt it.

### S-7 Keeping an idle session alive

1. A developer opens a session against an endpoint behind a proxy that closes idle connections.
2. The configured heartbeat keeps the session open without flooding the stream with noise.
3. When the peer stops answering the heartbeat, the session is reported as failed with that
   reason rather than lingering in a false open state.

### S-8 Product owner consumes the discovery

1. A product owner reads the discovery document and can state, in one sentence, what the epic
   will and will not deliver.
2. A tech lead reads the RFC and interaction guidelines and can start architecture without
   re-deriving user intent.
3. Both open Epic PYPOST-1123 and find implementation stories covering the networking engine,
   the data model, the interface, and the test harness, in a defensible order.
4. Nothing in those documents pre-empts a design decision that belongs to the architecture step.

## Definition of Done

- [ ] A product discovery document exists that states the problem, users, journeys, agreed scope,
      and explicit non-goals of WebSocket support in PyPost.
- [ ] A specification (RFC) exists covering connection handshake semantics (headers,
      authentication, query parameters, subprotocols), connection states, message encodings
      (JSON, plain text, binary as hexadecimal or base64), heartbeat/ping-pong management,
      bounded auto-reconnect, and saved message presets.
- [ ] The competitive benchmark of Postman, Insomnia, Bruno, and Hoppscotch is documented with
      cited sources and concludes with a table-stakes list and a differentiation list.
- [ ] All six core user workflows (FR-2.1 to FR-2.6) are described end to end.
- [ ] Interaction-model guidance for the PySide6 desktop client is documented, covering session
      placement, connection controls, state indicators, the message-stream inspector (search,
      filter by direction and type, pause/resume, clear), the message composer, saved messages
      and sequences, long-session ergonomics, keyboard access, automation identities, and error
      and empty states.
- [ ] Coexistence decisions are recorded for collections, import/export compatibility,
      environments and templating, hidden values, history, scripting, MCP/agents, the headless
      daemon, Copy as cURL, settings, and observability — each marked in scope, deferred, or
      excluded, with a reason.
- [ ] Resource and safety bounds are specified: retained stream length, per-message size, session
      memory, and the user-visible behavior at each bound.
- [ ] Non-functional expectations (security and masking, responsiveness, bounded resources,
      reliability, backward compatibility, observability, testability, accessibility,
      portability) are stated as verifiable criteria.
- [ ] An implementation breakdown exists covering at least the networking engine, the data model
      and persistence, the user-interface components, and the test harness, with dependency order
      and parallelization noted.
- [ ] Concrete engineering stories/tasks matching that breakdown exist in Jira under Epic
      PYPOST-1123, each with a business goal, scope, and observable acceptance criteria.
- [ ] Every PyPost behavioral claim in the deliverables cites a repository path or a document
      under `doc/`; every competitive claim cites a public source.
- [ ] Open questions, decisions taken, risks, and deferred follow-ups are recorded.
- [ ] No production code, dependency, or file outside `ai-tasks/PYPOST-1124/` was changed by this
      story.
- [ ] Artifacts satisfy the Markdown and file-handling standards (English, ATX headings,
      maximum 100 characters per line, LF endings, no trailing whitespace, final newline).

## Q&A

**Q: The Jira description is phrased as work items ("conduct research", "create tasks"). What is
the underlying business requirement?**
A: PyPost cannot serve users whose APIs have a real-time surface, so those users keep a second
API client installed and PyPost's "reuse over rebuild" promise stops at the HTTP boundary
(`README.md`). The business requirement is to extend PyPost to real-time APIs without breaking
the local-first, secrets-safe, agent-ready product it already is. Discovery is the cheapest step
that makes that extension predictable, because WebSocket breaks the one-send/one-response
assumption that PyPost's request model, tabs, history, masking, and MCP contract are all built
on.

**Q: Why not skip discovery and implement a minimal client?**
A: The minimal client is not the expensive part. The expensive part is that a session touches
`RequestData`, collection persistence and import/export, the tab and response panes, history,
hidden-value masking, and the MCP tool contract. Choosing those contracts twice costs far more
than one story of research, and a half-integrated WebSocket tab would violate the product
principles in `README.md`.

**Q: Is a WebSocket connection a new kind of request, or a new kind of object?**
A: Open, and deliberately so — it is the first decision the discovery must take, because
everything downstream (collection tree, storage, tabs, MCP eligibility) depends on it. Today
`RequestData` carries an HTTP-shaped `method` field and a single `body`
(`pypost/models/models.py:65-88`), and `HistoryEntry` records exactly one status code and one
round-trip time (`pypost/models/models.py:105-115`), so neither fits a session unchanged. This
document requires the decision and its consequences to be recorded; it does not pre-empt it.

**Q: Should WebSocket sessions be exposed as MCP tools?**
A: Not assumed. The current contract is a single tool call returning a single result
(`doc/user/mcp-tools.md`, `pypost/core/mcp_tool_contract.py`), which does not map onto a
long-lived stream. FR-6.7 requires an explicit decision; "not in this epic" is acceptable if
recorded with a reason, so agent owners know what to expect.

**Q: Do competitors already solve this, and what do they agree on?**
A: Yes. Postman, Insomnia, and Hoppscotch have shipped WebSocket clients for years, and Bruno
added support in v2.13.0. They agree on four things: a persistent connect/disconnect control
distinct from per-message send; one unified timestamped stream of sent, received, and lifecycle
events; a first-class multi-line composer with format selection; and connection parameters that
are frozen while connected. Postman is the most complete on inspection tooling — per-message
expand, text/hex toggle, in-message search, timing comparison, saved messages, and explicit
connection settings for handshake timeout, reconnection attempts and interval, and maximum
message size.

**Q: Where can PyPost differentiate rather than copy?**
A: None of the four combines a WebSocket client with local-first storage, hidden-variable
masking, and MCP tooling in one product. PyPost's angle is integration: real-time sessions
inherit the same environments, secret handling, collection storage, and agent story as the rest
of the API surface.

**Q: Does this story create the Jira issues?**
A: The story does, in a later step of this run; Step 1 does not. Step 1 defines what the
breakdown must cover (FR-7) and makes issue creation part of the Definition of Done.

**Q: Which programming language applies?**
A: The artifacts of PYPOST-1124 are Markdown documents. The capability the discovery defines
will be built in Python 3.11+ with PySide6, matching the existing application
(`README.md`, `doc/dev/architecture.md`); each implementation story records that at its own
Step 1.

**Q: Does PyPost have any real-time capability today that could be reused conceptually?**
A: Two partial precedents, both worth studying and neither sufficient. Streaming HTTP bodies are
appended to the response pane through a debounced buffer to avoid flooding the event loop
(`doc/dev/response-streaming-display.md`) — directly relevant to a high-rate message stream. And
Server-Sent Events are handled as a bounded probe of at most five events over roughly ten seconds
before being summarized as a static body (`pypost/core/http_client.py:28-31`) — which is the
opposite of a long-lived session and should not be taken as a model.

## References

### Repository

- `README.md` — product vision, principles, and feature set
- `doc/dev/architecture.md` — layering, composition root, core components
- `doc/user/interface.md`, `doc/user/requests.md`, `doc/user/hotkeys.md` — current desktop UX
- `doc/user/environments.md`, `doc/user/templating.md`, `doc/user/scripts.md` — variables,
  templating, and post-request scripting
- `doc/user/mcp-tools.md`, `doc/mcp_integration.md`, `doc/dev/mcp_server_registry.md` — agent
  integration
- `doc/dev/request_execution.md`, `doc/dev/response-streaming-display.md` — execution pipeline
  and streamed display
- `doc/dev/collection_storage.md`, `doc/dev/collection_import.md`, `doc/dev/collection_export.md`
  — persistence and interchange
- `doc/dev/sensitive_data_masking_policy.md`, `doc/dev/hidden_variables.md` — secret handling
- `doc/dev/daemon.md`, `doc/dev/logging.md`, `doc/prometheus_monitoring.md` — headless operation
  and observability
- `doc/dev/ui_identity.md`, `doc/dev/gui_testing.md`, `doc/dev/agent_e2e.md` — UI automation
- `pypost/models/models.py`, `pypost/models/response.py`, `pypost/models/settings.py` — domain
  models
- `pypost/core/qt/worker.py`, `pypost/core/http_client.py`, `pypost/core/script_executor.py` —
  execution behavior
- `pypost/ui/widgets/request_editor.py`, `pypost/ui/presenters/tabs_presenter.py`,
  `pypost/ui/widgets/history_panel.py`, `pypost/ui/widget_ids.py` — desktop surfaces

### Competitive sources

- Postman — Send WebSocket requests:
  https://learning.postman.com/docs/use/send-requests/protocols/websocket/websocket-overview
- Postman — Create a WebSocket request:
  https://learning.postman.com/docs/use/send-requests/protocols/websocket/create-a-websocket-request
- Postman — Add details to a WebSocket or Socket.IO request:
  https://learning.postman.com/docs/sending-requests/websocket/add-details-websocket
- Postman — Work with WebSocket messages:
  https://learning.postman.com/docs/sending-requests/websocket/work-with-websocket-messages
- Insomnia — Requests (Kong Docs):
  https://developer.konghq.com/insomnia/requests/
- Insomnia — Kong Insomnia 2022.6 supports WebSockets:
  https://konghq.com/blog/product-releases/kong-insomnia-2022-6
- Hoppscotch — WebSocket documentation:
  https://docs.hoppscotch.io/documentation/getting-started/realtime/websocket
- Bruno — issue #316, WebSocket support (shipped in v2.13.0):
  https://github.com/usebruno/bruno/issues/316
- Bruno — issue #5283, WebSocket feature request detail:
  https://github.com/usebruno/bruno/issues/5283
