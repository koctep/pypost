# PYPOST-551: Migrate MCP network transport from deprecated SSE to Streamable HTTP

## Goals

PyPost exposes saved HTTP requests as MCP tools so local AI agents (e.g. Cursor, Claude
Desktop) can call them. That integration depends on a **network transport** — the way the
agent and PyPost exchange MCP messages over HTTP.

The MCP specification has **deprecated** the older HTTP+SSE transport in favor of
**Streamable HTTP**, the current standard for remote MCP servers. New and updated MCP
clients increasingly expect Streamable HTTP. If PyPost keeps only the legacy transport,
users risk failed connections, unsupported-transport errors, or being unable to use PyPost
with modern agents — even though their tools, environments, and request definitions are
correct.

The business goal is **continued, reliable MCP connectivity**: PyPost must speak the
current MCP network transport so users can keep connecting local AI agents without rework,
while optionally preserving access for agents still configured for the legacy transport
during the ecosystem transition.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **PyPost user**, I want my enabled MCP server to work with current local AI agents,
  so I can expose API requests as tools without maintaining a separate integration path.
- As an **AI agent operator**, I want to connect PyPost using the transport my MCP client
  supports today (Streamable HTTP), so setup matches client documentation and defaults.
- As a **PyPost user**, I want `list_tools` and `call_tool` to keep working after the
  transport change, so agent behavior (tool discovery and execution) is unchanged from my
  perspective.
- As a **PyPost user** who already configured a legacy SSE connection URL, I want that
  configuration to keep working if backward compatibility is provided, so I am not forced
  to reconfigure every agent immediately.
- As a **PyPost user** running the observability MCP endpoint (metrics/resources), I want
  that server to remain reachable by MCP clients on the same terms as the main request-tools
  server, so monitoring integrations are not left on a deprecated transport alone.
- As a **PyPost user** who exercises MCP from within the app (e.g. listing or calling tools
  against the local server), I want those flows to succeed against the updated transport,
  so in-app verification matches what external agents experience.

## Definition of Done

- [ ] A **local AI agent** (representative: Cursor or equivalent MCP client on the same
  machine) can connect to PyPost's main MCP server, list exposed tools, and successfully
  invoke at least one tool — using the **Streamable HTTP** transport as the primary
  connection method.
- [ ] Tool execution outcomes are unchanged: same tools listed, same arguments accepted,
  same HTTP request behavior and responses as before the transport migration (environment
  variables, MCP arguments, and GUI parity from PYPOST-550 remain intact).
- [ ] PyPost no longer relies on the **deprecated HTTP+SSE-only** transport as its sole
  network MCP offering for the main request-tools server.
- [ ] **Optional (per Jira):** Legacy SSE-based clients can still connect to PyPost if
  backward compatibility is implemented; if omitted, user-facing guidance must make clear
  that agents must use Streamable HTTP.
- [ ] The **metrics/observability MCP server** (when enabled) is included in the transport
  migration scope so both MCP servers in PyPost align with the same connectivity
  expectations.
- [ ] Automated tests demonstrate a successful MCP protocol round-trip (at minimum
  `list_tools` and `call_tool`) over the new transport, comparable to existing integration
  coverage for the legacy transport.
- [ ] Acceptance from Jira: **local AI agent connects** and can use PyPost MCP tools after
  migration.

## Task Description

### Problem

PyPost currently serves MCP over the **HTTP+SSE** transport pattern (separate SSE stream and
message POST paths). The MCP specification deprecates this pattern in favor of **Streamable
HTTP**. Client ecosystems are moving to auto-detect or require Streamable HTTP for remote
servers.

Users enable MCP on an environment, mark requests as tools, and configure an agent with a
local URL (documented today as an SSE endpoint). That workflow is valuable only if the
agent can complete the MCP handshake and exchange messages. Transport deprecation threatens
that workflow even when tool definitions and execution logic are correct.

### Scope

**In scope**

- Migrating **network transport** for MCP servers embedded in PyPost from deprecated
  HTTP+SSE to Streamable HTTP as the primary, spec-aligned option.
- Preserving end-to-end MCP behavior: server lifecycle (start/stop with environment),
  tool registration, `list_tools`, `call_tool`, and metrics/resource access on the
  observability server.
- **Optional** dual support so legacy SSE-configured clients can still connect during
  transition (Jira: "Optional backward compatibility with SSE clients").
- In-app MCP client flows that verify connectivity to the local server (same user-visible
  operations: list tools, call tool).
- Test coverage proving protocol round-trip on the new transport.

**Out of scope**

- Changes to **what** is exposed as tools, tool naming, schema generation, or request
  execution semantics (including environment-variable injection — PYPOST-550).
- **stdio** MCP transport (PyPost remains a network/local HTTP server, not a subprocess
  stdio server).
- Authentication, TLS, or exposing MCP beyond localhost unless already governed by existing
  host/port settings.
- Rewriting outbound HTTP execution (`RequestService`, templates, scripts).
- User documentation updates (Step 7), except noting here that connection instructions
  will need to reflect the new transport after implementation.
- MCP protocol version negotiation beyond what the official Python MCP SDK supports for
  Streamable HTTP.

### Functional requirements

1. **Primary transport** — PyPost's MCP network servers must support **Streamable HTTP**
   as the supported, spec-current way for local agents to connect.
2. **Behavioral parity** — After migration, agents receive the same tool catalog and
   execution results for the same environment, tool arguments, and request definitions as
   today; only the connection mechanism changes.
3. **Main MCP server** — The server started when a user enables MCP on an environment
   (request tools on the configured host/port) must be reachable via Streamable HTTP.
4. **Observability MCP server** — The separate metrics MCP server must receive the same
   transport treatment so resource access (e.g. metrics dump) remains available to agents
   on the updated transport.
5. **Lifecycle unchanged** — Users still start/stop MCP by selecting an environment with
   MCP enabled; port and host settings continue to govern where agents connect.
6. **Optional legacy support** — If implemented, agents configured for the deprecated
   SSE transport may continue to connect without forcing immediate reconfiguration; if not
   implemented, this is an explicit product trade-off documented for users in Step 7.
7. **In-app verification** — Flows inside PyPost that connect to the local MCP server to
   list or invoke tools must work against the migrated transport so users can validate
   connectivity before configuring external agents.

### Non-functional requirements

- **Compatibility** — Align with the MCP specification direction (Streamable HTTP as the
  current remote transport; legacy HTTP+SSE deprecated).
- **Reliability** — Connection setup must remain suitable for local development: single-user,
  localhost-oriented, no regression in server start/stop stability.
- **Maintainability** — Reduce reliance on deprecated SDK/spec transport so future MCP SDK
  upgrades do not strand PyPost on unsupported paths.
- **Security** — No broadening of exposure beyond today's localhost-by-default model;
  transport change must not introduce new unauthenticated remote access.

### Constraints and assumptions

- PyPost uses the official **Python MCP SDK** for server and client protocol handling;
  Streamable HTTP support is assumed to be available in that dependency (implementation
  detail deferred to Step 2).
- Default connection remains **local** (`127.0.0.1` and configurable port); users who
  bind to `0.0.0.0` accept existing network exposure trade-offs.
- Two MCP servers exist today: **request tools** (default port 1080) and **metrics**
  (default port 9080); both currently use the legacy SSE-style HTTP transport and are
  assumed in scope unless explicitly narrowed in architecture review.
- External agents (Cursor, etc.) may auto-detect transport by probing POST vs GET; PyPost
  does not control client behavior, only server-side transport support.
- User-facing docs currently describe SSE URLs and client type "SSE"; updating those
  instructions is follow-up work in Step 7, not a blocker for defining requirements here.

### Main entities (business view)

| Entity | Role |
| --- | --- |
| **MCP Client (AI Agent)** | External or in-app software that connects to PyPost to discover and invoke tools. |
| **Main MCP Server** | PyPost service exposing user-defined HTTP requests as MCP tools when MCP is enabled on the active environment. |
| **Observability MCP Server** | PyPost service exposing metrics/resources via MCP on the metrics port. |
| **MCP Tool** | A saved request marked for exposure; listed and executed through the protocol. |
| **Network Transport** | The HTTP-based message exchange pattern between client and server (legacy SSE vs Streamable HTTP). |
| **Connection URL** | The address and path the user or agent config uses to reach PyPost's MCP server. |

**Interactions**

1. User enables MCP on an environment → PyPost starts the main MCP server on configured
   host/port.
2. Agent connects using Streamable HTTP (and optionally legacy SSE if supported) → MCP
   handshake completes.
3. Agent calls `list_tools` → receives tools for requests marked "expose as MCP."
4. Agent calls `call_tool` → PyPost executes the HTTP request and returns the result.
5. Separately, observability clients may connect to the metrics MCP server for resources.

## Q&A

| Question | Answer |
| --- | --- |
| Why migrate if SSE still works today? | MCP spec deprecates HTTP+SSE; new clients and SDKs favor Streamable HTTP. Staying on SSE-only risks broken connections as the ecosystem moves on. |
| What is the business impact if we do nothing? | Users with up-to-date MCP clients may fail to connect; PyPost's core "agents call my APIs" value erodes despite correct tool setup. |
| Must legacy SSE keep working? | Jira marks backward compatibility as **optional**. Requirements include it as a desirable transition aid, not a hard blocker if cost is high — decision in Step 2. |
| Are tool execution and env vars in scope? | No. This task is transport only; PYPOST-550 and existing execution behavior must not regress. |
| Is the metrics server in scope? | Yes, unless architecture explicitly excludes it — it is a second MCP network server using the same deprecated pattern today. |
| What does Jira acceptance "Local AI agent connects via current MCP transport" mean? | After migration, a local agent successfully connects and uses tools via PyPost's **updated** supported transport (Streamable HTTP primary). |
| Do users need new ports? | Not required by this task; existing port/host settings should continue to apply (connection path details deferred to architecture). |
| Is stdio transport in scope? | No. PyPost is a long-running HTTP server integrated with the Qt app, not a subprocess stdio MCP server. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: (subagent aggregate)
